"""Explicitly activated fictional ASGI sessions; no serving entry point."""

import asyncio
import secrets
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Request
from httpx2 import ASGITransport, AsyncBaseTransport, Response
from httpx2 import Request as HTTPRequest
from starlette.responses import JSONResponse, RedirectResponse

from experiments.oidc_fixture import Fixture, create_fixture, parameters
from experiments.oidc_protocol import BFF, COOKIE, DEADLINE, ISSUER, Protocol, strict_json
from experiments.session_events import FictionalEvents
from experiments.session_store import (
    ACTIONS,
    HANDLE,
    Denied,
    Previous,
    SessionStore,
    Unavailable,
    digest,
    random_value,
)

SESSION_COOKIE = "__Host-fp_session"
PREAUTH_COOKIE = "__Host-fp_preauth"
MAX_PENDING = 16
PATHS = {
    "/_spike/start",
    "/_spike/callback",
    "/_spike/complete",
    "/_spike/rejected",
    "/_session/preauth",
    "/_session/csrf",
    "/_session/me",
    "/_session/marker",
    "/_session/logout",
    "/_session/logout-all",
    "/_session/step-up",
}
HEADERS = {
    "Cache-Control": "no-store",
    "Pragma": "no-cache",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}


class SessionTransport(AsyncBaseTransport):
    def __init__(self, bff: FastAPI, oidc: Fixture) -> None:
        self.bff, self.oidc = bff, oidc

    async def handle_async_request(self, request: HTTPRequest) -> Response:
        url = request.url
        try:
            origin = str(url.copy_with(path="/", query=None)).rstrip("/")
            if url.username or url.password or url.fragment:
                raise Denied(400)
            if origin == ISSUER:
                if "cookie" in request.headers:
                    raise Denied(400)
                return await self.oidc.transport.handle_async_request(request)
            if origin != BFF or url.path not in PATHS:
                raise Denied(400)
            response = await ASGITransport(app=self.bff).handle_async_request(request)
            await response.aread()
            return response
        finally:
            request.url = url.copy_with(query=None)


@dataclass(frozen=True, repr=False)
class Preauth:
    csrf: str
    expires: float


@dataclass(frozen=True, repr=False)
class Attempt:
    epochs: dict[str, int]
    previous: Previous | None
    step_up: bool
    expires: float


@dataclass(repr=False)
class SessionFixture:
    bff: FastAPI
    oidc: Fixture
    transport: SessionTransport
    store: SessionStore | None
    events: FictionalEvents | None
    preauth: dict[str, Preauth]
    attempts: dict[str, Attempt]

    def clear(self) -> None:
        self.preauth.clear()
        self.attempts.clear()
        self.oidc.clear()
        if self.store:
            self.store.clear()
        if self.events:
            self.events.clear()


def cookies(request: Request) -> dict[str, str]:
    raw = request.headers.getlist("cookie")
    if len(raw) > 1 or (raw and len(raw[0]) > 1024):
        raise Denied(400)
    found: dict[str, str] = {}
    for part in raw[0].split(";") if raw else []:
        key, separator, value = part.strip().partition("=")
        if key in {SESSION_COOKIE, PREAUTH_COOKIE, COOKIE}:
            if not separator or key in found:
                raise Denied(400)
            digest(value)  # Canonical opaque syntax; no values in errors.
            found[key] = value
    return found


def same_origin(request: Request) -> None:
    expected = {
        "origin": BFF,
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
    }
    if any(request.headers.getlist(k) != [v] for k, v in expected.items()):
        raise Denied(403)
    if any(
        k in request.headers
        for k in (
            "x-http-method-override",
            "x-method-override",
            "x-user-id",
            "forwarded",
            "x-forwarded-host",
        )
    ):
        raise Denied(403)


async def empty_json(request: Request) -> None:
    if request.headers.getlist("content-type") not in [
        ["application/json"],
        ["application/json; charset=utf-8"],
    ]:
        raise Denied(415)
    raw = b""
    async for part in request.stream():
        raw += part
        if len(raw) > 64:
            raise Denied(413)
    try:
        if strict_json(raw) != {}:
            raise Denied(422)
    except Exception:
        raise Denied(422) from None


def delete_cookie(response: Any, name: str) -> None:
    response.delete_cookie(name, secure=True, httponly=True, samesite="lax", path="/")


def create_session_fixture(
    *,
    enabled: bool = False,
    clock: Callable[[], float] = time.monotonic,
    wall_clock: Callable[[], float] = time.time,
) -> SessionFixture:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            fixture.clear()

    bff = FastAPI(openapi_url=None, docs_url=None, redoc_url=None, lifespan=lifespan)
    oidc = create_fixture(enabled=enabled, clock=clock, wall_clock=wall_clock)
    store = SessionStore(clock) if enabled else None
    events = FictionalEvents(store, wall_clock) if store else None
    fixture = SessionFixture(bff, oidc, SessionTransport(bff, oidc), store, events, {}, {})
    if not enabled:
        return fixture
    assert store is not None and oidc.protocol is not None
    service: SessionStore = store
    protocol: Protocol = oidc.protocol

    def prune() -> None:
        now = clock()
        for key, pre in list(fixture.preauth.items()):
            if now >= pre.expires:
                fixture.preauth.pop(key)
        for key, attempt in list(fixture.attempts.items()):
            if now >= attempt.expires:
                fixture.attempts.pop(key)

    @bff.middleware("http")
    async def security(request: Request, call_next: Any) -> Any:
        try:
            if (
                str(request.base_url).rstrip("/") != BFF
                or request.headers.getlist("host") != ["127.0.0.1:9444"]
                or any(k.startswith("x-forwarded-") for k in request.headers)
                or request.client is None
                or request.client.host != "127.0.0.1"
                or request.scope["raw_path"] != request.url.path.encode("ascii")
            ):
                raise Denied(400)
            if request.url.path != "/_spike/callback":
                if request.url.query:
                    raise Denied(400)
                same_origin(request)
                if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
                    if len(request.headers.getlist("x-csrf-token")) != 1:
                        raise Denied(403)
                    await empty_json(request)
            cookies(request)
            response = await call_next(request)
        except Denied as error:
            response = JSONResponse({"code": "SESSION_FIXTURE_REJECTED"}, status_code=error.status)
        except Exception:
            response = JSONResponse({"code": "SESSION_FIXTURE_UNAVAILABLE"}, status_code=503)
        response.headers.update(HEADERS)
        return response

    @bff.get("/_session/preauth")
    async def preauth(request: Request) -> Any:
        service.healthy()
        # Bootstrap security material only, never an authenticated session.
        active = {k: v for k, v in fixture.preauth.items() if clock() < v.expires}
        old = cookies(request).get(PREAUTH_COOKIE)
        if old:
            active.pop(digest(old), None)
        if len(active) >= MAX_PENDING:
            raise Denied(429)
        binding, token = random_value(), random_value()
        active[digest(binding)] = Preauth(token, clock() + DEADLINE)
        fixture.preauth = active
        response = JSONResponse({"csrf": token})
        response.set_cookie(
            PREAUTH_COOKIE,
            binding,
            max_age=DEADLINE,
            secure=True,
            httponly=True,
            samesite="lax",
            path="/",
        )
        return response

    async def begin(request: Request, step_up: bool) -> Any:
        service.healthy()
        supplied = cookies(request)
        token = request.headers.get("x-csrf-token", "")
        previous = None
        old_handle = supplied.get(SESSION_COOKIE)
        if step_up or old_handle:
            try:
                key, record = service.lookup(old_handle or "")
                previous = Previous(key, record.owner)
            except Unavailable:
                raise
            except Denied:
                if step_up:
                    raise
                # Unknown/expired fixation cookie has no authority in a fresh login.
        async with preauth_lock:
            async with service.fence.many(
                {previous.owner} if step_up and previous else set(), "step_up"
            ):
                if step_up:
                    assert previous is not None
                    record = service.by_key(previous.key)
                    service.csrf(record, "POST:/_session/step-up", token)
                else:
                    if PREAUTH_COOKIE not in supplied:
                        raise Denied(403)
                    pre = fixture.preauth.get(digest(supplied[PREAUTH_COOKIE]))
                    if pre is None or clock() >= pre.expires or not secrets_equal(pre.csrf, token):
                        raise Denied(403)
                epochs = service.epochs()
                if (
                    len([a for a in fixture.attempts.values() if clock() < a.expires])
                    >= MAX_PENDING
                ):
                    raise Denied(429)
                before = set(protocol.transactions)
                try:
                    url, binding = await protocol.begin()
                    if step_up:
                        assert previous is not None
                        service.consume_step_up(previous.key, token)
                    prune()
                    fixture.attempts[digest(binding)] = Attempt(
                        epochs, previous, step_up, clock() + DEADLINE
                    )
                    if not step_up:
                        fixture.preauth.pop(digest(supplied[PREAUTH_COOKIE]))
                except BaseException:
                    for created in set(protocol.transactions) - before:
                        protocol.discard(created)
                    raise
                response = RedirectResponse(url, status_code=303)
                response.set_cookie(
                    COOKIE,
                    binding,
                    max_age=DEADLINE,
                    secure=True,
                    httponly=True,
                    samesite="lax",
                    path="/",
                )
                delete_cookie(response, PREAUTH_COOKIE)
                return response

    preauth_lock = asyncio.Lock()

    @bff.post("/_spike/start")
    async def start(request: Request) -> Any:
        return await begin(request, False)

    @bff.post("/_session/step-up")
    async def step_up(request: Request) -> Any:
        return await begin(request, True)

    @bff.get("/_spike/callback")
    async def callback(request: Request) -> Any:
        supplied = cookies(request)
        binding = supplied.get(COOKIE, "")
        issued: str | None = None
        try:
            attempt = fixture.attempts.pop(digest(binding), None)
            if attempt is None or clock() >= attempt.expires:
                raise Denied()
            params = parameters(request.scope["query_string"])
            request.scope["query_string"] = b""
            identity = await protocol.finish(binding, params)
            issued = await service.login(
                identity, attempt.epochs, attempt.previous, step_up=attempt.step_up
            )
            target = "/_spike/complete"
        except Exception:
            protocol.discard(binding)
            target = "/_spike/rejected"
        finally:
            request.scope["query_string"] = b""
        response = RedirectResponse(target, status_code=303)
        delete_cookie(response, COOKIE)
        delete_cookie(response, PREAUTH_COOKIE)
        if issued:
            response.set_cookie(
                SESSION_COOKIE, issued, secure=True, httponly=True, samesite="lax", path="/"
            )
        return response

    @bff.get("/_spike/complete")
    @bff.get("/_spike/rejected")
    async def completed() -> Any:
        return JSONResponse({"mode": "fictional_session_fixture"})

    @bff.get("/_session/csrf")
    @bff.get("/_session/me")
    async def read(request: Request) -> Any:
        tokens, marker = await service.read(cookies(request).get(SESSION_COOKIE, ""))
        if request.url.path.endswith("csrf"):
            return JSONResponse({"tokens": tokens})
        return JSONResponse({"mode": "fictional_session_fixture", "marker": marker})

    @bff.api_route("/_session/marker", methods=["POST", "PUT", "PATCH", "DELETE"])
    async def marker(request: Request) -> Any:
        action = request.method + ":/_session/marker"
        await service.marker(
            cookies(request).get(SESSION_COOKIE, ""),
            action,
            request.headers.get("x-csrf-token", ""),
        )
        return JSONResponse({"mode": "fictional_marker_committed"})

    @bff.post("/_session/logout")
    @bff.post("/_session/logout-all")
    async def logout(request: Request) -> Any:
        await service.revoke(
            cookies(request).get(SESSION_COOKIE, ""),
            request.headers.get("x-csrf-token", ""),
            all_sessions=request.url.path.endswith("logout-all"),
        )
        response = JSONResponse({"mode": "local_revocation_complete", "upstream": "unverified"})
        delete_cookie(response, SESSION_COOKIE)
        return response

    assert all(a.split(":", 1)[1] in PATHS for a in ACTIONS)
    return fixture


def secrets_equal(expected: str, supplied: str) -> bool:
    return bool(HANDLE.fullmatch(supplied)) and secrets.compare_digest(expected, supplied)
