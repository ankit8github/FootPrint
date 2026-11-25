"""Proposed evidence-only contract. No independent assessment/classifier rules."""

import json
from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from app.contracts import Adapter, Contract
from app.phase2 import Code

MAX_BODY = 8 * 1024 * 1024
MAX_ROWS = 10_000
Index = Annotated[int, Field(ge=0, lt=MAX_ROWS)]
Count = Annotated[int, Field(ge=0, le=MAX_ROWS)]
Epoch = Annotated[int, Field(ge=1, le=1_000_000)]
SourceID = Annotated[str, Field(pattern=r"^s[0-9]{4}$", max_length=5)]
EventID = Annotated[str, Field(pattern=r"^s[0-9]{4}:r[0-9]{5}$", max_length=12)]
Alias = Annotated[str, Field(pattern=r"^order(?:[0-9]{4}|10000)$", max_length=10)]
Domain = Literal[
    "fictional-cafe.test",
    "fictional-clinic.test",
    "fictional-date.test",
    "fictional-duplicate.test",
    "fictional-library.test",
    "fictional-museum.test",
    "fictional-news.test",
    "fictional-notes.test",
    "fictional-parcel.test",
    "fictional-postcard.test",
    "fictional-shop.test",
    "fictional-shopper.test",
    "fictional-studio.test",
]
UTC = Annotated[
    str,
    Field(
        pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.(?:[0-9]{3}|[0-9]{6})Z$",
        max_length=27,
    ),
]
Feature = Literal[
    "ACCOUNT_REQUEST",
    "ACCOUNT_PREFERENCES_CHANGED",
    "PAID_RECEIPT_CLAIM",
    "CANCELLED_BEFORE_PAYMENT_CLAIM",
    "UNPAID_INVOICE_CLAIM",
    "NEWSLETTER_CUE",
    "QUOTED_CONTEXT",
    "UNTRUSTED_INSTRUCTIONS",
]
Issue = (
    Code
    | Literal[
        "NO_SUPPORTED_FEATURE",
        "QUOTED_CONTEXT",
        "UNTRUSTED_INSTRUCTIONS",
        "MULTIPLE_COMMERCIAL_REFERENCES",
        "FEATURE_LIMIT",
    ]
)
COMMERCIAL = {"PAID_RECEIPT_CLAIM", "CANCELLED_BEFORE_PAYMENT_CLAIM", "UNPAID_INVOICE_CLAIM"}


class Source(Contract):
    source_id: SourceID
    adapter: Adapter
    record_count: Count


class Observation(Contract):
    id: EventID
    source_id: SourceID
    record_index: Index
    domain: Domain | None
    occurred_at: UTC | None
    time_status: Literal["valid", "invalid", "missing"]
    order_keys: Annotated[list[Alias], Field(max_length=8)]
    duplicate_of: EventID | None
    issue_code: Issue | None

    @model_validator(mode="after")
    def timestamp(self) -> Self:
        if (self.occurred_at is not None) != (self.time_status == "valid"):
            raise ValueError("invalid evidence")
        if self.occurred_at is not None:
            parsed = datetime.fromisoformat(self.occurred_at.replace("Z", "+00:00"))
            if not 1970 <= parsed.year <= 2100:
                raise ValueError("invalid evidence")
        if len(set(self.order_keys)) != len(self.order_keys):
            raise ValueError("invalid evidence")
        return self


class EmailObservation(Observation):
    adapter: Literal["email_eml_v1"]
    kind: Literal[
        "registration_email_detected",
        "transaction_email_detected",
        "marketing_email_detected",
        "account_notification_detected",
        "unclassified_observation",
    ]
    attribution: Literal["unverified_sender"]
    features: Annotated[list[Feature], Field(max_length=8)]

    @model_validator(mode="after")
    def metadata(self) -> Self:
        if len(set(self.features)) != len(self.features):
            raise ValueError("invalid evidence")
        if self.issue_code is not None:
            if self.domain is not None or self.kind != "unclassified_observation":
                raise ValueError("invalid evidence")
        elif self.domain is None:
            raise ValueError("invalid evidence")
        if self.order_keys and (self.domain is None or not COMMERCIAL.intersection(self.features)):
            raise ValueError("invalid evidence")
        return self


class HistoryObservation(Observation):
    adapter: Literal["browser_chrome_json_v1"]
    kind: Literal["site_visit_observed"]
    attribution: Literal["browser_record"]
    features: Annotated[list[Literal["VISIT_RECORDED"]], Field(min_length=1, max_length=1)]

    @model_validator(mode="after")
    def metadata(self) -> Self:
        if self.domain is None or self.time_status != "valid" or self.order_keys or self.issue_code:
            raise ValueError("invalid evidence")
        return self


Evidence = Annotated[EmailObservation | HistoryObservation, Field(discriminator="adapter")]


class Excluded(Contract):
    event_id: EventID
    source_id: SourceID
    record_index: Index
    code: Issue


class Context(Contract):
    observation_id: EventID
    features: Annotated[
        list[Literal["CLINIC_APPOINTMENT_PORTAL_CONTEXT"]], Field(min_length=1, max_length=1)
    ]


class CommercialGroup(Contract):
    alias: Alias
    domain: Domain
    members: Annotated[list[EventID], Field(min_length=1, max_length=MAX_ROWS)]


class MinimizedBatch(Contract):
    schema_version: Literal["minimized-evidence-v1"]
    parser_version: Literal["phase2-normalized-v1"]
    feature_version: Literal["email_features_v1"]
    fusion_version: Literal["relationship_fusion_v1"]
    context_version: Literal["email_context_v1"]
    assessment_version: Literal["sensitivity_rules_v1"]
    sources: Annotated[list[Source], Field(max_length=20)]
    observations: Annotated[list[Evidence], Field(max_length=MAX_ROWS)]
    excluded: Annotated[list[Excluded], Field(max_length=MAX_ROWS)]
    contexts: Annotated[list[Context], Field(max_length=MAX_ROWS)]
    duplicate_groups: Annotated[
        list[Annotated[list[EventID], Field(min_length=2, max_length=MAX_ROWS)]],
        Field(max_length=MAX_ROWS),
    ]
    commercial_groups: Annotated[list[CommercialGroup], Field(max_length=MAX_ROWS)]

    @model_validator(mode="after")
    def references(self) -> Self:
        def require(condition: bool) -> None:
            if not condition:
                raise ValueError("invalid evidence")

        require(sum(s.record_count for s in self.sources) <= MAX_ROWS)
        sources = {s.source_id: s for s in self.sources}
        require(
            [s.source_id for s in self.sources] == [f"s{i + 1:04}" for i in range(len(sources))]
        )
        rows: set[str] = set()
        observations = {o.id: o for o in self.observations}
        require(len(observations) == len(self.observations))
        for row in [*self.observations, *self.excluded]:
            identifier = row.id if isinstance(row, Observation) else row.event_id
            source = sources.get(row.source_id)
            require(source is not None)
            assert source is not None
            require(row.record_index < source.record_count)
            require(identifier == f"{row.source_id}:r{row.record_index:05}")
            require(identifier not in rows)
            rows.add(identifier)
            if isinstance(row, Observation):
                require(row.adapter == source.adapter)
        require(len(rows) == sum(s.record_count for s in self.sources))
        # Duplicate membership is complete and direct: no unscoped/group fallback.
        grouped: set[str] = set()
        duplicates: set[str] = set()
        for group in self.duplicate_groups:
            require(len(set(group)) == len(group) and not grouped.intersection(group))
            grouped.update(group)
            primary = observations.get(group[0])
            require(primary is not None and primary.duplicate_of is None)
            assert primary is not None
            for member in group[1:]:
                copy = observations.get(member)
                require(copy is not None and copy.duplicate_of == primary.id)
                assert copy is not None
                require(
                    all(
                        getattr(copy, k) == getattr(primary, k)
                        for k in (
                            "adapter",
                            "kind",
                            "domain",
                            "occurred_at",
                            "time_status",
                            "features",
                            "order_keys",
                            "issue_code",
                            "attribution",
                        )
                    )
                )
                duplicates.add(member)
        require(duplicates == {o.id for o in self.observations if o.duplicate_of is not None})
        require(len({c.observation_id for c in self.contexts}) == len(self.contexts))
        for context in self.contexts:
            observation = observations.get(context.observation_id)
            require(isinstance(observation, EmailObservation))
            assert isinstance(observation, EmailObservation)
            require(observation.issue_code is None and "ACCOUNT_REQUEST" in observation.features)
        aliases = list(dict.fromkeys(alias for o in self.observations for alias in o.order_keys))
        require([g.alias for g in self.commercial_groups] == aliases)
        require(aliases == [f"order{i + 1:04}" for i in range(len(aliases))])
        for commercial in self.commercial_groups:
            members = [o for o in self.observations if commercial.alias in o.order_keys]
            require(commercial.members == [o.id for o in members])
            require(
                all(
                    isinstance(o, EmailObservation)
                    and o.domain == commercial.domain
                    and bool(COMMERCIAL.intersection(o.features))
                    for o in members
                )
            )
        return self


class AdmissionEnvelope(Contract):
    consent_version: Literal["fictional-admission-consent-v1"]
    consent_epoch: Epoch
    expected_revision: Epoch
    batch: MinimizedBatch


def canonical(batch: MinimizedBatch) -> bytes:
    return json.dumps(
        batch.model_dump(warnings="error"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def parse_json(raw: bytes) -> object:
    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result or key in {"__proto__", "constructor", "prototype"}:
                raise ValueError("invalid evidence")
            result[key] = value
        return result

    def no_constant(value: str) -> object:
        raise ValueError("invalid evidence")

    data: object = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=unique,
        parse_constant=no_constant,
        parse_float=no_constant,
    )
    stack = [(data, 1)]
    while stack:
        value, depth = stack.pop()
        if isinstance(value, (dict, list)):
            if depth > 8:
                raise ValueError("invalid evidence")
            children = value.values() if isinstance(value, dict) else value
            stack.extend((v, depth + 1) for v in children)
        elif isinstance(value, str) and not value.isascii():
            raise ValueError("invalid evidence")
    return data
