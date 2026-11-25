"""Bounded adversarial regressions; passing checks are not independent approval."""

import asyncio
import copy
import hashlib
import json
import logging
import random
import socket
import warnings
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from admission_test_support import DIGESTS, batch, envelope, example, exchange, harness, submit
from session_test_support import ORIGIN
from starlette.requests import Request

from experiments.admission_fixture import ERROR, RECEIPT, streamed
from experiments.admission_registry import DATA, SyntheticRegistry
from experiments.minimized_contract import AdmissionEnvelope, MinimizedBatch, canonical
from experiments.session_fixture import SESSION_COOKIE
from experiments.session_store import IDLE, Denied

SENTINEL = "ASSURANCE_PRIVATE_subject_token@example.com"
SEEDS = (60101, 60102, 60103, 60104)


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # Windows creates a loopback socketpair for its event-loop wakeup pipe.
    # Prepare it before forbidding connections by the actual test/generator.
    loop = asyncio.new_event_loop()
    monkeypatch.setattr(asyncio.events, "new_event_loop", lambda: loop)

    def deny(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("assurance cases must not connect to a socket")

    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)
    monkeypatch.setattr(socket, "create_connection", deny)
    try:
        yield
    finally:
        if not loop.is_closed():
            loop.close()


def extra_model(level: str) -> AdmissionEnvelope:
    value = AdmissionEnvelope.model_validate(
        envelope(
            example(
                {
                    "excluded": "excluded",
                    "context": "contexts",
                    "commercial": "commercial_groups",
                }.get(level, "observations")
            )
        )
    )
    target: Any = value if level == "envelope" else value.batch
    if level not in {"envelope", "batch"}:
        target = getattr(
            value.batch,
            {
                "source": "sources",
                "observation": "observations",
                "excluded": "excluded",
                "context": "contexts",
                "commercial": "commercial_groups",
            }[level],
        )[0]
    # This is the exact state produced by target.model_copy(update={"owner_id": ...}).
    # Preserve the parent's reference so nested copies can be tested uniformly.
    copied = target.model_copy(update={"owner_id": SENTINEL})
    target.__dict__.update(copied.__dict__)
    assert target.__dict__["owner_id"] == SENTINEL
    return value


@pytest.mark.parametrize(
    "level", ["envelope", "batch", "source", "observation", "excluded", "context", "commercial"]
)
def test_unvalidated_extra_fields_must_not_be_silently_dropped(level: str) -> None:
    async def run() -> None:
        async with harness() as (fixture, a, _, _):
            assert fixture.authority
            principal = fixture.authority.resolve(a.cookies[SESSION_COOKIE])
            with pytest.raises(Denied):
                await fixture.validate(principal, extra_model(level), fixture.csrf(principal))

    asyncio.run(run())


def test_direct_registry_must_reject_unvalidated_extra_fields() -> None:
    value = MinimizedBatch.model_validate(example()).model_copy(update={"raw_body": SENTINEL})
    with pytest.raises(Denied):
        SyntheticRegistry().admit(value)


def test_direct_registry_must_not_emit_sensitive_serializer_warning() -> None:
    value = MinimizedBatch.model_validate(example())
    value.sources[0].__dict__["record_count"] = SENTINEL
    with warnings.catch_warnings(record=True) as emitted:
        warnings.simplefilter("always")
        with pytest.raises(Denied):
            SyntheticRegistry().admit(value)
    assert SENTINEL not in "".join(str(w.message) for w in emitted)


@pytest.mark.parametrize("value", [True, False, 1.0, "1", None, [], {}, -1, 1_000_001])
def test_nested_unvalidated_known_scalar_is_rejected_without_warning(value: Any) -> None:
    async def run() -> None:
        async with harness() as (fixture, a, _, _):
            assert fixture.authority
            principal = fixture.authority.resolve(a.cookies[SESSION_COOKIE])
            data = AdmissionEnvelope.model_validate(envelope())
            data.batch.sources[0].__dict__["record_count"] = value
            with warnings.catch_warnings(record=True) as emitted:
                warnings.simplefilter("always")
                with pytest.raises(Denied) as error:
                    await fixture.validate(principal, data, fixture.csrf(principal))
            assert error.value.status == 422 and not emitted

    asyncio.run(run())


def leaves(value: Any, path: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    if isinstance(value, dict):
        return [p for key, child in value.items() for p in leaves(child, (*path, key))]
    if isinstance(value, list):
        return [p for index, child in enumerate(value) for p in leaves(child, (*path, index))]
    return [path]


@pytest.mark.parametrize("seed", SEEDS)
def test_seeded_leaf_mutations_cannot_widen_catalog(seed: int) -> None:
    rng = random.Random(seed)
    registry = SyntheticRegistry()
    catalog = {(DATA / (d + ".json")).read_bytes()[:-1] for d in DIGESTS}
    mutations = [SENTINEL, True, 1.5, 10**100, None, {}, [], "unsupported"]
    attempted = 0
    for digest in DIGESTS:
        original = batch(digest)
        paths = leaves(original)
        for _ in range(8):
            data = copy.deepcopy(original)
            path = rng.choice(paths)
            target = data
            for part in path[:-1]:
                target = target[part]
            target[path[-1]] = rng.choice(mutations)
            attempted += 1
            try:
                model = MinimizedBatch.model_validate(data)
            except ValueError:
                continue
            encoded = canonical(model)
            if encoded in catalog:
                # A mutation can be an identity operation or another registered batch.
                registry.admit(model)
            else:
                with pytest.raises(Denied) as error:
                    registry.admit(model)
                assert error.value.status == 422
    assert attempted == 256


@pytest.mark.parametrize(
    "raw",
    [
        b'{"consent_epoch":1,"\\u0063onsent_epoch":1}',
        b'{"x":{"\\u005f_proto__":1}}',
        b'{"x":{"constr\\u0075ctor":1}}',
        b'{"x":{"prot\\u006ftype":1}}',
        b'{"x":"\\udfff"}',
        b'{"x":"\\ud83d\\ude00"}',
        b'{"x":"\\u0000"}',
        b'{"x":"\\u2028"}',
        b'{"x":' + b"9" * 5000 + b"}",
        b'{"x":-999999999999999999999999999999}',
        b'{"x":1e-99999}',
        b'{"x":+1}',
        b'{"x":01}',
    ],
)
def test_escaped_keys_and_integer_parser_edges_are_nonreflecting(
    raw: bytes, caplog: pytest.LogCaptureFixture
) -> None:
    async def run() -> None:
        async with harness() as (_, a, _, _):
            response = await submit(a, raw=raw)
            assert response.status_code == 422 and response.json() == ERROR
            assert raw.decode("ascii") not in response.text + caplog.text

    asyncio.run(run())


def test_equivalent_json_spelling_is_not_extra_admission_authority() -> None:
    async def run() -> None:
        async with harness() as (_, a, _, _):
            data = envelope()
            raw = json.dumps(data, indent=2).replace('"batch"', '"\\u0062atch"').encode()
            assert (await submit(a, raw=raw)).json() == RECEIPT
            # The escaped spelling does not make an unknown field acceptable.
            raw = raw[:-1] + b', "\\u006fwner_id":"PRIVATE"}'
            response = await submit(a, raw=raw)
            assert response.status_code == 422 and response.json() == ERROR

    asyncio.run(run())


def test_digest_collision_without_byte_equality_does_not_admit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = SyntheticRegistry()
    data = example()
    data["observations"][0]["occurred_at"] = "2099-01-01T00:00:00.000Z"
    data["observations"][0]["time_status"] = "valid"
    # Pick a simple batch without duplicate timestamp invariants.
    data["duplicate_groups"] = []
    for observation in data["observations"]:
        observation["duplicate_of"] = None
    model = MinimizedBatch.model_validate(data)
    assert canonical(model) not in {(DATA / (d + ".json")).read_bytes()[:-1] for d in DIGESTS}

    class Collision:
        def hexdigest(self) -> str:
            return DIGESTS[0]

    monkeypatch.setattr(hashlib, "sha256", lambda _: Collision())
    with pytest.raises(Denied) as error:
        registry.admit(model)
    assert error.value.status == 422


@pytest.mark.parametrize("mode", ["one_byte", "empty_fragments", "zero_claim", "short_claim"])
def test_fragmented_and_underdeclared_body_cannot_change_membership(mode: str) -> None:
    async def run() -> None:
        raw = json.dumps(envelope()).encode()
        chunks = [raw[i : i + 1] for i in range(len(raw))]
        if mode == "empty_fragments":
            chunks = [b""] * 64 + [raw]
        claimed = 0 if mode == "zero_claim" else 1 if mode == "short_claim" else len(raw)
        async with harness() as (fixture, a, _, _):
            status, body, reads = await exchange(
                fixture,
                a,
                chunks,
                headers=[
                    (b"content-type", b"application/json"),
                    (b"content-length", str(claimed).encode()),
                ],
            )
            assert status == (422 if mode.endswith("claim") else 200)
            assert json.loads(body) == (ERROR if status == 422 else RECEIPT)
            assert reads == len(chunks)

    asyncio.run(run())


@pytest.mark.parametrize("mode", ["disconnect", "blocked", "empty_frames"])
def test_stream_resource_limitations_are_boundedly_reproduced(mode: str) -> None:
    async def run() -> None:
        calls = 0
        reached = asyncio.Event()
        release = asyncio.Event()

        async def receive() -> Any:
            nonlocal calls
            calls += 1
            if mode == "disconnect":
                return {"type": "http.disconnect"}
            if mode == "empty_frames" and calls <= 128:
                return {"type": "http.request", "body": b"", "more_body": True}
            reached.set()
            await release.wait()
            return {"type": "http.disconnect"}

        request = Request(
            {
                "type": "http",
                "headers": [(b"content-type", b"application/json"), (b"content-length", b"1")],
            },
            receive,
        )
        task = asyncio.create_task(streamed(request))
        if mode == "disconnect":
            from starlette.requests import ClientDisconnect

            with pytest.raises(ClientDisconnect):
                await asyncio.wait_for(task, 1)
        else:
            await asyncio.wait_for(reached.wait(), 1)
            assert (
                not task.done()
            )  # No internal time/frame bound; known residual, not a pass claim.
            assert calls == (129 if mode == "empty_frames" else 1)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(task, 1)

    asyncio.run(run())


@pytest.mark.parametrize("change", ["expired", "recovery", "consent_epoch", "revision"])
def test_invalidation_during_fragmented_body_rejects_before_admission(change: str) -> None:
    async def run() -> None:
        async with harness() as (fixture, a, b, clock):
            assert fixture.authority and fixture.session.store and fixture.session.events
            principal = fixture.authority.resolve(a.cookies[SESSION_COOKIE])
            other = fixture.authority.resolve(b.cookies[SESSION_COOKIE])
            raw = json.dumps(envelope()).encode()
            original = fixture.controls[principal.owner_id]
            entered, release = asyncio.Event(), asyncio.Event()
            calls = 0
            messages: list[Any] = []

            async def receive() -> Any:
                nonlocal calls
                calls += 1
                if calls == 1:
                    return {"type": "http.request", "body": raw[:16], "more_body": True}
                assert calls == 2
                entered.set()
                await release.wait()
                return {"type": "http.request", "body": raw[16:], "more_body": False}

            async def send(message: Any) -> None:
                messages.append(message)

            scope: Any = {
                "type": "http",
                "method": "POST",
                "scheme": "https",
                "path": "/_admission/validate",
                "raw_path": b"/_admission/validate",
                "query_string": b"",
                "root_path": "",
                "http_version": "1.1",
                "client": ("127.0.0.1", 1234),
                "server": ("127.0.0.1", 9444),
                "headers": [
                    (b"host", b"127.0.0.1:9444"),
                    (b"cookie", (SESSION_COOKIE + "=" + a.cookies[SESSION_COOKIE]).encode()),
                    (b"x-csrf-token", fixture.csrf(principal).encode()),
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(raw)).encode()),
                    *[(k.encode(), v.encode()) for k, v in ORIGIN.items()],
                ],
            }
            task = asyncio.create_task(fixture.bff(scope, receive, send))
            await asyncio.wait_for(entered.wait(), 1)
            if change == "expired":
                clock.value += IDLE
            elif change == "recovery":
                await fixture.session.events.apply(
                    fixture.session.events.sign(principal.subject, 1, "recovery")
                )
            else:
                async with fixture.session.store.fence.hold(principal.subject, "assurance"):
                    fixture.controls[principal.owner_id] = (
                        replace(original, epoch=2)
                        if change == "consent_epoch"
                        else replace(original, revision=2)
                    )
            release.set()
            await asyncio.wait_for(task, 1)
            assert messages[0]["status"] == (401 if change in {"expired", "recovery"} else 409)
            assert json.loads(messages[1]["body"]) == ERROR
            assert calls == 2
            if change != "expired":
                assert fixture.authority.validate(other)

    asyncio.run(run())


@pytest.mark.parametrize("damage", ["profiles", "partial_entries", "byte_count", "extra_batch"])
def test_catalog_metadata_and_membership_cannot_be_reenrolled(
    damage: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import experiments.admission_registry as module

    for source in DATA.glob("*.json"):
        (tmp_path / source.name).write_bytes(source.read_bytes())
    manifest = json.loads((tmp_path / "manifest.json").read_bytes())
    if damage == "profiles":
        manifest["profiles"][0]["sources"] = []
    elif damage == "partial_entries":
        manifest["entries"].pop()
    elif damage == "byte_count":
        manifest["entries"][0]["bytes"] += 1
    else:
        manifest["entries"].append(copy.deepcopy(manifest["entries"][0]))
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(module, "DATA", tmp_path)
    with pytest.raises(Denied) as error:
        SyntheticRegistry()
    assert error.value.status == 503


def test_debug_warning_capture_and_responses_do_not_reflect_http_sentinels(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def run() -> None:
        caplog.set_level(logging.DEBUG)
        async with harness() as (_, a, b, _):
            for client in (a, b):
                data = envelope()
                data["batch"]["observations"][0]["features"] = [SENTINEL]
                with warnings.catch_warnings(record=True) as emitted:
                    warnings.simplefilter("always")
                    response = await submit(client, data)
                assert response.status_code == 422 and response.json() == ERROR
                assert response.headers["cache-control"] == "no-store"
                assert SENTINEL not in (
                    response.text
                    + str(response.headers)
                    + caplog.text
                    + "".join(str(w.message) for w in emitted)
                )

    asyncio.run(run())


@pytest.mark.parametrize(
    "name,status",
    [
        ("X-User-ID", 422),
        ("X-Owner-ID", 422),
        ("X-Tenant-ID", 422),
        ("Authorization", 422),
        ("X-Forwarded-Host", 422),
        ("X-HTTP-Method-Override", 422),
        ("Content-Encoding", 415),
        ("Transfer-Encoding", 415),
    ],
)
@pytest.mark.parametrize("capitalized", [False, True])
def test_direct_asgi_forbidden_headers_must_be_case_insensitive(
    name: str, status: int, capitalized: bool
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
                    ((name if capitalized else name.lower()).encode(), SENTINEL.encode()),
                ],
            )
            assert result == status and json.loads(body) == ERROR and reads == 0

    asyncio.run(run())
