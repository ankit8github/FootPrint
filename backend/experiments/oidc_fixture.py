"""Explicitly activated ASGI-only issuer/BFF fixture. No module-level app or CLI."""

import asyncio
import secrets
import time
from collections import deque
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, urlencode

from authlib.oauth2.rfc7636 import create_s256_code_challenge  # type: ignore[import-untyped]
from fastapi import FastAPI, Request
from httpx2 import ASGITransport, AsyncBaseTransport, Response
from httpx2 import Request as HTTPRequest
from joserfc import jwt
from joserfc.jwk import RSAKey
from starlette.responses import JSONResponse, RedirectResponse

from experiments.oidc_protocol import (
    AUTHORIZE,
    BFF,
    CALLBACK,
    CLIENT_ID,
    COOKIE,
    DEADLINE,
    ISSUER,
    JWKS,
    MAX_RESPONSE,
    MAX_TRANSACTIONS,
    OPAQUE,
    TOKEN,
    Protocol,
    Rejected,
)


def parameters(raw: bytes) -> dict[str, str]:
    if len(raw) > 2048:
        raise Rejected()
    pairs = parse_qsl(raw.decode("ascii"), keep_blank_values=True, strict_parsing=True)
    if len(pairs) != len(dict(pairs)):
        raise Rejected()
    return dict(pairs)


class LoopbackTransport(AsyncBaseTransport):
    """No network fallback; erase query before HTTPX logs/retains handled URL."""

    def __init__(self, apps: dict[str, FastAPI]) -> None:
        self.apps = apps

    async def handle_async_request(self, request: HTTPRequest) -> Response:
        url = request.url
        origin = str(url.copy_with(path="/", query=None)).rstrip("/")
        try:
            if origin not in self.apps or url.username or url.password or url.fragment:
                raise Rejected()
            allowed = (
                {"/authorize", "/token", "/jwks"}
                if origin == ISSUER
                else {"/_spike/start", "/_spike/callback", "/_spike/complete", "/_spike/rejected"}
            )
            if url.path not in allowed:
                raise Rejected()
            response = await ASGITransport(app=self.apps[origin]).handle_async_request(request)
            await response.aread()
            if len(response.content) > MAX_RESPONSE:
                raise Rejected()
            return response
        finally:
            request.url = url.copy_with(query=None)


@dataclass(repr=False)
class Code:
    nonce: str
    challenge: str
    expires: float
    timer: asyncio.TimerHandle | None = None


class MockIssuer:
    def __init__(self, clock: Callable[[], float], wall_clock: Callable[[], float]) -> None:
        self.clock = clock
        self.wall_clock = wall_clock
        self.subject = "fictional-a"
        self.key: RSAKey | None = RSAKey.generate_key(2048, {"kid": "spike-key-1"})
        self.codes: dict[str, Code] = {}
        # Contains field names and paths only, never values or complete URLs.
        self.received: deque[tuple[str, frozenset[str]]] = deque(maxlen=128)

    def discard(self, code: str) -> Code | None:
        entry = self.codes.pop(code, None)
        if entry and entry.timer:
            entry.timer.cancel()
        return entry

    def clear(self) -> None:
        for code in list(self.codes):
            self.discard(code)
        self.received.clear()
        self.key = None

    def prune(self) -> None:
        for code, value in list(self.codes.items()):
            if self.clock() >= value.expires:
                self.discard(code)

    def authorize(self, params: dict[str, str]) -> str:
        self.prune()
        if set(params) != {
            "response_type",
            "client_id",
            "redirect_uri",
            "scope",
            "state",
            "nonce",
            "code_challenge",
            "code_challenge_method",
        }:
            raise Rejected()
        expected = {
            "response_type": "code",
            "client_id": CLIENT_ID,
            "redirect_uri": CALLBACK,
            "scope": "openid",
            "code_challenge_method": "S256",
        }
        if any(params[k] != v for k, v in expected.items()):
            raise Rejected()
        if not all(OPAQUE.fullmatch(params[k]) for k in ("state", "nonce", "code_challenge")):
            raise Rejected()
        if len(self.codes) >= MAX_TRANSACTIONS:
            raise Rejected()
        self.received.append(("/authorize", frozenset(params)))
        code = secrets.token_urlsafe(32)
        self.codes[code] = Code(params["nonce"], params["code_challenge"], self.clock() + DEADLINE)
        self.codes[code].timer = asyncio.get_running_loop().call_later(DEADLINE, self.discard, code)
        return CALLBACK + "?" + urlencode({"code": code, "state": params["state"], "iss": ISSUER})

    def exchange(self, params: dict[str, str]) -> dict[str, Any]:
        self.prune()
        code = self.discard(params.get("code", ""))
        if code is None or self.key is None:
            raise Rejected()
        if set(params) != {"grant_type", "code", "redirect_uri", "client_id", "code_verifier"}:
            raise Rejected()
        if (params["grant_type"], params["redirect_uri"], params["client_id"]) != (
            "authorization_code",
            CALLBACK,
            CLIENT_ID,
        ):
            raise Rejected()
        if not OPAQUE.fullmatch(params["code_verifier"]):
            raise Rejected()
        challenge = create_s256_code_challenge(params["code_verifier"])
        if not secrets.compare_digest(challenge, code.challenge):
            raise Rejected()
        self.received.append(("/token", frozenset(params)))
        now = int(self.wall_clock())
        claims = {
            "iss": ISSUER,
            "sub": self.subject,
            "aud": CLIENT_ID,
            "nonce": code.nonce,
            "iat": now,
            "nbf": now,
            "exp": now + 120,
            "email": "shared@identity.test",
        }
        encoded = jwt.encode({"alg": "RS256", "kid": "spike-key-1", "typ": "JWT"}, claims, self.key)
        return {
            "access_token": secrets.token_urlsafe(32),
            "token_type": "Bearer",
            "id_token": encoded,
            "expires_in": 120,
        }

    def jwks(self) -> dict[str, Any]:
        self.received.append(("/jwks", frozenset()))
        if self.key is None:
            raise Rejected()
        key = self.key.as_dict(private=False)
        return {
            "keys": [
                {**key, "kid": "spike-key-1", "alg": "RS256", "use": "sig", "key_ops": ["verify"]}
            ]
        }


@dataclass(repr=False)
class Fixture:
    bff: FastAPI
    issuer_app: FastAPI
    transport: LoopbackTransport
    protocol: Protocol | None = None
    issuer: MockIssuer | None = None

    def clear(self) -> None:
        if self.protocol:
            self.protocol.clear()
        if self.issuer:
            self.issuer.clear()


def create_fixture(
    *,
    enabled: bool = False,
    clock: Callable[[], float] = time.monotonic,
    wall_clock: Callable[[], float] = time.time,
) -> Fixture:
    """No env switch or normal-app registration can activate this fixture."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            fixture.clear()

    bff = FastAPI(openapi_url=None, docs_url=None, redoc_url=None, lifespan=lifespan)
    issuer_app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None, lifespan=lifespan)
    fixture = Fixture(bff, issuer_app, LoopbackTransport({BFF: bff, ISSUER: issuer_app}))
    if not enabled:
        return fixture
    issuer = MockIssuer(clock, wall_clock)
    protocol = Protocol(fixture.transport, clock=clock, wall_clock=wall_clock)
    fixture.protocol, fixture.issuer = protocol, issuer

    async def exchange_response(request: Request, call_next: Any) -> Any:
        # In-process transport asserts loopback too; no public serving entry point.
        origin = BFF if request.app is bff else ISSUER
        if (
            str(request.base_url).rstrip("/") != origin
            or request.client is None
            or request.client.host != "127.0.0.1"
        ):
            return JSONResponse({"code": "OIDC_SPIKE_REJECTED"}, status_code=400)
        try:
            response = await call_next(request)
        except Exception:
            response = JSONResponse({"code": "OIDC_SPIKE_REJECTED"}, status_code=400)
        response.headers.update(
            {
                "Cache-Control": "no-store",
                "Pragma": "no-cache",
                "Referrer-Policy": "no-referrer",
                "X-Content-Type-Options": "nosniff",
                "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
            }
        )
        return response

    bff.middleware("http")(exchange_response)
    issuer_app.middleware("http")(exchange_response)

    @bff.post("/_spike/start")
    async def start(request: Request) -> Any:
        if request.url.query:
            raise Rejected()
        async for part in request.stream():
            if part:
                raise Rejected()
        # Cancel previous attempt, never promote this cookie to an auth session.
        protocol.discard(request.cookies.get(COOKIE, ""))
        url, binding = await protocol.begin()
        response = RedirectResponse(url, status_code=303)
        response.set_cookie(
            COOKIE, binding, max_age=DEADLINE, secure=True, httponly=True, samesite="lax", path="/"
        )
        return response

    @bff.get("/_spike/callback")
    async def callback(request: Request) -> Any:
        binding = request.cookies.get(COOKIE, "")
        try:
            if request.scope["raw_path"] != b"/_spike/callback":
                raise Rejected()
            params = parameters(request.scope["query_string"])
            request.scope["query_string"] = b""
            await protocol.finish(binding, params)  # No session/account/result retained.
            target = "/_spike/complete"
        except Exception:
            protocol.discard(binding)
            target = "/_spike/rejected"
        finally:
            request.scope["query_string"] = b""
        response = RedirectResponse(target, status_code=303)
        response.delete_cookie(COOKIE, secure=True, httponly=True, samesite="lax", path="/")
        return response

    @bff.get("/_spike/complete")
    @bff.get("/_spike/rejected")
    async def completed() -> Any:
        return JSONResponse({"mode": "fictional_protocol_only"})

    @issuer_app.get("/authorize")
    async def authorize(request: Request) -> Any:
        try:
            return RedirectResponse(
                issuer.authorize(parameters(request.scope["query_string"])), status_code=303
            )
        finally:
            request.scope["query_string"] = b""

    @issuer_app.post("/token")
    async def token(request: Request) -> Any:
        if request.url.query or request.headers.get("content-type") not in {
            "application/x-www-form-urlencoded",
            "application/x-www-form-urlencoded;charset=UTF-8",
        }:
            raise Rejected()
        raw = b""
        async for part in request.stream():
            raw += part
            if len(raw) > 2048:
                raise Rejected()
        return JSONResponse(issuer.exchange(parameters(raw)))

    @issuer_app.get("/jwks")
    async def keys(request: Request) -> Any:
        if request.url.query or request.headers.get("authorization"):
            raise Rejected()
        return JSONResponse(issuer.jwks())

    # Check constants without accepting discovery/configuration from a caller.
    assert AUTHORIZE == ISSUER + "/authorize" and TOKEN == ISSUER + "/token"
    assert JWKS == ISSUER + "/jwks"
    return fixture
