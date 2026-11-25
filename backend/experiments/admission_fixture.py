"""Never-served validation-only ASGI experiment; default has no authority/routes."""

import asyncio
import hashlib
import hmac
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass

from httpx2 import ASGITransport, AsyncBaseTransport, Response
from httpx2 import Request as HTTPRequest
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import Receive, Scope, Send

from experiments.admission_registry import SyntheticRegistry
from experiments.minimized_contract import MAX_BODY, AdmissionEnvelope, parse_json
from experiments.oidc_protocol import BFF
from experiments.ownership_fixture import FORBIDDEN_HEADERS
from experiments.ownership_principal import (
    CSRF_BASE,
    IDENTITIES,
    AuthenticatedPrincipal,
    PrincipalAuthority,
)
from experiments.session_fixture import (
    HEADERS,
    SESSION_COOKIE,
    SessionFixture,
    cookies,
    create_session_fixture,
    same_origin,
)
from experiments.session_store import Denied

PREFIX = "/_admission"
ERROR = {"code": "ADMISSION_FIXTURE_REJECTED"}
RECEIPT = {"schema_version": "minimized-evidence-v1", "mode": "fictional_batch_validation_only"}


@dataclass(frozen=True)
class FictionalConsent:
    granted: bool = False
    epoch: int = 1
    revision: int = 1
    auth_epoch: int = 0


class AdmissionTransport(AsyncBaseTransport):
    def __init__(self, fixture: "AdmissionFixture") -> None:
        self.fixture = fixture

    async def handle_async_request(self, request: HTTPRequest) -> Response:
        url = request.url
        if not url.path.startswith(PREFIX):
            return await self.fixture.session.transport.handle_async_request(request)
        try:
            origin = str(url.copy_with(path="/", query=None)).rstrip("/")
            if origin != BFF or url.username or url.password or url.fragment:
                return Response(422, json=ERROR, headers=HEADERS)
            response = await ASGITransport(app=self.fixture.bff).handle_async_request(request)
            await response.aread()
            return response
        finally:
            # Synthetic path/query sentinels must not enter HTTPX retained URL/logs.
            request.url = url.copy_with(path=PREFIX + "/redacted", query=None)


class AdmissionFixture:
    def __init__(self, session: SessionFixture, *, enabled: bool) -> None:
        self.session = session
        self.authority = PrincipalAuthority(session.store) if enabled and session.store else None
        self.registry = SyntheticRegistry() if enabled else None
        # Trusted test seeding/corruption API only, never remotely reachable.
        self.controls = (
            {owner: FictionalConsent() for owner in IDENTITIES.values()} if enabled else {}
        )
        self.enabled = enabled
        self.bff = self.dispatch
        self.transport = AdmissionTransport(self)

    def clear(self) -> None:
        self.session.clear()
        self.controls.clear()
        self.authority = None
        self.registry = None
        self.enabled = False

    def control(self, principal: AuthenticatedPrincipal) -> FictionalConsent:
        if (
            type(self.authority) is not PrincipalAuthority
            or type(self.registry) is not SyntheticRegistry
        ):
            raise Denied(503)
        self.authority.validate(principal)
        if type(self.controls) is not dict or set(self.controls) != set(IDENTITIES.values()):
            raise Denied(503)
        for state in self.controls.values():
            if (
                type(state) is not FictionalConsent
                or type(state.granted) is not bool
                or any(
                    type(v) is not int or not 1 <= v <= 1_000_000
                    for v in (state.epoch, state.revision)
                )
                or type(state.auth_epoch) is not int
                or not 0 <= state.auth_epoch <= 1_000_000
            ):
                raise Denied(503)
        return self.controls[principal.owner_id]

    def csrf(self, principal: AuthenticatedPrincipal) -> str:
        if self.authority is None:
            raise Denied(503)
        record = self.authority.validate(principal)
        return hmac.new(
            dict(record.tokens)[CSRF_BASE].encode("ascii"),
            b"fictional-admission-v1:validate",
            hashlib.sha256,
        ).hexdigest()

    def precondition(
        self,
        principal: AuthenticatedPrincipal,
        token: str,
        envelope: AdmissionEnvelope | None = None,
    ) -> FictionalConsent:
        state = self.control(principal)
        if (
            type(token) is not str
            or len(token) != 64
            or any(c not in "0123456789abcdef" for c in token)
            or not secrets.compare_digest(self.csrf(principal), token)
        ):
            raise Denied(403)
        if not state.granted:
            raise Denied(403)
        if state.auth_epoch != principal.auth_epoch:
            raise Denied(409)
        if envelope is not None and (
            envelope.consent_epoch != state.epoch or envelope.expected_revision != state.revision
        ):
            raise Denied(409)
        return state

    async def validate(
        self, principal: AuthenticatedPrincipal, envelope: AdmissionEnvelope, token: str
    ) -> dict[str, str]:
        # Revalidate trusted Python callers as well as the HTTP path.
        if type(envelope) is not AdmissionEnvelope:
            raise Denied(422)
        initial = self.precondition(principal, token, envelope)
        store = self.session.store
        if store is None:
            raise Denied(503)
        async with store.fence.hold(principal.subject, "admission"):
            self.precondition(principal, token, envelope)
            await store.fence.hook("locked:admission", principal.subject)
            if self.precondition(principal, token, envelope) != initial:
                raise Denied(409)
            if type(self.registry) is not SyntheticRegistry:
                raise Denied(503)
            self.registry.admit(envelope.batch)
            task = asyncio.current_task()
            if task is None or task.cancelling():
                raise asyncio.CancelledError
            if self.precondition(principal, token, envelope) != initial:
                raise Denied(409)
            # No await, writes, session touch, token rotation or batch retention.
            return dict(RECEIPT)

    async def dispatch(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    self.clear()
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        if scope["type"] != "http":
            return
        if not self.enabled:
            await JSONResponse(ERROR, status_code=404, headers=HEADERS)(scope, receive, send)
            return
        if not scope["path"].startswith(PREFIX):
            await self.session.bff(scope, receive, send)
            return
        try:
            response = await self.handle(Request(scope, receive))
        except Denied as error:
            response = JSONResponse(ERROR, status_code=error.status)
        except Exception:
            response = JSONResponse(ERROR, status_code=503)
        response.headers.update(HEADERS)
        await response(scope, receive, send)

    async def handle(self, request: Request) -> JSONResponse:
        if (
            str(request.base_url).rstrip("/") != BFF
            or request.headers.getlist("host") != ["127.0.0.1:9444"]
            or request.client is None
            or request.client.host != "127.0.0.1"
            or not request.url.path.isascii()
            or request.scope["raw_path"] != request.url.path.encode("ascii")
            or any(k.startswith("x-forwarded-") or "method-override" in k for k in request.headers)
        ):
            raise Denied(422)
        if self.authority is None:
            raise Denied(503)
        principal = self.authority.resolve(cookies(request).get(SESSION_COOKIE, ""))
        if any(k in FORBIDDEN_HEADERS for k in request.headers) or request.scope["query_string"]:
            raise Denied(422)
        same_origin(request)
        if request.url.path == PREFIX + "/csrf" and request.method == "GET":
            self.control(principal)
            async for part in request.stream():
                if part:
                    raise Denied(422)
            return JSONResponse({"csrf": self.csrf(principal)})
        if request.url.path != PREFIX + "/validate":
            raise Denied(404)
        if request.method != "POST":
            raise Denied(422)
        tokens = request.headers.getlist("x-csrf-token")
        if len(tokens) != 1:
            raise Denied(403)
        self.precondition(principal, tokens[0])
        payload = await streamed(request)
        try:
            envelope = AdmissionEnvelope.model_validate(parse_json(payload))
        except (ValueError, RecursionError, UnicodeError):
            raise Denied(422) from None
        return JSONResponse(await self.validate(principal, envelope, tokens[0]))


async def streamed(request: Request) -> bytes:
    if (
        request.headers.getlist("content-type")
        not in [["application/json"], ["application/json; charset=utf-8"]]
        or "content-encoding" in request.headers
        or "transfer-encoding" in request.headers
    ):
        raise Denied(415)
    lengths = request.headers.getlist("content-length")
    if not lengths:
        raise Denied(415)
    if (
        len(lengths) != 1
        or not lengths[0].isascii()
        or not lengths[0].isdigit()
        or len(lengths[0]) > 10
    ):
        raise Denied(422)
    length = int(lengths[0])
    if length > MAX_BODY:
        raise Denied(413)
    body = bytearray()
    async for part in request.stream():
        if len(body) + len(part) > MAX_BODY:
            raise Denied(413)
        body.extend(part)
    if len(body) != length:
        raise Denied(422)
    return bytes(body)


def create_admission_fixture(
    *,
    enabled: bool = False,
    clock: Callable[[], float] = time.monotonic,
    wall_clock: Callable[[], float] = time.time,
) -> AdmissionFixture:
    if type(enabled) is not bool:
        raise Denied(422)
    return AdmissionFixture(
        create_session_fixture(enabled=enabled, clock=clock, wall_clock=wall_clock), enabled=enabled
    )
