"""Negative synthetic admission matrix, independent of browser assertions."""

import asyncio
import copy
import hashlib
import json
from dataclasses import replace
from typing import Any

import pytest
from admission_test_support import (
    DIGESTS,
    MANIFEST,
    batch,
    envelope,
    example,
    exchange,
    harness,
    submit,
)
from httpx2 import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.main import app
from experiments.admission_fixture import ERROR, RECEIPT, FictionalConsent, create_admission_fixture
from experiments.admission_registry import DATA, MANIFEST_SHA256, SyntheticRegistry
from experiments.minimized_contract import (
    MAX_BODY,
    AdmissionEnvelope,
    MinimizedBatch,
    canonical,
    parse_json,
)
from experiments.ownership_principal import IDENTITIES
from experiments.session_fixture import SESSION_COOKIE
from experiments.session_store import IDLE, Denied

SENTINEL = "SECRET_SENTINEL_PRIVATE_EMAIL_subject_attachment_token@example.com"


@pytest.mark.parametrize("digest", DIGESTS)
@pytest.mark.parametrize("subject", ["a", "b"])
def test_every_complete_registered_envelope_is_validation_only(digest: str, subject: str) -> None:
    async def run() -> None:
        async with harness() as (f, a, b, _):
            before = copy.deepcopy(f.controls)
            assert f.session.store
            sessions = dict(f.session.store.sessions)
            response = await submit(a if subject == "a" else b, envelope(batch(digest)))
            assert response.status_code == 200
            assert response.json() == RECEIPT
            assert response.headers["cache-control"] == "no-store"
            assert f.controls == before and f.session.store.sessions == sessions
            # Replays validate again; no save, IDs, generation advance or retained data.
            assert (
                await submit(a if subject == "a" else b, envelope(batch(digest)))
            ).json() == RECEIPT

    asyncio.run(run())


def test_registry_integrity_and_schema_are_separate_from_phase2() -> None:
    assert hashlib.sha256((DATA / "manifest.json").read_bytes()).hexdigest() == MANIFEST_SHA256
    assert len(MANIFEST["profiles"]) == 70 and len(DIGESTS) == 32
    registry = SyntheticRegistry()
    for digest in DIGESTS:
        model = MinimizedBatch.model_validate(batch(digest))
        encoded = canonical(model)
        assert hashlib.sha256(encoded).hexdigest() == digest
        assert encoded + b"\n" == (DATA / (digest + ".json")).read_bytes()
        registry.admit(model)
    schema = json.loads((DATA / "minimized-evidence-v1.schema.json").read_bytes())
    assert schema == AdmissionEnvelope.model_json_schema()
    assert "minimized-evidence-v1" not in json.dumps(app.openapi())


@pytest.mark.parametrize(
    "field",
    [
        "owner",
        "owner_id",
        "user_id",
        "tenant_id",
        "synthetic_only",
        "hash",
        "sha256",
        "fixture",
        "path",
        "filename",
        "email",
        "subject",
        "recipient",
        "attachment",
        "url",
        "message_id",
        "authorization",
        "raw_body",
        "metadata",
        "classification",
        "confidence",
        "relationships",
        "evidence_state",
    ],
)
@pytest.mark.parametrize(
    "level", ["envelope", "batch", "source", "observation", "excluded", "context", "commercial"]
)
def test_unknown_fields_at_every_object_level_never_reflect(
    field: str, level: str, caplog: pytest.LogCaptureFixture
) -> None:
    async def run() -> None:
        data = envelope(
            example(
                {
                    "excluded": "excluded",
                    "context": "contexts",
                    "commercial": "commercial_groups",
                }.get(level, "observations")
            )
        )
        target = (
            data
            if level == "envelope"
            else data["batch"]
            if level == "batch"
            else data["batch"][
                {
                    "source": "sources",
                    "observation": "observations",
                    "excluded": "excluded",
                    "context": "contexts",
                    "commercial": "commercial_groups",
                }[level]
            ][0]
        )
        # Some legitimate field names already exist: replace with secret scalar, never accept.
        target[field] = SENTINEL
        async with harness() as (f, a, _, _):
            before = copy.deepcopy(f.controls)
            response = await submit(a, data)
            assert response.status_code == 422 and response.json() == ERROR
            assert SENTINEL not in response.text + caplog.text
            assert f.controls == before

    asyncio.run(run())


def mutate(data: dict[str, Any], case: str) -> None:
    b = data["batch"]
    if case == "unknown_batch":
        b["observations"][0]["domain"] = "fictional-library.test"
    elif case in {
        "feature",
        "context",
        "kind",
        "adapter",
        "version",
        "time",
        "time_status",
        "domain",
        "real_domain",
        "null_domain",
    }:
        o = b["observations"][0]
        if case == "feature":
            o["features"] = ["CONFIRMED_ACCOUNT"]
        elif case == "context":
            b["contexts"] = [{"observation_id": o["id"], "features": ["DIAGNOSIS"]}]
        elif case == "kind":
            o["kind"] = "verified_account"
        elif case == "adapter":
            o["adapter"] = "real_provider_v1"
        elif case == "version":
            b["feature_version"] = "email_features_v2"
        elif case == "time":
            o["occurred_at"] = "2101-01-01T00:00:00.000Z"
        elif case == "time_status":
            o["time_status"] = "missing"
        elif case == "domain":
            o["domain"] = "unknown-synthetic.test"
        elif case == "real_domain":
            o["domain"] = "example.com"
        else:
            o["domain"] = None
    elif case == "source_ref":
        b["observations"][0]["source_id"] = "s0020"
    elif case == "row_ref":
        b["observations"][0]["record_index"] = 9999
    elif case == "row_duplicate":
        b["observations"].append(copy.deepcopy(b["observations"][0]))
    elif case == "missing_row":
        b["observations"].pop()
    elif case == "source_duplicate":
        b["sources"].append(copy.deepcopy(b["sources"][0]))
    elif case == "too_many_sources":
        b["sources"] *= 21
    elif case == "too_many_rows":
        b["sources"][0]["record_count"] = 10001
    elif case == "boolean_count":
        b["sources"][0]["record_count"] = True
    elif case == "coercion":
        b["sources"][0]["record_count"] = "1"
    elif case == "reorder":
        b["sources"].reverse()
    elif case == "subset":
        b["sources"].pop()
    elif case == "duplicate_cycle":
        group = b["duplicate_groups"][0]
        next(o for o in b["observations"] if o["id"] == group[0])["duplicate_of"] = group[1]
    elif case == "duplicate_primary":
        b["duplicate_groups"][0][0] = "s0020:r00000"
    elif case == "duplicate_missing":
        b["duplicate_groups"] = []
    elif case == "duplicate_member":
        b["duplicate_groups"][0].append("s0020:r00000")
    elif case == "duplicate_repeat":
        b["duplicate_groups"][0].append(b["duplicate_groups"][0][0])
    elif case == "commercial_domain":
        b["commercial_groups"][0]["domain"] = "fictional-clinic.test"
    elif case == "commercial_missing":
        b["commercial_groups"] = []
    elif case == "commercial_member":
        b["commercial_groups"][0]["members"] = ["s0020:r00000"]
    elif case == "commercial_alias":
        b["commercial_groups"][0]["alias"] = "order9999"
    elif case == "commercial_duplicate":
        b["commercial_groups"].append(copy.deepcopy(b["commercial_groups"][0]))
    elif case == "commercial_reorder":
        b["commercial_groups"][0]["members"].reverse()
    elif case == "context_ref":
        b["contexts"][0]["observation_id"] = "s0020:r00000"
    elif case == "context_duplicate":
        b["contexts"].append(copy.deepcopy(b["contexts"][0]))
    elif case == "history_features":
        next(o for o in b["observations"] if o["adapter"] == "browser_chrome_json_v1")[
            "features"
        ] = ["ACCOUNT_REQUEST"]
    else:
        raise AssertionError(case)


CASES = [
    "unknown_batch",
    "feature",
    "context",
    "kind",
    "adapter",
    "version",
    "time",
    "time_status",
    "domain",
    "real_domain",
    "null_domain",
    "source_ref",
    "row_ref",
    "row_duplicate",
    "missing_row",
    "source_duplicate",
    "too_many_sources",
    "too_many_rows",
    "boolean_count",
    "coercion",
    "reorder",
    "subset",
    "duplicate_cycle",
    "duplicate_primary",
    "duplicate_missing",
    "duplicate_member",
    "duplicate_repeat",
    "commercial_domain",
    "commercial_missing",
    "commercial_member",
    "commercial_alias",
    "commercial_duplicate",
    "commercial_reorder",
    "context_ref",
    "context_duplicate",
    "history_features",
]


@pytest.mark.parametrize("case", CASES)
def test_structural_and_whole_registry_mutations_are_denied(case: str) -> None:
    async def run() -> None:
        field = (
            "duplicate_groups"
            if case.startswith("duplicate_")
            else "commercial_groups"
            if case.startswith("commercial_")
            else "contexts"
            if case.startswith("context_")
            else "observations"
        )
        candidates = [batch(d) for d in DIGESTS if batch(d)[field]]
        if case in {"reorder", "subset"}:
            candidates = [b for b in candidates if len(b["sources"]) > 1]
        if case == "commercial_reorder":
            candidates = [b for b in candidates if len(b[field][0]["members"]) > 1]
        if case == "history_features":
            candidates = [
                b
                for b in candidates
                if any(o["adapter"] == "browser_chrome_json_v1" for o in b["observations"])
            ]
        data = envelope(candidates[0])
        mutate(data, case)
        async with harness() as (f, a, _, _):
            before = copy.deepcopy(f.controls)
            response = await submit(a, data)
            assert response.status_code == 422 and response.json() == ERROR, case
            assert f.controls == before

    asyncio.run(run())


@pytest.mark.parametrize(
    "raw",
    [
        b'{"batch":{},"batch":{}}',
        b'{"__proto__":{}}',
        b'{"x":{"constructor":{}}}',
        b'{"x":[{"prototype":1}]}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":-Infinity}',
        b'{"x":1e999}',
        b'{"x":1.0}',
        b"\xff",
        b"\xef\xbb\xbf{}",
        b'{"x":"\\ud800"}',
        b"[]",
        b"null",
        b"{}{}",
        b"[" * 9 + b"0" + b"]" * 9,
        b"[" * 2000 + b"0" + b"]" * 2000,
    ],
)
def test_strict_json_rejection(raw: bytes) -> None:
    async def run() -> None:
        async with harness() as (_, a, _, _):
            r = await submit(a, raw=raw)
            assert r.status_code == 422 and r.json() == ERROR

    asyncio.run(run())


@pytest.mark.parametrize(
    "headers,status",
    [
        ([(b"content-type", b"multipart/form-data")], 415),
        ([(b"content-type", b"text/plain")], 415),
        ([(b"content-type", b"application/json"), (b"content-encoding", b"gzip")], 415),
        ([(b"content-type", b"application/json"), (b"content-encoding", b"identity")], 415),
        ([(b"content-type", b"application/json"), (b"transfer-encoding", b"chunked")], 415),
        ([(b"content-type", b"application/json")], 415),
        ([(b"content-type", b"application/json"), (b"content-length", b"-1")], 422),
        (
            [
                (b"content-type", b"application/json"),
                (b"content-length", b"2"),
                (b"content-length", b"2"),
            ],
            422,
        ),
        (
            [
                (b"content-type", b"application/json"),
                (b"content-type", b"application/json"),
                (b"content-length", b"2"),
            ],
            415,
        ),
        (
            [
                (b"content-type", b"application/json"),
                (b"content-length", str(MAX_BODY + 1).encode()),
            ],
            413,
        ),
    ],
)
def test_media_and_framing_fail_before_body_read(
    headers: list[tuple[bytes, bytes]], status: int
) -> None:
    async def run() -> None:
        async with harness() as (f, a, _, _):
            result, body, reads = await exchange(f, a, [SENTINEL.encode()], headers=headers)
            assert result == status and json.loads(body) == ERROR and reads == 0

    asyncio.run(run())


@pytest.mark.parametrize("mode", ["fragmented_valid", "actual_oversize", "length_mismatch"])
def test_actual_streamed_bound_and_fragmentation(mode: str) -> None:
    async def run() -> None:
        raw = json.dumps(envelope()).encode()
        async with harness() as (f, a, _, _):
            chunks = (
                [raw[:5], raw[5:]]
                if mode == "fragmented_valid"
                else [b"x" * (MAX_BODY // 2)] * 2 + [b"x"]
                if mode == "actual_oversize"
                else [raw]
            )
            headers = (
                None
                if mode == "fragmented_valid"
                else [(b"content-type", b"application/json"), (b"content-length", b"1")]
            )
            status, body, reads = await exchange(f, a, chunks, headers=headers)
            assert (
                status
                == {"fragmented_valid": 200, "actual_oversize": 413, "length_mismatch": 422}[mode]
            )
            assert reads == len(chunks) and json.loads(body) == (
                RECEIPT if status == 200 else ERROR
            )

    asyncio.run(run())


@pytest.mark.parametrize(
    "case,status",
    [
        ("anonymous", 401),
        ("expired", 401),
        ("missing", 401),
        ("epoch", 401),
        ("csrf", 403),
        ("origin", 403),
        ("owner_header", 422),
        ("query", 422),
        ("no_consent", 403),
        ("consent_epoch", 409),
        ("revision", 409),
        ("consent_version", 422),
        ("foreign_consent", 403),
        ("foreign_csrf", 403),
        ("corrupt_control", 503),
        ("missing_control", 503),
        ("missing_registry", 503),
        ("store_unavailable", 503),
    ],
)
def test_authorization_consent_and_state_fail_closed(case: str, status: int) -> None:
    async def run() -> None:
        async with harness() as (f, a, b, clock):
            assert f.authority and f.session.store
            p = f.authority.resolve(a.cookies[SESSION_COOKIE])
            headers: dict[str, str] = {}
            data = envelope()
            csrf = f.csrf(p)
            if case == "anonymous":
                a.cookies.clear()
            elif case == "expired":
                clock.value += IDLE
            elif case == "missing":
                f.session.store.sessions.pop(p.session_key)
            elif case == "epoch":
                f.session.store.controls[p.subject] = replace(
                    f.session.store.controls[p.subject], epoch=1
                )
            elif case == "csrf":
                headers["x-csrf-token"] = "0" * 64
            elif case == "origin":
                headers["origin"] = "https://evil.test"
            elif case == "owner_header":
                headers["x-user-id"] = SENTINEL
            elif case == "no_consent":
                f.controls[p.owner_id] = FictionalConsent()
            elif case == "consent_epoch":
                data["consent_epoch"] = 2
            elif case == "revision":
                data["expected_revision"] = 2
            elif case == "consent_version":
                data["consent_version"] = "local-processing-v1"
            elif case == "foreign_consent":
                f.controls[p.owner_id] = FictionalConsent()
                assert f.controls[f.authority.resolve(b.cookies[SESSION_COOKIE]).owner_id].granted
            elif case == "foreign_csrf":
                headers["x-csrf-token"] = f.csrf(f.authority.resolve(b.cookies[SESSION_COOKIE]))
            elif case == "corrupt_control":
                f.controls[p.owner_id] = replace(f.controls[p.owner_id], epoch=True)
            elif case == "missing_control":
                f.controls.pop(p.owner_id)
            elif case == "missing_registry":
                f.registry = None
            elif case == "store_unavailable":
                f.session.store.available = False
            path = "/_admission/validate" + ("?owner=" + SENTINEL if case == "query" else "")
            r = await a.post(path, json=data, headers={"x-csrf-token": csrf, **headers})
            assert r.status_code == status and r.json() == ERROR
            assert SENTINEL not in r.text

    asyncio.run(run())


def test_missing_consent_or_auth_does_not_consume_body() -> None:
    async def run() -> None:
        async with harness(consent=False) as (f, a, _, _):
            assert (await exchange(f, a, [SENTINEL.encode()]))[::2] == (403, 0)
            assert f.session.store
            f.session.store.sessions.clear()
            assert (await exchange(f, a, [SENTINEL.encode()]))[::2] == (401, 0)

    asyncio.run(run())


def test_principal_mismatch_and_missing_context_never_fall_back() -> None:
    async def run() -> None:
        async with harness() as (f, a, _, _):
            assert f.authority
            p = f.authority.resolve(a.cookies[SESSION_COOKIE])
            other_owner = next(owner for owner in IDENTITIES.values() if owner != p.owner_id)
            for principal in [
                replace(p, owner_id=other_owner),
                replace(p, subject="fictional-b"),
                replace(p, auth_epoch=1),
                None,
            ]:
                with pytest.raises(Denied):
                    await f.validate(
                        principal,  # type: ignore[arg-type]
                        AdmissionEnvelope.model_validate(envelope()),
                        f.csrf(p),
                    )

    asyncio.run(run())


@pytest.mark.parametrize(
    "timestamp",
    [
        "1969-12-31T23:59:59.000Z",
        "2101-01-01T00:00:00.000Z",
        "2026-02-30T00:00:00.000Z",
        "2026-10-17T12:00:00+00:00",
        "2026-10-17T12:00:60.000Z",
        "2026-10-17T12:00:00Z",
        "2026-10-17T12:00:00.0000000Z",
    ],
)
def test_time_semantics(timestamp: str) -> None:
    data = example()
    data["observations"][0]["occurred_at"] = timestamp
    with pytest.raises(ValidationError):
        MinimizedBatch.model_validate(data)


def test_canonicalization_and_depth_boundaries() -> None:
    data = envelope()
    compact = json.dumps(data, separators=(",", ":")).encode()
    pretty = json.dumps(data, indent=2, sort_keys=True).encode()
    assert canonical(AdmissionEnvelope.model_validate(parse_json(compact)).batch) == canonical(
        AdmissionEnvelope.model_validate(parse_json(pretty)).batch
    )
    assert parse_json(b"[" * 8 + b"0" + b"]" * 8)
    with pytest.raises(ValueError):
        parse_json(b"[" * 9 + b"0" + b"]" * 9)


def test_default_disabled_and_normal_app_remain_separate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOOTPRINT_ADMISSION_ENABLED", "true")
    f = create_admission_fixture()
    assert not f.enabled and f.authority is None and f.registry is None and f.controls == {}
    assert f.session.store is None

    async def run() -> None:
        async with AsyncClient(
            transport=ASGITransport(app=f.bff), base_url="https://127.0.0.1:9444"
        ) as client:
            assert (await client.post("/_admission/validate", json=envelope())).status_code == 404
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            assert (await client.post("/_admission/validate", json=envelope())).status_code == 404
            assert (await client.get("/api/v1/demo")).status_code == 200

    asyncio.run(run())


@pytest.mark.parametrize("damage", ["manifest", "missing", "content", "canonical", "schema"])
def test_registry_corruption_fails_closed(
    damage: str, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    import experiments.admission_registry as module

    for path in DATA.glob("*.json"):
        (tmp_path / path.name).write_bytes(path.read_bytes())
    target = tmp_path / (DIGESTS[0] + ".json")
    if damage == "manifest":
        (tmp_path / "manifest.json").write_bytes(b"{}")
    elif damage == "missing":
        target.unlink()
    elif damage == "content":
        target.write_bytes(b"{}\n")
    elif damage == "canonical":
        target.write_bytes(b" " + target.read_bytes())
    else:
        data = batch()
        data["sources"] = []
        target.write_text(json.dumps(data) + "\n")
    monkeypatch.setattr(module, "DATA", tmp_path)
    with pytest.raises(Denied) as denied:
        SyntheticRegistry()
    assert denied.value.status == 503


def test_secret_path_query_and_error_logs_are_redacted(caplog: pytest.LogCaptureFixture) -> None:
    async def run() -> None:
        async with harness() as (_, a, _, _):
            caplog.set_level("INFO")
            for path in ["/_admission/" + SENTINEL, "/_admission/validate?token=" + SENTINEL]:
                r = await a.post(path, json={"raw_body": SENTINEL})
                assert r.json() == ERROR
                assert SENTINEL not in r.text + str(r.request.url) + caplog.text

    asyncio.run(run())


@pytest.mark.parametrize(
    "field",
    [
        "schema_version",
        "parser_version",
        "feature_version",
        "fusion_version",
        "context_version",
        "assessment_version",
    ],
)
def test_all_version_identifiers_are_exact(field: str) -> None:
    data = example()
    data[field] = SENTINEL
    with pytest.raises(ValidationError):
        MinimizedBatch.model_validate(data)


@pytest.mark.parametrize(
    "field", ["observations", "excluded", "contexts", "duplicate_groups", "commercial_groups"]
)
def test_array_ceiling_is_not_truncation(field: str) -> None:
    data = example(field)
    data[field] = data[field][:1] * 10001
    with pytest.raises(ValidationError):
        MinimizedBatch.model_validate(data)


def test_registry_denies_structurally_valid_but_unregistered_features_and_time() -> None:
    data = example()
    data["observations"][0]["occurred_at"] = "2050-01-01T00:00:00.000Z"
    data["observations"][0]["time_status"] = "valid"
    model = MinimizedBatch.model_validate(data)
    with pytest.raises(Denied) as error:
        SyntheticRegistry().admit(model)
    assert error.value.status == 422


@pytest.mark.parametrize(
    "key",
    [
        "owner",
        "owner_id",
        "user_id",
        "tenant_id",
        "x-user-id",
        "x-owner",
        "x-owner-id",
        "x-tenant-id",
        "authorization",
    ],
)
def test_all_ownership_headers_are_denied_without_consuming_body(key: str) -> None:
    async def run() -> None:
        async with harness() as (f, a, _, _):
            headers = [
                (b"content-type", b"application/json"),
                (b"content-length", b"2"),
                (key.encode(), SENTINEL.encode()),
            ]
            status, body, reads = await exchange(f, a, [b"{}"], headers=headers)
            assert status == 422 and json.loads(body) == ERROR and reads == 0

    asyncio.run(run())
