"""Strict synthetic observation boundary. No ingestion, storage or analysis."""

import json
from datetime import datetime
from typing import Annotated, Literal, Self

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import Field, field_validator, model_validator
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.contracts import Adapter, Contract

MAX_BODY = 8 * 1024 * 1024
MAX_RECORDS = 10_000
Code = Literal[
    "OK",
    "EMAIL_UNCLASSIFIED",
    "DUPLICATE_RECORD",
    "INVALID_TIMESTAMP",
    "INVALID_URL",
    "INVALID_RECORD",
    "INVALID_JSON",
    "JSON_LIMIT",
    "MALFORMED_MIME",
    "UNSUPPORTED_ENCODING",
    "MISSING_SENDER",
    "ORIGIN_CONFLICT",
    "HTML_ONLY_IGNORED",
    "UNAVAILABLE_HISTORY",
    "NOT_APPROVED_SYNTHETIC",
    "FILE_LIMIT",
    "BATCH_LIMIT",
    "RECORD_LIMIT",
    "UNSUPPORTED_FILE",
    "PARSER_TIMEOUT",
    "PARSER_FAILED",
]
Domain = Annotated[
    str, Field(pattern=r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.test$", max_length=68)
]
UTC = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3}(?:\d{3})?)?Z$")]


class NormalizedObservation(Contract):
    adapter: Adapter
    kind: Literal["site_visit_observed", "unclassified_observation"]
    domain: Domain
    occurred_at: UTC | None
    summary_code: Literal["VISIT_RECORDED", "EMAIL_RECEIVED_UNVERIFIED"]
    origin: Literal["browser_record", "unverified_sender"]
    time_status: Literal["valid", "invalid", "missing"]

    @field_validator("occurred_at")
    @classmethod
    def valid_utc(cls, value: str | None) -> str | None:
        if value is not None:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if not 1970 <= parsed.year <= 2100:
                raise ValueError("timestamp outside supported range")
        return value

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if (self.occurred_at is not None) != (self.time_status == "valid"):
            raise ValueError("inconsistent timestamp")
        if self.adapter == "browser_chrome_json_v1":
            if (self.kind, self.summary_code, self.origin, self.time_status) != (
                "site_visit_observed",
                "VISIT_RECORDED",
                "browser_record",
                "valid",
            ):
                raise ValueError("invalid history observation")
        elif (self.kind, self.summary_code, self.origin) != (
            "unclassified_observation",
            "EMAIL_RECEIVED_UNVERIFIED",
            "unverified_sender",
        ):
            raise ValueError("invalid email observation")
        return self


class ImportRecord(Contract):
    record_index: Annotated[int, Field(ge=0, lt=MAX_RECORDS)]
    disposition: Literal["normalized", "unresolved", "excluded", "duplicate"]
    code: Code
    observation: NormalizedObservation | None
    duplicate_of_index: Annotated[int, Field(ge=0, lt=MAX_RECORDS)] | None

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if (self.disposition == "normalized") != (self.observation is not None):
            raise ValueError("invalid observation disposition")
        if self.disposition == "normalized" and self.code not in {"OK", "EMAIL_UNCLASSIFIED"}:
            raise ValueError("invalid normalized code")
        if self.disposition in {"unresolved", "excluded"} and self.code in {
            "OK",
            "EMAIL_UNCLASSIFIED",
            "DUPLICATE_RECORD",
        }:
            raise ValueError("invalid issue code")
        if self.disposition == "duplicate":
            if self.code != "DUPLICATE_RECORD" or self.duplicate_of_index is None:
                raise ValueError("invalid duplicate")
            if self.duplicate_of_index >= self.record_index:
                raise ValueError("duplicate must cite earlier record")
        elif self.duplicate_of_index is not None:
            raise ValueError("unexpected duplicate reference")
        return self


class SourceResult(Contract):
    source_id: Annotated[str, Field(pattern=r"^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$")]
    adapter: Adapter
    records: Annotated[list[ImportRecord], Field(max_length=MAX_RECORDS)]

    @model_validator(mode="after")
    def provenance(self) -> Self:
        seen: dict[int, ImportRecord] = {}
        for record in self.records:
            if record.record_index in seen:
                raise ValueError("duplicate record index")
            if record.observation and record.observation.adapter != self.adapter:
                raise ValueError("adapter mismatch")
            if record.duplicate_of_index is not None:
                target = seen.get(record.duplicate_of_index)
                if target is None or target.disposition != "normalized":
                    raise ValueError("duplicate lacks normalized source support")
            seen[record.record_index] = record
        return self


class NormalizedBatch(Contract):
    schema_version: Literal["phase2-normalized-v1"]
    synthetic_only: Literal[True]
    sources: Annotated[list[SourceResult], Field(max_length=20)]

    @model_validator(mode="after")
    def bounded(self) -> Self:
        if len({x.source_id for x in self.sources}) != len(self.sources):
            raise ValueError("duplicate source identity")
        if sum(len(x.records) for x in self.sources) > MAX_RECORDS:
            raise ValueError("record limit")
        return self


class ValidationReceipt(Contract):
    schema_version: Literal["phase2-normalized-v1"] = "phase2-normalized-v1"
    synthetic_only: Literal[True] = True
    records: int


class BoundedJSON:
    """Reject media types and bound streamed bodies before model validation."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] != "POST":
            await self.app(scope, receive, send)
            return
        headers = dict(scope["headers"])
        if headers.get(b"content-type", b"").lower() not in {
            b"application/json",
            b"application/json; charset=utf-8",
        }:
            await JSONResponse({"code": "JSON_REQUIRED"}, status_code=415)(scope, receive, send)
            return
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > MAX_BODY:
                await JSONResponse({"code": "BODY_LIMIT"}, status_code=413)(scope, receive, send)
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
            result: dict[str, object] = {}
            for key, value in pairs:
                if key in result or key in {"__proto__", "constructor", "prototype"}:
                    raise ValueError("invalid object keys")
                result[key] = value
            return result

        try:
            json.loads(
                body,
                object_pairs_hook=unique_object,
                parse_constant=lambda value: (_ for _ in ()).throw(ValueError("constant")),
            )
        except (ValueError, RecursionError, UnicodeError):
            await JSONResponse({"code": "INVALID_NORMALIZED_PAYLOAD"}, status_code=422)(
                scope, receive, send
            )
            return

        async def bounded_receive() -> Message:
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, bounded_receive, send)


boundary = FastAPI(
    title="PV1 Phase 2 synthetic validation",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
boundary.add_middleware(BoundedJSON)


@boundary.exception_handler(RequestValidationError)
async def safe_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Never serialize exc.errors(): Pydantic includes input values by default.
    return JSONResponse({"code": "INVALID_NORMALIZED_PAYLOAD"}, status_code=422)


@boundary.post("/validate")
def validate_normalized(payload: NormalizedBatch) -> ValidationReceipt:
    """Validation only: no echo, logging, persistence or downstream processing."""
    return ValidationReceipt(records=sum(len(x.records) for x in payload.sources))
