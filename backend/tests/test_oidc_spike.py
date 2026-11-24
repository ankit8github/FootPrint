"""Local ASGI fixtures only. No actual identity provider or network sockets."""

import asyncio
import base64
import builtins
import json
import logging
import secrets
import socket
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit

import pytest
from fastapi.testclient import TestClient
from httpx2 import ASGITransport, AsyncBaseTransport, AsyncClient, Request, Response
from joserfc import jws, jwt
from joserfc.jwk import RSAKey

from app.main import app
from experiments.oidc_fixture import Fixture, create_fixture
from experiments.oidc_protocol import (
    AUTHORIZE,
    BFF,
    CALLBACK,
    CLIENT_ID,
    COOKIE,
    DEADLINE,
    ISSUER,
    MAX_TRANSACTIONS,
    TOKEN,
    Identity,
    Rejected,
)


@asynccontextmanager
async def harness(
    clock: Callable[[], float] = time.monotonic,
) -> AsyncIterator[tuple[Fixture, AsyncClient]]:
    fixture = create_fixture(enabled=True, clock=clock)
    try:
        async with AsyncClient(
            transport=fixture.transport, base_url=BFF, follow_redirects=False, trust_env=False
        ) as client:
            yield fixture, client
    finally:
        fixture.clear()


async def pending(client: AsyncClient) -> tuple[str, dict[str, str]]:
    start = await client.post("/_spike/start")
    assert start.status_code == 303
    authorize = await client.get(start.headers["location"])
    assert authorize.status_code == 303
    location = authorize.headers["location"]
    return location, dict(parse_qsl(urlsplit(location).query))


def test_positive_exchange_and_clean_completion() -> None:
    async def scenario() -> None:
        async with harness() as (fixture, client):
            location, _ = await pending(client)
            response = await client.get(location)
            assert response.status_code == 303
            assert response.headers["location"] == "/_spike/complete"
            assert response.request.url.query == b""
            assert response.headers["cache-control"] == "no-store"
            assert response.headers["referrer-policy"] == "no-referrer"
            assert COOKIE not in client.cookies
            assert fixture.protocol and not fixture.protocol.transactions
            assert fixture.issuer and not fixture.issuer.codes

    asyncio.run(scenario())


def test_equal_email_never_links_distinct_subjects() -> None:
    async def scenario() -> None:
        async with harness() as (fixture, client):
            assert fixture.issuer and fixture.protocol
            identities = []
            for subject in ("fictional-a", "fictional-b"):
                fixture.issuer.subject = subject
                _, params = await pending(client)
                identity = await fixture.protocol.finish(client.cookies[COOKIE], params)
                identities.append(identity)
            assert identities == [Identity(ISSUER, "fictional-a"), Identity(ISSUER, "fictional-b")]
            assert identities[0] != identities[1]
            assert not fixture.protocol.transactions and not fixture.issuer.codes

    asyncio.run(scenario())


def resign(
    fixture: Fixture,
    result: dict[str, Any],
    change: Callable[[dict[str, Any]], None],
    *,
    header: dict[str, Any] | None = None,
    wrong_key: bool = False,
) -> dict[str, Any]:
    assert fixture.issuer and fixture.issuer.key
    claims = jwt.decode(result["id_token"], fixture.issuer.key, algorithms=["RS256"]).claims
    change(claims)
    key = RSAKey.generate_key(2048) if wrong_key else fixture.issuer.key
    result["id_token"] = jwt.encode(
        header or {"alg": "RS256", "kid": "spike-key-1", "typ": "JWT"},
        claims,
        key,
        algorithms=["RS256", "RS512"],
    )
    return result


async def expect_rejected(client: AsyncClient, location: str) -> None:
    response = await client.get(location)
    assert response.status_code == 303
    assert response.headers["location"] == "/_spike/rejected"
    assert response.request.url.query == b""
    assert response.content == b"" and COOKIE not in client.cookies


@pytest.mark.parametrize(
    "case",
    [
        "issuer",
        "issuer_list",
        "audience",
        "audience_list",
        "client_id",
        "nonce",
        "missing_nonce",
        "nonce_list",
        "expired",
        "expiry_boundary",
        "future_iat",
        "future_nbf",
        "missing_exp",
        "bool_time",
        "string_time",
        "long_lifetime",
        "reverse_time",
        "subject",
        "signature",
        "algorithm",
        "kid",
        "header_url",
        "extra_claim",
    ],
)
def test_invalid_signed_tokens_fail_closed(case: str, monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        async with harness() as (fixture, client):
            assert fixture.issuer
            original = fixture.issuer.exchange
            issued: list[bool] = []

            def changed(params: dict[str, str]) -> dict[str, Any]:
                result = original(params)

                def mutate(claims: dict[str, Any]) -> None:
                    values: dict[str, tuple[str, Any]] = {
                        "issuer": ("iss", "https://attacker.test"),
                        "issuer_list": ("iss", [ISSUER]),
                        "audience": ("aud", "wrong-client"),
                        "audience_list": ("aud", [CLIENT_ID]),
                        "client_id": ("azp", "wrong-client"),
                        "nonce": ("nonce", "wrong-nonce"),
                        "nonce_list": ("nonce", [claims["nonce"]]),
                        "expired": ("exp", int(time.time()) - 1),
                        "expiry_boundary": ("exp", int(time.time())),
                        "future_iat": ("iat", int(time.time()) + 60),
                        "future_nbf": ("nbf", int(time.time()) + 60),
                        "bool_time": ("iat", True),
                        "string_time": ("nbf", "invalid"),
                        "long_lifetime": ("exp", int(time.time()) + DEADLINE + 100),
                        "reverse_time": ("exp", claims["iat"] - 1),
                        "subject": ("sub", "real-user"),
                        "extra_claim": ("raw_footprint", "SYNTHETIC_PRIVATE_CLAIM"),
                    }
                    if case in values:
                        name, value = values[case]
                        claims[name] = value
                    if case in {"missing_nonce", "missing_exp"}:
                        claims.pop(case.removeprefix("missing_"))

                header = {"alg": "RS256", "kid": "spike-key-1", "typ": "JWT"}
                if case == "algorithm":
                    header["alg"] = "RS512"
                if case == "kid":
                    header["kid"] = "unknown-key"
                if case == "header_url":
                    header["jku"] = "https://attacker.test/keys"
                encoded = resign(
                    fixture, result, mutate, header=header, wrong_key=case == "signature"
                )
                issued.append(True)
                return encoded

            monkeypatch.setattr(fixture.issuer, "exchange", changed)
            location, _ = await pending(client)
            await expect_rejected(client, location)
            assert issued == [True]
            assert fixture.protocol and not fixture.protocol.transactions
            assert not fixture.issuer.codes

    asyncio.run(scenario())


def test_alg_none_and_unsigned_token_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        async with harness() as (fixture, client):
            assert fixture.issuer
            original = fixture.issuer.exchange

            def unsigned(params: dict[str, str]) -> dict[str, Any]:
                result = original(params)
                _, payload, _ = result["id_token"].split(".")
                # Malicious input construction, not signing/authentication cryptography.
                header = (
                    base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').decode().rstrip("=")
                )
                result["id_token"] = header + "." + payload + "."
                return result

            monkeypatch.setattr(fixture.issuer, "exchange", unsigned)
            location, _ = await pending(client)
            await expect_rejected(client, location)

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "case", ["state", "issuer", "code", "extra", "duplicate", "provider_error"]
)
def test_callback_manipulation_consumes_transaction(case: str) -> None:
    async def scenario() -> None:
        async with harness() as (fixture, client):
            location, params = await pending(client)
            original_binding = client.cookies[COOKIE]
            if case in {"state", "code"}:
                params[case] = secrets.token_urlsafe(32)
            if case == "issuer":
                params["iss"] = "https://attacker.test"
            if case == "extra":
                params["redirect_uri"] = "https://attacker.test"
            if case == "provider_error":
                params = {"error": "SYNTHETIC_PROVIDER_SECRET", "state": params["state"]}
            altered = CALLBACK + "?" + urlencode(params)
            if case == "duplicate":
                altered += "&state=" + params["state"]
            await expect_rejected(client, altered)
            assert fixture.protocol and not fixture.protocol.transactions
            client.cookies.set(COOKIE, original_binding, domain="127.0.0.1", path="/")
            await expect_rejected(client, location)

    asyncio.run(scenario())


def test_browser_binding_replay_and_concurrent_callback() -> None:
    async def scenario() -> None:
        async with harness() as (fixture, client):
            location, params = await pending(client)
            assert fixture.protocol
            binding = client.cookies[COOKIE]
            with pytest.raises(Rejected, match="^OIDC_SPIKE_REJECTED$"):
                await fixture.protocol.finish(secrets.token_urlsafe(32), params)
            results = await asyncio.gather(
                fixture.protocol.finish(binding, params),
                fixture.protocol.finish(binding, params),
                return_exceptions=True,
            )
            assert sum(isinstance(r, Identity) for r in results) == 1
            assert sum(isinstance(r, Rejected) for r in results) == 1
            await expect_rejected(client, location)

    asyncio.run(scenario())


@dataclass
class Clock:
    value: float = 1000

    def __call__(self) -> float:
        return self.value


@pytest.mark.parametrize("delta", [299, 300, 301])
def test_transaction_deadline_boundary(delta: int) -> None:
    async def scenario() -> None:
        clock = Clock()
        async with harness(clock) as (fixture, client):
            location, _ = await pending(client)
            clock.value += delta
            response = await client.get(location)
            assert response.headers["location"] == (
                "/_spike/complete" if delta < DEADLINE else "/_spike/rejected"
            )
            assert fixture.protocol and not fixture.protocol.transactions

    asyncio.run(scenario())


def test_deadline_rechecked_after_exchange(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        clock = Clock()
        async with harness(clock) as (fixture, client):
            assert fixture.issuer
            original = fixture.issuer.exchange

            def delayed(params: dict[str, str]) -> dict[str, Any]:
                result = original(params)
                clock.value += DEADLINE
                return result

            monkeypatch.setattr(fixture.issuer, "exchange", delayed)
            location, _ = await pending(client)
            await expect_rejected(client, location)

    asyncio.run(scenario())


@pytest.mark.parametrize("case", ["pkce", "code_reuse", "redirect", "client_id"])
def test_code_exchange_rejects_bad_binding(case: str) -> None:
    async def scenario() -> None:
        async with harness() as (fixture, client):
            assert fixture.protocol and fixture.issuer
            location, params = await pending(client)
            tx = fixture.protocol.transactions[client.cookies[COOKIE]]
            data = {
                "grant_type": "authorization_code",
                "code": params["code"],
                "redirect_uri": CALLBACK,
                "client_id": CLIENT_ID,
                "code_verifier": tx.verifier,
            }
            if case == "pkce":
                data["code_verifier"] = secrets.token_urlsafe(48)
            if case == "redirect":
                data["redirect_uri"] = CALLBACK + "/"
            if case == "client_id":
                data["client_id"] = "wrong-client"
            response = await client.post(TOKEN, data=data)
            assert response.status_code == (200 if case == "code_reuse" else 400)
            if case == "code_reuse":
                assert (await client.post(TOKEN, data=data)).status_code == 400
            await expect_rejected(client, location)
            assert not fixture.issuer.codes

    asyncio.run(scenario())


@pytest.mark.parametrize("case", ["redirect", "client_id", "scope", "pkce_method", "discovery"])
def test_authorize_rejects_unregistered_parameters(case: str) -> None:
    async def scenario() -> None:
        async with harness() as (_, client):
            response = await client.post("/_spike/start")
            params = dict(parse_qsl(urlsplit(response.headers["location"]).query))
            field, value = {
                "redirect": ("redirect_uri", CALLBACK + "?next=https://attacker.test"),
                "client_id": ("client_id", "wrong-client"),
                "scope": ("scope", "openid email"),
                "pkce_method": ("code_challenge_method", "plain"),
                "discovery": ("issuer", "https://attacker.test/.well-known/openid-configuration"),
            }[case]
            params[field] = value
            result = await client.get(AUTHORIZE, params=params)
            assert result.status_code == 400
            assert result.json() == {"code": "OIDC_SPIKE_REJECTED"}
            assert "location" not in result.headers

    asyncio.run(scenario())


class FaultTransport(AsyncBaseTransport):
    def __init__(self, delegate: AsyncBaseTransport, target: str, fault: str) -> None:
        self.delegate, self.target, self.fault = delegate, target, fault
        self.paths: list[str] = []

    async def handle_async_request(self, request: Request) -> Response:
        self.paths.append(request.url.path)
        if request.url.path != self.target:
            return await self.delegate.handle_async_request(request)
        if self.fault == "unavailable":
            raise RuntimeError("SYNTHETIC_PROVIDER_SECRET")
        if self.fault == "timeout":
            await asyncio.sleep(0.1)
        if self.fault == "redirect":
            return Response(302, headers={"location": "https://attacker.test/secrets"})
        if self.fault == "malformed":
            return Response(200, content=b'{"keys":', headers={"content-type": "application/json"})
        if self.fault == "duplicate":
            return Response(
                200, content=b'{"keys":[],"keys":[]}', headers={"content-type": "application/json"}
            )
        if self.fault == "oversized":
            return Response(200, content=b" " * 16385, headers={"content-type": "application/json"})
        return await self.delegate.handle_async_request(request)


@pytest.mark.parametrize("target", ["/token", "/jwks"])
@pytest.mark.parametrize(
    "fault", ["unavailable", "timeout", "redirect", "malformed", "duplicate", "oversized"]
)
def test_provider_failures_fail_closed(
    target: str,
    fault: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        async with harness() as (fixture, client):
            assert fixture.protocol
            transport = FaultTransport(fixture.transport, target, fault)
            fixture.protocol.transport = transport
            if fault == "timeout":
                monkeypatch.setattr("experiments.oidc_protocol.EXCHANGE_TIMEOUT", 0.01)
            location, _ = await pending(client)
            await expect_rejected(client, location)
            assert set(transport.paths) <= {"/token", "/jwks"}
            assert not fixture.protocol.transactions

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "fault", ["empty", "multiple", "private", "size", "use", "ops", "alg", "kid", "exponent"]
)
def test_jwks_validation(fault: str, monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        async with harness() as (fixture, client):
            assert fixture.issuer
            original = fixture.issuer.jwks

            def changed() -> dict[str, Any]:
                data = original()
                if fault == "empty":
                    return {"keys": []}
                if fault == "multiple":
                    return {"keys": data["keys"] * 2}
                key = data["keys"][0]
                if fault == "size":
                    key.update(RSAKey.generate_key(3072).as_dict(private=False))
                else:
                    name, value = {
                        "private": ("d", "not-public"),
                        "use": ("use", "enc"),
                        "ops": ("key_ops", ["sign"]),
                        "alg": ("alg", "HS256"),
                        "kid": ("kid", "other"),
                        "exponent": ("e", "AA"),
                    }[fault]
                    key[name] = value
                return data

            monkeypatch.setattr(fixture.issuer, "jwks", changed)
            location, _ = await pending(client)
            await expect_rejected(client, location)

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "url",
    [
        "https://attacker.test/token",
        ISSUER + "/.well-known/openid-configuration",
        "http://127.0.0.1:9443/token",
        "https://localhost:9443/token",
        "https://127.0.0.1:9443@attacker.test/token",
        ISSUER + "/jwks#ignored",
    ],
)
def test_transport_has_no_dynamic_network_target(url: str) -> None:
    async def scenario() -> None:
        async with harness() as (_, client):
            with pytest.raises(Rejected, match="^OIDC_SPIKE_REJECTED$"):
                await client.get(url)

    asyncio.run(scenario())


def test_default_disabled_and_normal_app_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOOTPRINT_OIDC_ENABLED", "true")
    fixture = create_fixture()
    assert fixture.protocol is None and fixture.issuer is None
    for target in (app, fixture.bff, fixture.issuer_app):
        with TestClient(target) as client:
            for path in (
                "/auth/login",
                "/auth/callback",
                "/_spike/start",
                "/_spike/callback",
                "/authorize",
                "/token",
                "/jwks",
                "/.well-known/openid-configuration",
            ):
                assert client.get(path).status_code == 404
                assert client.post(path).status_code == 404
    assert set(app.openapi()["paths"]) == {"/api/v1/health", "/api/v1/demo"}


def test_no_network_no_logs_no_footprint_or_session(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Network access prohibited")

    caplog.set_level(logging.DEBUG)

    async def scenario() -> None:
        # Install after asyncio creates its Windows wakeup socket pair.
        monkeypatch.setattr(socket, "getaddrinfo", forbidden)
        monkeypatch.setattr(socket.socket, "connect", forbidden)
        async with harness() as (fixture, client):
            assert fixture.protocol and fixture.issuer
            start = await client.post(
                "/_spike/start", json={"footprint": "SYNTHETIC_FOOTPRINT_SECRET"}
            )
            assert start.status_code == 400 and not fixture.issuer.received
            location, params = await pending(client)
            binding = client.cookies[COOKIE]
            tx = fixture.protocol.transactions[binding]
            sensitive = [
                binding,
                params["code"],
                tx.state,
                tx.nonce,
                tx.verifier,
                "shared@identity.test",
                "SYNTHETIC_FOOTPRINT_SECRET",
            ]
            original_exchange = fixture.issuer.exchange

            def observed(params: dict[str, str]) -> dict[str, Any]:
                result = original_exchange(params)
                sensitive.extend([result["id_token"], result["access_token"]])
                return result

            monkeypatch.setattr(fixture.issuer, "exchange", observed)
            original_open = builtins.open

            def safe_open(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
                assert not any(flag in mode for flag in "wax+"), "Persistent write prohibited"
                return original_open(file, mode, *args, **kwargs)

            monkeypatch.setattr(builtins, "open", safe_open)
            response = await client.get(location)
            assert response.headers["location"] == "/_spike/complete"
            completed = await client.get(response.headers["location"])
            assert completed.json() == {"mode": "fictional_protocol_only"}
            assert (
                not client.cookies
                and not fixture.protocol.transactions
                and not fixture.issuer.codes
            )
            assert set(fixture.issuer.received) == {
                (
                    "/authorize",
                    frozenset(
                        {
                            "response_type",
                            "client_id",
                            "redirect_uri",
                            "scope",
                            "state",
                            "nonce",
                            "code_challenge",
                            "code_challenge_method",
                        }
                    ),
                ),
                (
                    "/token",
                    frozenset({"grant_type", "code", "redirect_uri", "client_id", "code_verifier"}),
                ),
                ("/jwks", frozenset()),
            }
            assert all(
                value not in caplog.text + response.text + completed.text for value in sensitive
            )
            assert response.request.url.query == b"" and completed.request.url.query == b""
            assert "set-cookie" not in completed.headers

    asyncio.run(scenario())


def test_transaction_cookie_randomness_capacity_expiry_and_shutdown() -> None:
    async def scenario() -> None:
        clock = Clock()
        async with harness(clock) as (fixture, client):
            assert fixture.protocol and fixture.issuer
            first = await client.post("/_spike/start")
            flags = first.headers["set-cookie"]
            assert all(
                flag in flags
                for flag in ("HttpOnly", "Secure", "SameSite=lax", "Path=/", "Max-Age=300")
            )
            assert "Domain=" not in flags
            old_binding = client.cookies[COOKIE]
            await client.post("/_spike/start")
            assert old_binding not in fixture.protocol.transactions
            fixture.protocol.clear()
            values: set[str] = set()
            for _ in range(MAX_TRANSACTIONS):
                _, binding = await fixture.protocol.begin()
                tx = fixture.protocol.transactions[binding]
                assert not values.intersection({binding, tx.state, tx.nonce, tx.verifier})
                values.update({binding, tx.state, tx.nonce, tx.verifier})
            with pytest.raises(Rejected):
                await fixture.protocol.begin()
            clock.value += DEADLINE
            await fixture.protocol.begin()
            assert len(fixture.protocol.transactions) == 1
            fixture.clear()
            assert not fixture.protocol.transactions and not fixture.issuer.codes
            assert fixture.issuer.key is None

    asyncio.run(scenario())


def test_nonloopback_fixture_client_rejected() -> None:
    async def scenario() -> None:
        fixture = create_fixture(enabled=True)
        try:
            async with AsyncClient(
                transport=ASGITransport(app=fixture.bff, client=("192.0.2.1", 1)), base_url=BFF
            ) as client:
                assert (await client.post("/_spike/start")).status_code == 400
        finally:
            fixture.clear()

    asyncio.run(scenario())


@pytest.mark.parametrize("case", ["duplicate_claim", "invalid_token", "invalid_grant"])
def test_sensitive_provider_errors_never_leak(
    case: str,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)

    async def scenario() -> None:
        async with harness() as (fixture, client):
            assert fixture.issuer and fixture.issuer.key
            original = fixture.issuer.exchange
            secret = "SYNTHETIC_TOKEN_ERROR_SECRET"
            emitted: list[bool] = []

            def corrupt(params: dict[str, str]) -> dict[str, Any]:
                result = original(params)
                if case == "invalid_grant":
                    emitted.append(True)
                    return {"error": "invalid_grant", "error_description": secret}
                if case == "invalid_token":
                    result["id_token"] = secret
                else:
                    assert fixture.issuer and fixture.issuer.key
                    claims = jwt.decode(result["id_token"], fixture.issuer.key).claims
                    payload = json.dumps(claims)[:-1] + ',"sub":"' + secret + '"}'
                    result["id_token"] = jws.serialize_compact(
                        {"alg": "RS256", "kid": "spike-key-1", "typ": "JWT"},
                        payload,
                        fixture.issuer.key,
                        algorithms=["RS256"],
                    )
                emitted.append(True)
                return result

            monkeypatch.setattr(fixture.issuer, "exchange", corrupt)
            location, params = await pending(client)
            binding = client.cookies[COOKIE]
            response = await client.get(location)
            assert response.headers["location"] == "/_spike/rejected"
            assert emitted == [True]
            assert not response.content and COOKIE not in client.cookies
            assert all(
                value not in caplog.text + str(response.headers) + response.text
                for value in (secret, binding, params["code"], params["state"])
            )
            assert fixture.protocol and not fixture.protocol.transactions

    asyncio.run(scenario())


def test_ephemeral_clients_tokens_and_timer_cleanup(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        async with harness() as (fixture, client):
            assert fixture.protocol
            instances: list[Any] = []
            original = fixture.protocol._client

            def record() -> Any:
                instance = original()
                instances.append(instance)
                return instance

            monkeypatch.setattr(fixture.protocol, "_client", record)
            location, _ = await pending(client)
            tx = fixture.protocol.transactions[client.cookies[COOKIE]]
            assert tx.timer and not tx.timer.cancelled()
            response = await client.get(location)
            assert response.headers["location"] == "/_spike/complete"
            assert tx.timer.cancelled()
            assert all(instance.is_closed and not instance.token for instance in instances)

    asyncio.run(scenario())


def test_fixture_lifespan_discards_unfinished_state() -> None:
    fixture = create_fixture(enabled=True)
    assert fixture.protocol and fixture.issuer
    with TestClient(fixture.bff, base_url=BFF, client=("127.0.0.1", 1)) as client:
        assert client.post("/_spike/start", follow_redirects=False).status_code == 303
        assert fixture.protocol.transactions
    assert not fixture.protocol.transactions and not fixture.issuer.codes
    assert fixture.issuer.key is None


@pytest.mark.parametrize("path", ["/_spike/%63allback", "/_spike/call%62ack"])
def test_encoded_callback_alias_is_not_registered(path: str) -> None:
    async def scenario() -> None:
        async with harness() as (fixture, client):
            location, _ = await pending(client)
            altered = BFF + path + "?" + urlsplit(location).query
            await expect_rejected(client, altered)
            assert fixture.protocol and not fixture.protocol.transactions

    asyncio.run(scenario())
