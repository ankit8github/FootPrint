"""Explicit opt-in fictional ownership ASGI wrapper; never mounted by app.main."""

import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from fastapi import FastAPI, Request
from httpx2 import ASGITransport, AsyncBaseTransport, Response
from httpx2 import Request as HTTPRequest
from starlette.responses import JSONResponse

from experiments.oidc_protocol import BFF, strict_json
from experiments.ownership_principal import AuthenticatedPrincipal, PrincipalAuthority
from experiments.ownership_repository import (
    OwnerRepository,
    SyntheticRecord,
    SyntheticRepository,
    _Memory,
    _seed,
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

PREFIX = "/_ownership"
ERROR = {"code": "OWNERSHIP_FIXTURE_REJECTED"}
FORBIDDEN_HEADERS = {
    "x-user-id",
    "x-owner",
    "x-owner-id",
    "x-tenant-id",
    "authorization",
    "owner",
    "owner_id",
    "user_id",
    "tenant_id",
}


class OwnershipTransport(AsyncBaseTransport):
    def __init__(self, fixture: "OwnershipFixture") -> None:
        self.fixture = fixture

    async def handle_async_request(self, request: HTTPRequest) -> Response:
        url = request.url
        if not url.path.startswith(PREFIX):
            return await self.fixture.session.transport.handle_async_request(request)
        try:
            origin = str(url.copy_with(path="/", query=None)).rstrip("/")
            if origin != BFF or url.username or url.password or url.fragment:
                raise Denied(422)
            response = await ASGITransport(app=self.fixture.bff).handle_async_request(request)
            await response.aread()
            return response
        finally:
            # HTTPX logs/retained error requests must not capture IDs, filters or cursors.
            request.url = url.copy_with(path=PREFIX + "/redacted", query=None)


@dataclass(repr=False)
class OwnershipFixture:
    bff: FastAPI
    session: SessionFixture
    authority: PrincipalAuthority | None
    _memory: _Memory | None  # Trusted test-only seeding/corruption inspection, no HTTP access.
    transport: OwnershipTransport = field(init=False)

    def __post_init__(self) -> None:
        self.transport = OwnershipTransport(self)

    def repository(self, principal: AuthenticatedPrincipal) -> OwnerRepository:
        if self.authority is None or self._memory is None:
            raise Denied()
        return SyntheticRepository(principal, self.authority, self._memory)

    def clear(self) -> None:
        self.session.clear()
        if self._memory is not None:
            self._memory.clear()


def uuid(value: Any) -> UUID:
    try:
        if type(value) is not str or str(UUID(value)) != value:
            raise ValueError
        return UUID(value)
    except Exception:
        raise Denied(422) from None


def output(row: SyntheticRecord) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "code": row.code,
        "links": [str(k) for k in row.links],
        "synthetic": True,
    }


async def body(request: Request, keys: set[str]) -> dict[str, Any]:
    if request.headers.getlist("content-type") not in [
        ["application/json"],
        ["application/json; charset=utf-8"],
    ]:
        raise Denied(422)
    raw = b""
    async for part in request.stream():
        raw += part
        if len(raw) > 2048:
            raise Denied(422)
    try:
        data = strict_json(raw)
        if type(data) is not dict or set(data) != keys:
            raise ValueError
        if type(data["generation"]) is not int or not 1 <= data["generation"] <= 1_000_000:
            raise ValueError
        # Exact schemas at all levels: no ownership aliases, nested JSON, prose or claims.
        for field in {"links", "ids"} & keys:
            values = data[field]
            if type(values) is not list or len(values) > 8:
                raise ValueError
            data[field] = tuple(uuid(v) for v in values)
        return dict(data)
    except Exception:
        raise Denied(422) from None


def query(request: Request, allowed: set[str]) -> dict[str, str]:
    pairs = list(request.query_params.multi_items())
    values = dict(pairs)
    if len(pairs) != len(values) or not set(values) <= allowed or len(request.url.query) > 512:
        raise Denied(422)
    return values


def create_ownership_fixture(
    *,
    enabled: bool = False,
    clock: Callable[[], float] = time.monotonic,
    wall_clock: Callable[[], float] = time.time,
) -> OwnershipFixture:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            fixture.clear()

    session = create_session_fixture(enabled=enabled, clock=clock, wall_clock=wall_clock)
    bff = FastAPI(openapi_url=None, docs_url=None, redoc_url=None, lifespan=lifespan)
    authority = PrincipalAuthority(session.store) if session.store else None
    fixture = OwnershipFixture(bff, session, authority, _seed() if enabled else None)
    if not enabled:
        return fixture
    assert authority is not None
    service: PrincipalAuthority = authority

    @bff.middleware("http")
    async def security(request: Request, call_next: Any) -> Any:
        if not request.url.path.startswith(PREFIX):
            return await call_next(request)
        try:
            if (
                str(request.base_url).rstrip("/") != BFF
                or request.headers.getlist("host") != ["127.0.0.1:9444"]
                or any(k.startswith("x-forwarded-") for k in request.headers)
                or request.client is None
                or request.client.host != "127.0.0.1"
                or not request.url.path.isascii()
                or request.scope["raw_path"] != request.url.path.encode("ascii")
            ):
                raise Denied(422)
            try:
                principal = service.resolve(cookies(request).get(SESSION_COOKIE, ""))
            except Denied as error:
                raise Denied(401 if error.status != 503 else 503) from None
            if any(k in request.headers for k in FORBIDDEN_HEADERS):
                raise Denied(422)
            same_origin(request)
            # Reject before framework redirects/405s can reflect an unvalidated URL.
            if not request.url.path.startswith(PREFIX + "/"):
                raise Denied(404)
            if request.method not in {"GET", "POST", "PATCH", "DELETE"}:
                raise Denied(422)
            request.state.principal = principal
            response = await call_next(request)
        except Denied as error:
            response = JSONResponse(ERROR, status_code=error.status)
        except Exception:
            response = JSONResponse(ERROR, status_code=503)
        response.headers.update(HEADERS)
        return response

    @bff.api_route(
        PREFIX + "/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    )
    async def dispatch(request: Request, path: str) -> Any:
        principal = request.state.principal
        repo = fixture.repository(principal)
        parts = path.split("/")
        method = request.method
        if method == "GET":
            async for part in request.stream():
                if part:
                    raise Denied(422)
            if parts == ["csrf"]:
                query(request, set())
                await repo.count()
                return JSONResponse({"tokens": service.tokens(principal)})
            if parts == ["records"] or parts == ["records", "count"]:
                count = parts[-1] == "count"
                params = query(
                    request, {"related_to"} if count else {"related_to", "limit", "cursor"}
                )
                related = uuid(params["related_to"]) if "related_to" in params else None
                if count:
                    return JSONResponse({"count": await repo.count(related_to=related)})
                limit = params.get("limit", "2")
                if limit not in {str(i) for i in range(1, 9)}:
                    raise Denied(422)
                rows, cursor, generation = await repo.page(
                    limit=int(limit), cursor=params.get("cursor"), related_to=related
                )
                return JSONResponse(
                    {"items": [output(r) for r in rows], "cursor": cursor, "generation": generation}
                )
            query(request, set())
            if len(parts) == 2 and parts[0] == "records":
                return JSONResponse(output(await repo.read(uuid(parts[1]))))
            if len(parts) in {3, 4} and parts[0] == "records" and parts[2] == "children":
                parent = uuid(parts[1])
                if len(parts) == 3:
                    return JSONResponse({"items": [output(r) for r in await repo.join(parent)]})
                return JSONResponse(output(await repo.nested(parent, uuid(parts[3]))))
            raise Denied(404)
        query(request, set())
        action = (
            "create"
            if method == "POST" and parts == ["records"]
            else "batch"
            if method == "POST" and parts == ["records", "batch"]
            else "update"
            if method == "PATCH" and len(parts) == 2 and parts[0] == "records"
            else "delete"
            if method == "DELETE" and len(parts) == 2 and parts[0] == "records"
            else None
        )
        if action is None:
            raise Denied(422)
        tokens = request.headers.getlist("x-csrf-token")
        if len(tokens) != 1:
            raise Denied(403)
        service.csrf(principal, action, tokens[0])
        fields = {"generation"} | (
            {"links"} if action in {"create", "update"} else {"ids"} if action == "batch" else set()
        )
        data = await body(request, fields)
        generation, csrf = data["generation"], tokens[0]
        if action == "create":
            return JSONResponse(
                output(await repo.create(generation, data["links"], csrf)), status_code=201
            )
        if action == "update":
            return JSONResponse(
                output(await repo.update(uuid(parts[1]), generation, data["links"], csrf))
            )
        if action == "delete":
            await repo.delete(uuid(parts[1]), generation, csrf)
        else:
            await repo.batch(data["ids"], generation, csrf)
        return JSONResponse({"mode": "synthetic_mutation_committed"})

    bff.mount("/", session.bff)
    return fixture
