"""Symmetric two-user authorization, enumeration and fail-closed negatives."""

import asyncio
import builtins
import copy
import logging
import socket
from dataclasses import replace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from httpx2 import AsyncClient
from ownership_test_support import TabView, broadcast, harness, mutation
from session_test_support import ORIGIN, login, token

from app.main import app
from experiments.oidc_protocol import BFF, ISSUER
from experiments.ownership_fixture import ERROR, create_ownership_fixture
from experiments.ownership_principal import IDENTITIES, AuthenticatedPrincipal
from experiments.ownership_repository import (
    B_SENTINEL,
    MAX_CURSORS,
    SyntheticRecord,
    SyntheticRepository,
)
from experiments.session_fixture import HEADERS, SESSION_COOKIE
from experiments.session_store import ABSOLUTE, IDLE, Denied

BASE = "/_ownership/records"
A, AC, B, BC = (str(UUID(int=i)) for i in (101, 102, 201, 202))


def snapshot(f: Any) -> Any:
    assert f._memory
    return copy.deepcopy((f._memory.records, f._memory.lifecycle, f._memory.cursors))


def safe(response: Any, status: int) -> None:
    assert response.status_code == status, response.text
    assert response.json() == ERROR
    assert all(response.headers.get(k) == v for k, v in HEADERS.items())
    assert "set-cookie" not in response.headers
    assert "access-control-allow-credentials" not in response.headers
    assert B_SENTINEL not in str(response.headers) + response.text


def test_principal_registry_and_mandatory_scope() -> None:
    async def run() -> None:
        async with harness() as (f, a, b, _):
            assert f.authority and f._memory
            pa = f.authority.resolve(a.cookies[SESSION_COOKIE])
            pb = f.authority.resolve(b.cookies[SESSION_COOKIE])
            assert type(pa) is AuthenticatedPrincipal and pa.owner_id != pb.owner_id
            assert pa.issuer == pb.issuer == ISSUER
            assert len(IDENTITIES) == 2 and ("https://foreign.test", pa.subject) not in IDENTITIES
            # Both actual protocol logins used the mock issuer's same email claim.
            assert (await a.get(BASE)).json()["items"][0]["code"] == "SYNTHETIC_A"
            assert (await b.get(BASE)).json()["items"][0]["code"] == B_SENTINEL
            for bad in (
                None,
                replace(pa, owner_id=pb.owner_id),
                replace(pa, subject=pb.subject),
                replace(pa, issuer="https://foreign.test"),
                replace(pa, auth_epoch=True),
                replace(pa, session_key=pb.session_key),
            ):
                with pytest.raises(Denied):
                    f.repository(cast(AuthenticatedPrincipal, bad))
            with pytest.raises(TypeError):
                SyntheticRepository()  # type: ignore[call-arg]
            with pytest.raises(TypeError):
                f.repository()  # type: ignore[call-arg]
            repo = f.repository(pa)
            with pytest.raises(TypeError):
                await repo.count(owner_id=pb.owner_id)  # type: ignore[call-arg]
            for name in ("records", "memory", "all", "unscoped", "find_all", "delete_all"):
                assert not hasattr(repo, name)

    asyncio.run(run())


@pytest.mark.parametrize("swap", [False, True])
@pytest.mark.parametrize(
    "operation",
    [
        "read",
        "update",
        "delete",
        "filter",
        "count",
        "join",
        "nested_parent",
        "nested_child",
        "batch",
        "create_link",
        "update_link",
    ],
)
def test_foreign_and_missing_identical_with_no_state_changes(swap: bool, operation: str) -> None:
    async def run() -> None:
        async with harness() as (f, a, b, _):
            client, own, own_child, foreign = (b, B, BC, A) if swap else (a, A, AC, B)
            before = snapshot(f)
            results = []
            for target in (foreign, str(uuid4())):
                if operation == "read":
                    response = await client.get(BASE + "/" + target)
                elif operation in {"update", "delete"}:
                    data = {"generation": 1, **({"links": []} if operation == "update" else {})}
                    response = await mutation(client, operation, BASE + "/" + target, data)
                elif operation in {"filter", "count"}:
                    response = await client.get(
                        BASE + ("/count" if operation == "count" else ""),
                        params={"related_to": target},
                    )
                elif operation == "join":
                    response = await client.get(BASE + "/" + target + "/children")
                elif operation.startswith("nested"):
                    parent, child = (
                        (target, own_child) if operation == "nested_parent" else (own, target)
                    )
                    response = await client.get(f"{BASE}/{parent}/children/{child}")
                elif operation == "batch":
                    response = await mutation(
                        client, "batch", BASE + "/batch", {"generation": 1, "ids": [own, target]}
                    )
                else:
                    action = "create" if operation == "create_link" else "update"
                    response = await mutation(
                        client,
                        action,
                        BASE + ("/" + own if action == "update" else ""),
                        {"generation": 1, "links": [target]},
                    )
                safe(response, 404)
                assert snapshot(f) == before
                results.append((response.status_code, response.content, dict(response.headers)))
            assert results[0] == results[1]

    asyncio.run(run())


@pytest.mark.parametrize(
    "field",
    [
        "owner",
        "owner_id",
        "user_id",
        "tenant_id",
        "email",
        "subject",
        "iss",
        "principal",
        "claims",
        "__proto__",
    ],
)
@pytest.mark.parametrize("location", ["body", "query", "nested", "batch"])
def test_client_ownership_and_nested_claims_rejected(field: str, location: str) -> None:
    async def run() -> None:
        async with harness() as (f, a, _, _):
            before = snapshot(f)
            if location == "query":
                response = await a.get(BASE, params={field: B})
            elif location == "batch":
                response = await mutation(
                    a, "batch", BASE + "/batch", {"generation": 1, "ids": [{"id": A, field: B}]}
                )
            else:
                data: dict[str, Any] = {"generation": 1, "links": []}
                if location == "body":
                    data[field] = B
                else:
                    data["links"] = [{"id": AC, field: B}]
                response = await mutation(a, "create", data=data)
            safe(response, 422)
            assert snapshot(f) == before

    asyncio.run(run())


@pytest.mark.parametrize(
    "header", ["x-user-id", "x-owner", "x-owner-id", "x-tenant-id", "authorization"]
)
def test_ownership_headers_rejected(header: str) -> None:
    async def run() -> None:
        async with harness() as (f, a, _, _):
            before = snapshot(f)
            safe(await a.get(BASE, headers={header: B_SENTINEL}), 422)
            safe(await mutation(a, "create", headers={header: B_SENTINEL}), 422)
            assert snapshot(f) == before

    asyncio.run(run())


@pytest.mark.parametrize(
    "path",
    [
        "/owner/" + B,
        "/" + B + "/records",
        "/records/" + B + "/owner/" + A,
        "/records/not-a-uuid",
        "/records/" + B.upper(),
    ],
)
def test_forged_or_malformed_paths(path: str) -> None:
    async def run() -> None:
        async with harness() as (f, a, _, _):
            before = snapshot(f)
            response = await a.get("/_ownership" + path)
            safe(
                response,
                422 if path.startswith("/records/not-") or path == "/records/" + B.upper() else 404,
            )
            assert snapshot(f) == before

    asyncio.run(run())


def test_owned_crud_relationships_batch_and_generation() -> None:
    async def run() -> None:
        async with harness() as (f, a, b, _):
            assert (await a.get(BASE + "/count")).json() == {"count": 2}
            assert (await a.get(BASE, params={"related_to": A})).json()["items"][0]["id"] == AC
            assert (await a.get(f"{BASE}/{A}/children/{AC}")).json()["id"] == AC
            assert len((await a.get(f"{BASE}/{A}/children")).json()["items"]) == 1
            before_b = (await b.get(BASE)).content
            created = await mutation(a, "create", data={"generation": 1, "links": [AC]})
            assert created.status_code == 201 and created.json()["synthetic"]
            new_id = created.json()["id"]
            safe(await mutation(a, "create"), 409)
            changed = await mutation(
                a, "update", BASE + "/" + new_id, {"generation": 2, "links": []}
            )
            assert changed.status_code == 200 and changed.json()["code"] == "SYNTHETIC_UPDATED"
            assert (
                await mutation(a, "delete", BASE + "/" + AC, {"generation": 3})
            ).status_code == 200
            assert (await a.get(f"{BASE}/{A}/children")).json() == {"items": []}
            assert (
                await mutation(a, "batch", BASE + "/batch", {"generation": 4, "ids": [A, new_id]})
            ).status_code == 200
            assert (await a.get(BASE + "/count")).json() == {"count": 0}
            assert (await b.get(BASE)).content == before_b

    asyncio.run(run())


def test_cursors_counts_filters_and_b_only_metadata_changes() -> None:
    async def run() -> None:
        async with harness() as (f, a, b, _):
            first = (await a.get(BASE, params={"limit": "1"})).json()
            cursor = first["cursor"]
            second = await a.get(BASE, params={"limit": "1", "cursor": cursor})
            assert second.json()["items"][0]["id"] == AC and second.json()["cursor"] is None
            foreign = (await b.get(BASE, params={"limit": "1"})).json()["cursor"]
            for candidate in (foreign, "x" * 43, cursor[:-1] + ("a" if cursor[-1] != "a" else "b")):
                safe(await a.get(BASE, params={"limit": "1", "cursor": candidate}), 404)
            safe(await a.get(BASE, params={"limit": "2", "cursor": cursor}), 404)
            safe(await a.get(BASE, params={"limit": "1", "cursor": cursor, "related_to": A}), 404)
            before = (await a.get(BASE)).content, (await a.get(BASE + "/count")).content
            assert (await mutation(b, "create")).status_code == 201
            assert before == ((await a.get(BASE)).content, (await a.get(BASE + "/count")).content)
            assert (
                await a.get(BASE, params={"limit": "1", "cursor": cursor})
            ).content == second.content
            # A different session for the same owner cannot reuse this cursor.
            async with AsyncClient(
                transport=f.transport, base_url=BFF, headers=ORIGIN, trust_env=False
            ) as tab:
                await login(f.session, tab)
                safe(await tab.get(BASE, params={"limit": "1", "cursor": cursor}), 404)
            assert (await mutation(a, "create")).status_code == 201
            safe(await a.get(BASE, params={"limit": "1", "cursor": cursor}), 409)
            assert B_SENTINEL not in str(before) + second.text

    asyncio.run(run())


@pytest.mark.parametrize(
    "params",
    [
        {"limit": "0"},
        {"limit": "9"},
        {"limit": "01"},
        {"cursor": "bad"},
        {"cursor": "!" * 43},
        {"related_to": "bad"},
        {"order": B_SENTINEL},
        [("limit", "1"), ("limit", "2")],
    ],
)
def test_malformed_query_is_fixed(params: Any) -> None:
    async def run() -> None:
        async with harness() as (f, a, _, _):
            before = snapshot(f)
            safe(await a.get(BASE, params=params), 422)
            assert snapshot(f) == before

    asyncio.run(run())


def test_capacity_is_bounded_per_owner() -> None:
    async def run() -> None:
        async with harness() as (_, a, b, _):
            for _ in range(MAX_CURSORS):
                assert (await a.get(BASE, params={"limit": 1})).status_code == 200
            safe(await a.get(BASE, params={"limit": 1}), 429)
            assert (await b.get(BASE, params={"limit": 1})).status_code == 200
            for generation in range(1, 7):
                assert (
                    await mutation(a, "create", data={"generation": generation, "links": []})
                ).status_code == 201
            safe(await mutation(a, "create", data={"generation": 7, "links": []}), 429)
            assert (await mutation(b, "create")).status_code == 201

    asyncio.run(run())


@pytest.mark.parametrize(
    "case",
    [
        "missing",
        "invalid",
        "expired_idle",
        "expired_absolute",
        "epoch",
        "inactive",
        "quarantined",
        "missing_control",
        "corrupt_session",
        "missing_session",
        "outage",
        "record",
        "owner",
        "link",
        "lifecycle",
        "cursor",
        "availability",
    ],
)
def test_bad_session_and_repository_state_fail_closed(case: str) -> None:
    async def run() -> None:
        async with harness() as (f, a, b, clock):
            assert f.authority and f.session.store and f._memory
            store, memory = f.session.store, f._memory
            handle = a.cookies[SESSION_COOKIE]
            p = f.authority.resolve(handle)
            code = 401
            if case == "missing":
                a.cookies.clear()
            elif case == "invalid":
                a.cookies.clear()
                a.headers["cookie"] = SESSION_COOKIE + "=invalid"
            elif case == "expired_idle":
                clock.value += IDLE
            elif case == "expired_absolute":
                clock.value += ABSOLUTE
            elif case in {"epoch", "inactive", "quarantined"}:
                kwargs = (
                    {"epoch": 1}
                    if case == "epoch"
                    else {"active": False}
                    if case == "inactive"
                    else {"quarantined": True}
                )
                store.controls[p.subject] = replace(store.controls[p.subject], **kwargs)
            elif case == "missing_control":
                del store.controls[p.subject]
                code = 503
            elif case == "corrupt_session":
                store.sessions[p.session_key] = replace(store.sessions[p.session_key], key="wrong")
                code = 503
            elif case == "missing_session":
                del store.sessions[p.session_key]
            elif case == "outage":
                store.available = False
                code = 503
            else:
                code = 503
                if case == "record":
                    memory.records[UUID(A)] = cast(SyntheticRecord, None)
                elif case == "owner":
                    memory.records[UUID(A)] = replace(memory.records[UUID(A)], owner=uuid4())
                elif case == "link":
                    memory.records[UUID(A)] = replace(memory.records[UUID(A)], links=(UUID(B),))
                elif case == "lifecycle":
                    memory.lifecycle[p.owner_id] = replace(
                        memory.lifecycle[p.owner_id], generation=True
                    )
                elif case == "availability":
                    memory.available = cast(bool, 1)
                else:
                    memory.cursors[p.owner_id]["bad"] = cast(Any, None)
            before = snapshot(f)
            safe(await a.get(BASE), code)
            assert snapshot(f) == before
            if case not in {
                "expired_idle",
                "expired_absolute",
                "missing_control",
                "outage",
                "record",
                "owner",
                "link",
                "lifecycle",
                "cursor",
                "availability",
            }:
                assert (await b.get(BASE)).status_code == 200

    asyncio.run(run())


@pytest.mark.parametrize(
    "case",
    [
        "missing",
        "foreign",
        "wrong_action",
        "origin",
        "metadata",
        "duplicate",
        "override",
        "malformed",
    ],
)
def test_csrf_and_origin_fail_without_writes(case: str) -> None:
    async def run() -> None:
        async with harness() as (f, a, b, _):
            tokens = (await a.get("/_ownership/csrf")).json()["tokens"]
            headers: Any = {"x-csrf-token": tokens["create"]}
            if case == "missing":
                headers = {}
            elif case == "foreign":
                headers["x-csrf-token"] = (await b.get("/_ownership/csrf")).json()["tokens"][
                    "create"
                ]
            elif case == "wrong_action":
                headers["x-csrf-token"] = tokens["delete"]
            elif case == "origin":
                headers["origin"] = "https://attacker.test"
            elif case == "metadata":
                headers["sec-fetch-site"] = "cross-site"
            elif case == "duplicate":
                headers = [("x-csrf-token", tokens["create"])] * 2
            elif case == "malformed":
                headers = [(b"x-csrf-token", b"\xff" * 64)]
            else:
                headers["x-http-method-override"] = "DELETE"
            before = snapshot(f)
            safe(await a.post(BASE, json={"generation": 1, "links": []}, headers=headers), 403)
            assert snapshot(f) == before
            # Consuming an ownership token invalidates all previous ownership tokens.
            assert (
                await a.post(
                    BASE,
                    json={"generation": 1, "links": []},
                    headers={"x-csrf-token": tokens["create"]},
                )
            ).status_code == 201
            safe(
                await a.post(
                    BASE,
                    json={"generation": 2, "links": []},
                    headers={"x-csrf-token": tokens["create"]},
                ),
                403,
            )

    asyncio.run(run())


@pytest.mark.parametrize(
    "raw",
    [
        b'{"generation":1,"generation":1,"links":[]}',
        b'{"generation":true,"links":[]}',
        b'{"generation":NaN,"links":[]}',
        b'{"generation":1,"links":[{"id":"foreign","owner":"b"}]}',
        b"[]",
        b"x" * 2049,
    ],
)
def test_strict_json_negative(raw: bytes) -> None:
    async def run() -> None:
        async with harness() as (f, a, _, _):
            csrf = (await a.get("/_ownership/csrf")).json()["tokens"]["create"]
            before = snapshot(f)
            safe(
                await a.post(
                    BASE,
                    content=raw,
                    headers={"x-csrf-token": csrf, "content-type": "application/json"},
                ),
                422,
            )
            assert snapshot(f) == before

    asyncio.run(run())


def test_two_tab_logout_account_switch_and_late_response_model() -> None:
    async def run() -> None:
        async with harness() as (f, a, b, _):
            tabs = (TabView(), TabView())
            response = await a.get(BASE)
            ticket = tabs[0].generation
            for tab in tabs:
                tab.accept(ticket, response.json()["items"])
            handle = a.cookies[SESSION_COOKIE]
            csrf = await token(a, "POST:/_session/logout")
            assert (
                await a.post("/_session/logout", json={}, headers={"x-csrf-token": csrf})
            ).status_code == 200
            broadcast(tabs, "invalidate")
            for tab in tabs:
                tab.accept(ticket, response.json()["items"])
                assert not tab.rows
            # Another HTTP client/tab reusing the shared revoked cookie is denied.
            async with AsyncClient(
                transport=f.transport,
                base_url=BFF,
                headers={**ORIGIN, "cookie": SESSION_COOKIE + "=" + handle},
                trust_env=False,
            ) as stale:
                safe(await stale.get(BASE), 401)
            # Switching to B also invalidates the ticket before accepting B's response.
            broadcast(tabs, "invalidate")
            tabs[0].accept(tabs[0].generation, (await b.get(BASE)).json()["items"])
            tabs[0].accept(ticket, response.json()["items"])
            assert all(row["code"] == B_SENTINEL for row in tabs[0].rows)

    asyncio.run(run())


def test_no_egress_persistence_or_secret_log_metadata(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    async def run() -> None:
        async with harness() as (f, a, _, _):
            original = builtins.open

            def guarded(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
                assert not any(flag in mode for flag in "wax+")
                return original(file, mode, *args, **kwargs)

            def network(*args: Any, **kwargs: Any) -> Any:
                raise AssertionError("Network forbidden")

            monkeypatch.setattr(builtins, "open", guarded)
            monkeypatch.setattr(socket, "getaddrinfo", network)
            monkeypatch.setattr(socket.socket, "connect", network)
            caplog.set_level(logging.DEBUG)
            assert (await mutation(a, "create")).status_code == 201
            safe(await a.get(BASE + "/" + B), 404)
            safe(await a.get(BASE, params={"owner_id": B_SENTINEL}), 422)
            response = await a.get(BASE)
            assert B_SENTINEL not in response.text
            assert B_SENTINEL not in caplog.text and B not in caplog.text
            assert a.cookies[SESSION_COOKIE] not in caplog.text
            assert "/_ownership/redacted" in caplog.text
            with pytest.raises(Denied):
                await a.get("https://external.test/_ownership/records")
            f.clear()
            assert f._memory and not f._memory.available and not f._memory.records
            safe(await a.get(BASE), 503)

    asyncio.run(run())


def test_default_disabled_normal_routes_and_lifespan(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOOTPRINT_OWNERSHIP_ENABLED", "true")
    disabled = create_ownership_fixture()
    assert not disabled.bff.routes and disabled.authority is None and disabled._memory is None
    with TestClient(app) as c:
        for path in (BASE, "/_ownership/csrf", BASE + "/count", BASE + "/" + A, BASE + "/batch"):
            assert c.get(path).status_code == 404
            assert c.post(path, json={}).status_code == 404
        assert "_ownership" not in c.get("/openapi.json").text
    f = create_ownership_fixture(enabled=True)
    with TestClient(f.bff, base_url=BFF, headers=ORIGIN, client=("127.0.0.1", 1)) as c:
        safe(c.get(BASE), 401)
    assert f._memory and not f._memory.available and not f._memory.records
    assert f.session.store and not f.session.store.available
    disabled.clear()


def test_inventory_is_explicit_and_future_rules_are_not_routes() -> None:
    from experiments.ownership_inventory import INVENTORY

    fixture = create_ownership_fixture(enabled=True)
    try:
        current = [r for r in INVENTORY if r.family.startswith("/_ownership")]
        assert {method for r in current for method in r.methods} == {
            "GET",
            "POST",
            "PATCH",
            "DELETE",
        }
        assert len(current) == 9
        for rule in current:
            assert rule.implemented and rule.session != "none" and rule.owner != "none"
            assert rule.consent_generation != "none" and rule.lifecycle != "none"
        future = [r for r in INVENTORY if not r.implemented]
        assert len(future) == 6 and all(r.family.startswith("future:") for r in future)
        assert all(r.session != "none" and r.owner != "none" for r in future)
        assert not any("future:" in getattr(route, "path", "") for route in fixture.bff.routes)
    finally:
        fixture.clear()


@pytest.mark.parametrize(
    "case",
    [
        "media",
        "empty_batch",
        "duplicate_batch",
        "duplicate_links",
        "unrelated_nested",
        "get_body",
        "owner_header",
    ],
)
def test_additional_input_and_relationship_negatives(case: str) -> None:
    async def run() -> None:
        async with harness() as (f, a, _, _):
            before = snapshot(f)
            if case == "media":
                response = await mutation(a, "create", headers={"content-type": "text/plain"})
            elif case in {"empty_batch", "duplicate_batch"}:
                response = await mutation(
                    a,
                    "batch",
                    BASE + "/batch",
                    {"generation": 1, "ids": [] if case == "empty_batch" else [A, A]},
                )
            elif case == "duplicate_links":
                response = await mutation(a, "create", data={"generation": 1, "links": [AC, AC]})
            elif case == "unrelated_nested":
                response = await a.get(f"{BASE}/{A}/children/{A}")
            elif case == "get_body":
                response = await a.request("GET", BASE, content=b"x" * 2049)
            else:
                response = await a.get(BASE, headers={"owner": B})
            safe(response, 404 if case == "unrelated_nested" else 422)
            assert snapshot(f) == before

    asyncio.run(run())


def test_corrupt_sentinel_ownership_and_cached_principal_fail_closed() -> None:
    async def run() -> None:
        async with harness() as (f, a, _, _):
            assert f.authority and f._memory
            p = f.authority.resolve(a.cookies[SESSION_COOKIE])
            repo = f.repository(p)
            f._memory.records[UUID(B)] = replace(
                f._memory.records[UUID(B)], owner=p.owner_id, links=()
            )
            with pytest.raises(Denied) as error:
                await repo.count()
            assert error.value.status == 503
            safe(await a.get(BASE), 503)
            for corrupt in (replace(p, issuer=cast(str, [])), replace(p, subject=cast(str, {}))):
                with pytest.raises(Denied):
                    f.repository(corrupt)

    asyncio.run(run())


@pytest.mark.parametrize("case", ["root", "prefix", "method", "unicode"])
def test_framework_redirect_and_method_errors_cannot_echo_identifiers(case: str) -> None:
    async def run() -> None:
        async with harness() as (f, a, _, _):
            before = snapshot(f)
            path = (
                "/_ownership"
                if case == "root"
                else "/_ownershipevil"
                if case == "prefix"
                else BASE + "/\u00e9"
                if case == "unicode"
                else BASE
            )
            response = await a.request(
                "TRACE" if case == "method" else "GET", path, params={"owner_id": B_SENTINEL}
            )
            safe(response, 404 if case in {"root", "prefix"} else 422)
            assert "location" not in response.headers
            assert snapshot(f) == before

    asyncio.run(run())
