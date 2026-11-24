import asyncio
import base64
import builtins
import copy
import logging
import secrets
import socket
from dataclasses import replace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from httpx2 import AsyncClient
from joserfc import jwt
from joserfc.jwk import RSAKey
from session_test_support import ORIGIN, authorize, harness, login, pending, token

from app.main import app
from experiments.oidc_protocol import BFF, ISSUER
from experiments.session_events import HEADER
from experiments.session_fixture import (
    MAX_PENDING,
    PREAUTH_COOKIE,
    SESSION_COOKIE,
    create_session_fixture,
)
from experiments.session_store import IDLE, MAX_PER_OWNER, Denied, digest


def test_valid_login_cookie_digest_and_deletion() -> None:
    async def run() -> None:
        async with harness() as (f, c, _, _):
            handle = await login(f, c)
            assert f.store
            assert len(handle) == 43 and handle not in repr(f.store.sessions)
            assert set(f.store.sessions) == {digest(handle)}
            assert f.store.lookup(handle)[1].owner == "fictional-a"
            csrf = await token(c, "POST:/_session/logout")
            response = await c.post("/_session/logout", json={}, headers={"x-csrf-token": csrf})
            assert response.status_code == 200
            flags = response.headers["set-cookie"]
            assert all(
                v in flags
                for v in (
                    SESSION_COOKIE,
                    "HttpOnly",
                    "Secure",
                    "SameSite=lax",
                    "Path=/",
                    "Max-Age=0",
                )
            )
            assert "Domain=" not in flags and not c.cookies
            assert not f.store.sessions
            assert (
                await c.get("/_session/me", headers={"cookie": f"{SESSION_COOKIE}={handle}"})
            ).status_code == 401

    asyncio.run(run())


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_one_use_session_action_csrf(method: str) -> None:
    async def run() -> None:
        async with harness() as (f, c, clock, _):
            await login(f, c)
            csrf = await token(c, method + ":/_session/marker")
            response = await c.request(
                method, "/_session/marker", json={}, headers={"x-csrf-token": csrf}
            )
            assert response.status_code == 200 and f.store
            assert f.store.controls["fictional-a"].markers == 1
            snapshot = copy.deepcopy((f.store.sessions, f.store.controls))
            clock.value += 1
            assert (
                await c.request(method, "/_session/marker", json={}, headers={"x-csrf-token": csrf})
            ).status_code == 403
            assert snapshot == (f.store.sessions, f.store.controls)

    asyncio.run(run())


@pytest.mark.parametrize(
    "case",
    [
        "missing_token",
        "wrong_token",
        "foreign_token",
        "missing_origin",
        "origin",
        "null_origin",
        "same_site",
        "cross_site",
        "fetch_mode",
        "fetch_dest",
        "missing_fetch",
        "content_type",
        "no_json",
        "extra_body",
        "duplicate_json",
        "huge_body",
        "duplicate_origin",
        "duplicate_token",
        "method_override",
        "owner_header",
        "query",
        "duplicate_cookie",
        "duplicate_host",
        "forwarded_proto",
    ],
)
def test_rejections_do_not_mutate_state(case: str) -> None:
    async def run() -> None:
        async with harness() as (f, c, clock, _):
            handle = await login(f, c)
            csrf = await token(c)
            assert f.store
            snapshot = copy.deepcopy((f.store.sessions, f.store.controls))
            clock.value += 10
            headers = {**ORIGIN, "x-csrf-token": csrf, "content-type": "application/json"}
            body = b"{}"
            path = "/_session/marker"
            if case == "missing_token":
                headers.pop("x-csrf-token")
            if case in {"wrong_token", "foreign_token"}:
                headers["x-csrf-token"] = secrets.token_urlsafe(32)
            if case == "missing_origin":
                headers.pop("origin")
            if case == "origin":
                headers["origin"] = "https://attacker.test"
            if case == "null_origin":
                headers["origin"] = "null"
            if case == "same_site":
                headers["sec-fetch-site"] = "same-site"
            if case == "cross_site":
                headers["sec-fetch-site"] = "cross-site"
            if case == "fetch_mode":
                headers["sec-fetch-mode"] = "navigate"
            if case == "fetch_dest":
                headers["sec-fetch-dest"] = "document"
            if case == "missing_fetch":
                headers.pop("sec-fetch-site")
            if case == "content_type":
                headers["content-type"] = "text/plain"
            if case == "no_json":
                body = b"not-json"
            if case == "extra_body":
                body = b'{"user_id":"fictional-b"}'
            if case == "duplicate_json":
                body = b'{"x":1,"x":2}'
            if case == "huge_body":
                body = b" " * 65
            if case == "method_override":
                headers["x-http-method-override"] = "GET"
            if case == "owner_header":
                headers["x-user-id"] = "fictional-b"
            if case == "query":
                path += "?user_id=fictional-b"
            if case == "duplicate_cookie":
                headers["cookie"] = f"{SESSION_COOKIE}={handle}; {SESSION_COOKIE}={handle}"
            if case == "forwarded_proto":
                headers["x-forwarded-proto"] = "http"
            pairs = list(headers.items())
            if case == "duplicate_origin":
                pairs.append(("origin", BFF))
            if case == "duplicate_token":
                pairs.append(("x-csrf-token", csrf))
            if case == "duplicate_host":
                pairs.extend([("host", "127.0.0.1:9444"), ("host", "attacker.test")])
            # Build a clean client so deleted test headers aren't inherited.
            async with AsyncClient(
                transport=f.transport, base_url=BFF, cookies=c.cookies, trust_env=False
            ) as attacker:
                response = await attacker.post(path, content=body, headers=pairs)
            assert response.status_code in {400, 403, 413, 415, 422}
            assert snapshot == (f.store.sessions, f.store.controls)
            assert response.headers["cache-control"] == "no-store"
            assert response.headers["referrer-policy"] == "no-referrer"
            assert "access-control-allow-origin" not in response.headers

    asyncio.run(run())


@pytest.mark.parametrize("delta,expected", [(1799, 200), (1800, 401), (1801, 401)])
def test_idle_boundary(delta: int, expected: int) -> None:
    async def run() -> None:
        async with harness() as (f, c, clock, _):
            await login(f, c)
            clock.value += delta
            assert (await c.get("/_session/me")).status_code == expected

    asyncio.run(run())


@pytest.mark.parametrize("delta,expected", [(43199, 200), (43200, 401), (43201, 401)])
def test_absolute_boundary_never_extended(delta: int, expected: int) -> None:
    async def run() -> None:
        async with harness() as (f, c, clock, _):
            handle = await login(f, c)
            assert f.store
            key, record = f.store.lookup(handle)
            clock.value += delta
            f.store.sessions[key] = replace(record, last_seen=clock.value - 1)
            assert (await c.get("/_session/me")).status_code == expected
            assert f.store.sessions[key].absolute == record.absolute

    asyncio.run(run())


@pytest.mark.parametrize("step_up", [False, True])
def test_rotation_fixation_and_original_absolute(step_up: bool) -> None:
    async def run() -> None:
        async with harness() as (f, c, clock, _):
            handle = await login(f, c)
            assert f.store
            absolute = f.store.lookup(handle)[1].absolute
            clock.value += 100
            if step_up:
                csrf = await token(c, "POST:/_session/step-up")
                start = await c.post("/_session/step-up", json={}, headers={"x-csrf-token": csrf})
            else:
                start = await pending(f, c)
            response = await authorize(f, c, start)
            new = c.cookies[SESSION_COOKIE]
            assert response.headers["location"] == "/_spike/complete" and new != handle
            assert f.store.lookup(new)[1].absolute == absolute
            with pytest.raises(Denied):
                f.store.lookup(handle)
            assert all(
                v in response.headers.get_list("set-cookie")[-1]
                for v in ("HttpOnly", "Secure", "SameSite=lax", "Path=/")
            )
            assert "Domain=" not in response.headers.get_list("set-cookie")[-1]
            assert "Max-Age=" not in response.headers.get_list("set-cookie")[-1]

    asyncio.run(run())


def test_chosen_fixation_cookie_and_preauth_are_not_sessions() -> None:
    async def run() -> None:
        async with harness() as (f, c, _, _):
            chosen = secrets.token_urlsafe(32)
            c.cookies.set(SESSION_COOKIE, chosen, domain="127.0.0.1", path="/")
            pre = await c.get("/_session/preauth")
            binding = c.cookies[PREAUTH_COOKIE]
            assert f.store
            with pytest.raises(Denied):
                f.store.lookup(binding)
            start = await c.post(
                "/_spike/start", json={}, headers={"x-csrf-token": pre.json()["csrf"]}
            )
            await authorize(f, c, start)
            assert c.cookies[SESSION_COOKIE] not in {chosen, binding}
            with pytest.raises(Denied):
                f.store.lookup(chosen)

    asyncio.run(run())


@pytest.mark.parametrize("case", ["missing", "wrong", "expired", "replay"])
def test_preauth_login_csrf(case: str) -> None:
    async def run() -> None:
        async with harness() as (f, c, clock, _):
            pre = await c.get("/_session/preauth")
            csrf = pre.json()["csrf"]
            if case == "wrong":
                csrf = secrets.token_urlsafe(32)
            if case == "expired":
                clock.value += 300
            if case == "replay":
                assert (
                    await c.post("/_spike/start", json={}, headers={"x-csrf-token": csrf})
                ).status_code == 303
            response = await c.post(
                "/_spike/start",
                json={},
                headers={} if case == "missing" else {"x-csrf-token": csrf},
            )
            assert response.status_code == 403 and f.store and not f.store.sessions

    asyncio.run(run())


@pytest.mark.parametrize("kind", ["recovery", "mfa_reset"])
def test_signed_event_replay_order_and_independent_identities(kind: str) -> None:
    async def run() -> None:
        async with harness() as (f, c, _, _):
            a = await login(f, c)
            # Independent browser jar, same fictional email from unchanged issuer.
            async with AsyncClient(
                transport=f.transport, base_url=BFF, headers=ORIGIN, trust_env=False
            ) as b:
                bh = await login(f, b, "fictional-b")
                assert f.store and f.events
                event = f.events.sign("fictional-a", 1, kind)
                with pytest.raises(Denied):
                    await f.events.apply(f.events.sign("fictional-a", 2, kind))
                assert f.store.lookup(a)
                await f.events.apply(event)
                with pytest.raises(Denied):
                    await f.events.apply(event)
                with pytest.raises(Denied):
                    f.store.lookup(a)
                assert f.store.lookup(bh)[1].owner == "fictional-b"
                await f.events.apply(f.events.sign("fictional-a", 2, kind))
                assert f.store.controls["fictional-a"].epoch == 2

    asyncio.run(run())


@pytest.mark.parametrize(
    "case",
    [
        "issuer",
        "audience",
        "identity_issuer",
        "subject",
        "kind",
        "sequence",
        "bool_sequence",
        "future_iat",
        "future_nbf",
        "expired",
        "long_lifetime",
        "missing_jti",
        "header",
        "signature",
        "unsigned",
        "oversized",
        "malformed",
    ],
)
def test_invalid_events_do_not_change_state(case: str) -> None:
    async def run() -> None:
        async with harness() as (f, c, _, wall):
            await login(f, c)
            assert f.events and f.events.key and f.store
            encoded = f.events.sign("fictional-a", 1)
            claims = jwt.decode(encoded, f.events.key).claims
            header = dict(HEADER)
            changes = {
                "issuer": ("iss", "https://attacker.test"),
                "audience": ("aud", "wrong"),
                "identity_issuer": ("identity_issuer", "https://other.test"),
                "subject": ("sub", "unknown"),
                "kind": ("kind", "login"),
                "sequence": ("sequence", 0),
                "bool_sequence": ("sequence", True),
                "future_iat": ("iat", int(wall.value) + 1),
                "future_nbf": ("nbf", int(wall.value) + 1),
                "expired": ("exp", int(wall.value)),
                "long_lifetime": ("exp", int(wall.value) + 61),
            }
            if case in changes:
                name, value = changes[case]
                claims[name] = value
            if case == "missing_jti":
                claims.pop("jti")
            if case == "header":
                header["jku"] = "https://attacker.test/keys"
            key = RSAKey.generate_key(2048) if case == "signature" else f.events.key
            encoded = jwt.encode(header, claims, key)
            if case == "unsigned":
                encoded = encoded.rsplit(".", 1)[0] + "."
            if case == "oversized":
                encoded = "SYNTHETIC_SECRET" * 1000
            if case == "malformed":
                encoded = "SYNTHETIC_SECRET"
            snapshot = copy.deepcopy((f.store.sessions, f.store.controls))
            with pytest.raises(Denied):
                await f.events.apply(encoded)
            assert snapshot == (f.store.sessions, f.store.controls)

    asyncio.run(run())


@pytest.mark.parametrize(
    "case",
    [
        "unavailable",
        "read_error",
        "missing",
        "epoch",
        "inactive",
        "quarantine",
        "corrupt_owner",
        "corrupt_epoch",
        "corrupt_time",
        "future_last_seen",
        "corrupt_tokens",
        "corrupt_key",
        "duplicate_csrf",
    ],
)
def test_store_unavailable_missing_corrupted_or_stale(case: str) -> None:
    async def run() -> None:
        async with harness() as (f, c, _, _):
            handle = await login(f, c)
            assert f.store
            key, record = f.store.lookup(handle)
            if case == "unavailable":
                f.store.available = False
            if case == "read_error":
                f.store.fail_on = "read"
            if case == "missing":
                f.store.sessions.pop(key)
            if case == "epoch":
                f.store.controls[record.owner] = replace(f.store.controls[record.owner], epoch=1)
            if case == "inactive":
                f.store.controls[record.owner] = replace(
                    f.store.controls[record.owner], active=False
                )
            if case == "quarantine":
                f.store.controls[record.owner] = replace(
                    f.store.controls[record.owner], quarantined=True
                )
            if case == "corrupt_owner":
                f.store.sessions[key] = replace(record, owner="untrusted")
            if case == "corrupt_epoch":
                f.store.sessions[key] = replace(record, epoch=-1)
            if case == "corrupt_time":
                f.store.sessions[key] = replace(record, absolute=float("nan"))
            if case == "future_last_seen":
                f.store.sessions[key] = replace(record, last_seen=record.last_seen + 1)
            if case == "corrupt_tokens":
                f.store.sessions[key] = replace(record, tokens=())
            if case == "corrupt_key":
                f.store.sessions[key] = replace(record, key="0" * 64)
            if case == "duplicate_csrf":
                f.store.sessions[key] = replace(
                    record, tokens=tuple((a, record.tokens[0][1]) for a, _ in record.tokens)
                )
            # NaN does not compare equal to itself; compare the exact unchanged object maps.
            sessions, controls = dict(f.store.sessions), dict(f.store.controls)
            response = await c.get("/_session/me")
            assert response.status_code in {401, 503}
            assert response.json()["code"].startswith("SESSION_FIXTURE_")
            assert sessions == f.store.sessions and controls == f.store.controls

    asyncio.run(run())


def test_logout_all_revokes_only_owner_even_when_provider_fails() -> None:
    async def run() -> None:
        async with harness() as (f, c, _, _):
            ah = await login(f, c)
            async with AsyncClient(
                transport=f.transport, base_url=BFF, headers=ORIGIN, trust_env=False
            ) as second:
                second_a = await login(f, second)
                async with AsyncClient(
                    transport=f.transport, base_url=BFF, headers=ORIGIN, trust_env=False
                ) as b:
                    bh = await login(f, b, "fictional-b")
                    csrf = await token(c, "POST:/_session/logout-all")
                    assert f.oidc.issuer and f.store
                    f.oidc.issuer.key = None
                    response = await c.post(
                        "/_session/logout-all", json={}, headers={"x-csrf-token": csrf}
                    )
                    assert (
                        response.status_code == 200 and response.json()["upstream"] == "unverified"
                    )
                    for old in (ah, second_a):
                        with pytest.raises(Denied):
                            f.store.lookup(old)
                    assert f.store.lookup(bh)[1].owner == "fictional-b"
                    assert f.store.controls["fictional-a"].epoch == 1

    asyncio.run(run())


def test_cross_session_and_cross_action_csrf() -> None:
    async def run() -> None:
        async with harness() as (f, c, _, _):
            await login(f, c)
            csrf = await token(c)
            async with AsyncClient(
                transport=f.transport, base_url=BFF, headers=ORIGIN, trust_env=False
            ) as b:
                await login(f, b, "fictional-b")
                assert f.store
                snapshot = copy.deepcopy((f.store.sessions, f.store.controls))
                assert (
                    await b.post("/_session/marker", json={}, headers={"x-csrf-token": csrf})
                ).status_code == 403
                assert (
                    await c.post("/_session/logout", json={}, headers={"x-csrf-token": csrf})
                ).status_code == 403
                assert snapshot == (f.store.sessions, f.store.controls)

    asyncio.run(run())


def test_live_session_limits_cleanup_and_revocation_capacity() -> None:
    async def run() -> None:
        async with harness() as (f, c, clock, _):
            await login(f, c)
            assert f.store
            # Trusted setup reuses a validated pair, never HTTP identity input.
            identity = f.store.lookup(c.cookies[SESSION_COOKIE])[1].owner
            from experiments.oidc_protocol import Identity

            for _ in range(MAX_PER_OWNER - 1):
                await f.store.login(Identity(ISSUER, identity), f.store.epochs())
            snapshot = copy.deepcopy((f.store.sessions, f.store.controls))
            with pytest.raises(Denied):
                await f.store.login(Identity(ISSUER, identity), f.store.epochs())
            assert snapshot == (f.store.sessions, f.store.controls)
            csrf = await token(c, "POST:/_session/logout-all")
            assert (
                await c.post("/_session/logout-all", json={}, headers={"x-csrf-token": csrf})
            ).status_code == 200
            assert not f.store.sessions
            await login(f, c)
            clock.value += IDLE
            await f.store.cleanup()
            assert not f.store.sessions

    asyncio.run(run())


@pytest.mark.parametrize("stage", ["preauth", "attempt"])
def test_pending_limits_and_expiration(stage: str) -> None:
    async def run() -> None:
        async with harness() as (f, c, clock, _):
            for _ in range(MAX_PENDING):
                c.cookies.clear()
                response = (
                    await c.get("/_session/preauth") if stage == "preauth" else await pending(f, c)
                )
                assert response.status_code in {200, 303}
            c.cookies.clear()
            if stage == "preauth":
                response = await c.get("/_session/preauth")
            else:
                pre = await c.get("/_session/preauth")
                response = await c.post(
                    "/_spike/start", json={}, headers={"x-csrf-token": pre.json()["csrf"]}
                )
            assert response.status_code == 429
            clock.value += 300
            c.cookies.clear()
            assert (await pending(f, c)).status_code == 303
            assert len(f.attempts) <= MAX_PENDING and len(f.preauth) <= MAX_PENDING

    asyncio.run(run())


def test_default_fixture_normal_app_and_method_boundaries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOOTPRINT_SESSION_ENABLED", "true")
    f = create_session_fixture()
    assert f.store is None and f.events is None
    for target in (app, f.bff):
        with TestClient(target) as c:
            for path in (
                "/_session/me",
                "/_session/csrf",
                "/_session/preauth",
                "/_session/logout",
                "/_session/marker",
                "/_spike/start",
                "/auth/login",
                "/api/v2/me",
            ):
                assert c.get(path).status_code == 404
                assert c.post(path).status_code == 404
    assert set(app.openapi()["paths"]) == {"/api/v1/health", "/api/v1/demo"}


def test_no_network_no_sensitive_logs_or_token_cookie_payload(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)

    async def run() -> None:
        async with harness() as (f, c, _, _):

            def forbidden(*args: Any, **kwargs: Any) -> Any:
                raise AssertionError("Network prohibited")

            # Windows asyncio wakeup socket pair is initialized before the guard.
            monkeypatch.setattr(socket, "getaddrinfo", forbidden)
            monkeypatch.setattr(socket.socket, "connect", forbidden)
            handle = await login(f, c)
            csrf = await token(c)
            assert f.events and f.store
            event = f.events.sign("fictional-a", 1, "mfa_reset")
            response = await c.post("/_session/marker", json={}, headers={"x-csrf-token": csrf})
            assert response.status_code == 200
            assert set(c.cookies) == {SESSION_COOKIE}
            assert "." not in handle and len(base64.urlsafe_b64decode(handle + "=")) == 32
            await f.events.apply(event)
            error = await c.get("/_session/me")
            assert error.status_code == 401
            assert all(
                secret not in caplog.text + response.text + error.text
                for secret in (handle, csrf, event, "shared@identity.test")
            )
            assert response.request.url.query == b"" and error.request.url.query == b""
            with pytest.raises(Denied):
                await c.get(ISSUER + "/authorize")  # Host-only cookie must never reach mock issuer.

    asyncio.run(run())


@pytest.mark.parametrize(
    "path", ["/_spike/start", "/_session/step-up", "/_session/logout", "/_session/logout-all"]
)
def test_every_login_revocation_mutation_requires_its_csrf(path: str) -> None:
    async def run() -> None:
        async with harness() as (f, c, clock, _):
            await login(f, c)
            await c.get("/_session/preauth")
            assert f.store
            snapshot = copy.deepcopy((f.store.sessions, f.store.controls))
            clock.value += 1
            response = await c.post(
                path, json={}, headers={"x-csrf-token": secrets.token_urlsafe(32)}
            )
            assert response.status_code == 403
            assert snapshot == (f.store.sessions, f.store.controls)
            assert not f.attempts

    asyncio.run(run())


@pytest.mark.parametrize("all_sessions", [False, True])
def test_http_invalidation_failure_is_not_success(all_sessions: bool) -> None:
    async def run() -> None:
        async with harness() as (f, c, _, _):
            handle = await login(f, c)
            assert f.store
            action = "logout_all" if all_sessions else "logout"
            path = "/_session/" + ("logout-all" if all_sessions else "logout")
            csrf = await token(c, "POST:" + path)
            f.store.fail_on = action
            response = await c.post(path, json={}, headers={"x-csrf-token": csrf})
            assert response.status_code == 503 and "set-cookie" not in response.headers
            assert c.cookies[SESSION_COOKIE] == handle
            assert "complete" not in response.text
            f.store.fail_on = None
            assert (await c.get("/_session/me")).status_code == 401
            assert f.store.controls["fictional-a"].quarantined

    asyncio.run(run())


@pytest.mark.parametrize("failure", ["unavailable", "publish"])
def test_authenticated_event_failure_stays_denied_until_authenticated_retry(failure: str) -> None:
    async def run() -> None:
        async with harness() as (f, c, _, _):
            handle = await login(f, c)
            assert f.store and f.events
            encoded = f.events.sign("fictional-a", 1)
            if failure == "unavailable":
                f.store.available = False
            else:
                f.store.fail_on = "event"
            with pytest.raises(Denied):
                await f.events.apply(encoded)
            f.store.available, f.store.fail_on = True, None
            assert f.store.controls["fictional-a"].quarantined
            assert (await c.get("/_session/me")).status_code == 401
            await f.events.apply(encoded)
            assert not f.store.controls["fictional-a"].quarantined
            with pytest.raises(Denied):
                f.store.lookup(handle)
            assert f.store.controls["fictional-a"].epoch == 1

    asyncio.run(run())


def test_step_up_requires_same_validated_subject_and_preserves_old_on_rejection() -> None:
    async def run() -> None:
        async with harness() as (f, c, _, _):
            old = await login(f, c)
            csrf = await token(c, "POST:/_session/step-up")
            start = await c.post("/_session/step-up", json={}, headers={"x-csrf-token": csrf})
            assert f.oidc.issuer and f.store
            f.oidc.issuer.subject = "fictional-b"
            snapshot = copy.deepcopy((f.store.sessions, f.store.controls))
            response = await authorize(f, c, start)
            assert response.headers["location"] == "/_spike/rejected"
            assert snapshot == (f.store.sessions, f.store.controls)
            assert c.cookies[SESSION_COOKIE] == old and f.store.lookup(old)

    asyncio.run(run())


@pytest.mark.parametrize("case", ["step_up_failure", "login_failure"])
def test_oidc_session_publication_failure_does_not_leave_protocol_or_session(case: str) -> None:
    async def run() -> None:
        async with harness() as (f, c, _, _):
            await login(f, c)
            assert f.store and f.oidc.protocol
            csrf = await token(c, "POST:/_session/step-up")
            snapshot = copy.deepcopy((f.store.sessions, f.store.controls))
            if case == "step_up_failure":
                f.store.fail_on = "step_up"
            start = await c.post("/_session/step-up", json={}, headers={"x-csrf-token": csrf})
            if case == "step_up_failure":
                assert start.status_code == 503
                assert snapshot == (f.store.sessions, f.store.controls)
            else:
                snapshot = copy.deepcopy((f.store.sessions, f.store.controls))
                f.store.fail_on = "login"
                response = await authorize(f, c, start)
                assert response.headers["location"] == "/_spike/rejected"
                assert snapshot == (f.store.sessions, f.store.controls)
            assert not f.oidc.protocol.transactions and not f.attempts

    asyncio.run(run())


def test_no_persistent_file_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    async def run() -> None:
        async with harness() as (f, c, _, _):
            original = builtins.open

            def guarded(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
                assert not any(flag in mode for flag in "wax+"), "Persistent writes prohibited"
                return original(file, mode, *args, **kwargs)

            monkeypatch.setattr(builtins, "open", guarded)
            await login(f, c)
            csrf = await token(c)
            assert (
                await c.post("/_session/marker", json={}, headers={"x-csrf-token": csrf})
            ).status_code == 200
            assert f.events
            await f.events.apply(f.events.sign("fictional-a", 1))

    asyncio.run(run())


def test_get_and_cors_cannot_mutate_session_state() -> None:
    async def run() -> None:
        async with harness() as (f, c, _, _):
            await login(f, c)
            assert f.store
            snapshot = copy.deepcopy((f.store.sessions, f.store.controls))
            for path in (
                "/_session/logout",
                "/_session/logout-all",
                "/_session/step-up",
                "/_spike/start",
                "/_session/marker",
            ):
                assert (await c.get(path)).status_code == 405
                response = await c.options(
                    path,
                    headers={
                        "origin": "https://attacker.test",
                        "access-control-request-method": "POST",
                        "access-control-request-headers": "X-CSRF-Token",
                    },
                )
                assert (
                    response.status_code == 403
                    and "access-control-allow-credentials" not in response.headers
                )
            assert snapshot == (f.store.sessions, f.store.controls)

    asyncio.run(run())


def test_shutdown_discards_all_security_state() -> None:
    f = create_session_fixture(enabled=True)
    assert f.store and f.events and f.oidc.protocol
    with TestClient(f.bff, base_url=BFF, client=("127.0.0.1", 1), headers=ORIGIN) as client:
        pre = client.get("/_session/preauth")
        assert (
            client.post(
                "/_spike/start",
                json={},
                headers={"x-csrf-token": pre.json()["csrf"]},
                follow_redirects=False,
            ).status_code
            == 303
        )
        assert f.attempts and f.oidc.protocol.transactions
    assert not f.store.available and not f.store.sessions and not f.attempts and not f.preauth
    assert not f.oidc.protocol.transactions and f.events.key is None and f.events.public is None
