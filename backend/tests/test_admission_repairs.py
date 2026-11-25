"""Faithful-state and case-preserved-header repair regressions; no human approval."""

import asyncio
import json
import logging
import warnings
from typing import Any

import pytest
from admission_test_support import DIGESTS, batch, envelope, example, exchange, harness, submit
from httpx2 import ASGITransport, AsyncClient
from session_test_support import ORIGIN
from starlette.types import Receive, Scope, Send
from test_admission_assurance import no_network as no_network

from app.contracts import Contract
from experiments.admission_fixture import ERROR, RECEIPT, admission_scope
from experiments.minimized_contract import AdmissionEnvelope
from experiments.oidc_protocol import BFF
from experiments.session_fixture import SESSION_COOKIE
from experiments.session_store import Denied

SENTINEL = "REPAIR_PRIVATE_subject_token@example.com"


def target(level: str) -> tuple[AdmissionEnvelope, Contract]:
    if level in {"email", "history"}:
        adapter = "email_eml_v1" if level == "email" else "browser_chrome_json_v1"
        data = next(
            batch(d)
            for d in DIGESTS
            if any(o["adapter"] == adapter for o in batch(d)["observations"])
        )
        model = AdmissionEnvelope.model_validate(envelope(data))
        return model, next(o for o in model.batch.observations if o.adapter == adapter)
    field = {
        "source": "sources",
        "excluded": "excluded",
        "context": "contexts",
        "commercial": "commercial_groups",
    }.get(level, "observations")
    model = AdmissionEnvelope.model_validate(envelope(example(field)))
    value = (
        model
        if level == "envelope"
        else model.batch
        if level == "batch"
        else getattr(model.batch, field)[0]
    )
    return model, value


@pytest.mark.parametrize("interface", ["fixture", "registry"])
@pytest.mark.parametrize(
    "damage",
    [
        "extra",
        "empty_extra",
        "private",
        "fields_set",
        "wrong_fields_set",
        "missing_field",
        "missing_slot",
    ],
)
def test_unexpected_internal_state_at_every_level_is_rejected_without_leaks(
    interface: str,
    damage: str,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def run() -> None:
        caplog.set_level(logging.DEBUG)
        async with harness() as (fixture, a, _, _):
            assert fixture.authority and fixture.registry
            principal = fixture.authority.resolve(a.cookies[SESSION_COOKIE])
            csrf = fixture.csrf(principal)
            levels = ["batch", "source", "email", "history", "excluded", "context", "commercial"]
            if interface == "fixture":
                levels.append("envelope")
            before = dict(fixture.controls)
            for level in levels:
                model, value = target(level)
                if damage in {"extra", "empty_extra"}:
                    object.__setattr__(
                        value,
                        "__pydantic_extra__",
                        {} if damage == "empty_extra" else {"raw_body": SENTINEL},
                    )
                elif damage == "private":
                    object.__setattr__(value, "__pydantic_private__", {"raw_body": SENTINEL})
                elif damage == "fields_set":
                    value.__pydantic_fields_set__.add("raw_body")
                elif damage == "wrong_fields_set":
                    object.__setattr__(value, "__pydantic_fields_set__", {"raw_body": SENTINEL})
                elif damage == "missing_slot":
                    object.__delattr__(value, "__pydantic_extra__")
                else:
                    value.__dict__.pop(next(iter(type(value).model_fields)))
                with warnings.catch_warnings(record=True) as emitted:
                    warnings.simplefilter("always")
                    with pytest.raises(Denied) as error:
                        if interface == "fixture":
                            await fixture.validate(principal, model, csrf)
                        else:
                            fixture.registry.admit(model.batch)
                assert error.value.status == 422 and not emitted
                assert str(error.value) == "SESSION_FIXTURE_REJECTED"
            captured = capsys.readouterr()
            assert not captured.err and SENTINEL not in captured.out + caplog.text
            assert fixture.controls == before

    asyncio.run(run())


def test_registry_rejects_unserializable_objects_without_invoking_repr(
    caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    class Unsafe:
        def __repr__(self) -> str:
            raise AssertionError("input representation must never run")

    async def run() -> None:
        caplog.set_level(logging.DEBUG)
        async with harness() as (fixture, _, _, _):
            assert fixture.registry
            caplog.clear()  # Scope the no-log assertion to admission, after test login.
            model, value = target("source")
            value.__dict__["record_count"] = Unsafe()
            with warnings.catch_warnings(record=True) as emitted:
                warnings.simplefilter("always")
                with pytest.raises(Denied) as error:
                    fixture.registry.admit(model.batch)
            assert error.value.status == 422 and not emitted
            assert not capsys.readouterr().err and not caplog.records

    asyncio.run(run())


@pytest.mark.parametrize(
    "name,status",
    [
        (b"Host", 422),
        (b"Cookie", 400),
        (b"Origin", 403),
        (b"X-Csrf-Token", 403),
        (b"Content-Type", 415),
        (b"Content-Length", 422),
        (b"Sec-Fetch-Site", 403),
    ],
)
def test_conflicting_case_duplicates_reject_before_body_read(
    name: bytes, status: int, caplog: pytest.LogCaptureFixture
) -> None:
    async def run() -> None:
        async with harness() as (fixture, a, _, _):
            raw = json.dumps(envelope()).encode()
            result, body, reads = await exchange(
                fixture,
                a,
                [raw],
                headers=[
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(raw)).encode()),
                    (name, SENTINEL.encode()),
                ],
            )
            assert result == status and json.loads(body) == ERROR and reads == 0
            assert SENTINEL not in body.decode() + caplog.text

    asyncio.run(run())


def test_all_case_preserved_security_headers_work_for_valid_request() -> None:
    async def run() -> None:
        async with harness() as (fixture, a, _, _):

            async def uppercase(scope: Scope, receive: Receive, send: Send) -> None:
                original = list(scope["headers"])
                copied = {**scope, "headers": [(k.upper(), v) for k, v in original]}
                await fixture.bff(copied, receive, send)
                assert scope["headers"] == original

            async with AsyncClient(
                transport=ASGITransport(app=uppercase),
                base_url=BFF,
                headers=ORIGIN,
                trust_env=False,
            ) as client:
                client.cookies.update(a.cookies)
                response = await submit(client)
                assert response.status_code == 200 and response.json() == RECEIPT

    asyncio.run(run())


def test_header_normalization_copies_names_and_keeps_duplicate_values() -> None:
    original: Any = {"type": "http", "headers": [(b"Host", b"first"), (b"hOsT", b"second")]}
    normalized = admission_scope(original)
    assert normalized is not original
    assert normalized["headers"] == [(b"host", b"first"), (b"host", b"second")]
    assert original["headers"] == [(b"Host", b"first"), (b"hOsT", b"second")]


@pytest.mark.parametrize(
    "name,value",
    [
        (b"bad name", b"x"),
        (b"", b"x"),
        (b":authority", b"x"),
        (b"\xff", b"x"),
        (b"X-Test", b"private\r\nvalue"),
        (b"X-Test", b"private\x00value"),
    ],
)
def test_malformed_raw_headers_fail_before_framework_or_body(
    name: bytes,
    value: bytes,
) -> None:
    async def run() -> None:
        async with harness() as (fixture, a, _, _):
            result, body, reads = await exchange(
                fixture,
                a,
                [SENTINEL.encode()],
                headers=[
                    (name, value),
                ],
            )
            assert result == 422 and json.loads(body) == ERROR and reads == 0

    asyncio.run(run())
