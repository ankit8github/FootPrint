"""Test-only consent seeding and in-process clients; no browser consent integration."""

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from httpx2 import AsyncClient, Response
from session_test_support import ORIGIN, Clock, login

from experiments.admission_fixture import (
    AdmissionFixture,
    FictionalConsent,
    create_admission_fixture,
)
from experiments.admission_registry import DATA
from experiments.oidc_protocol import BFF
from experiments.session_fixture import SESSION_COOKIE

MANIFEST = json.loads((DATA / "manifest.json").read_bytes())
DIGESTS: list[str] = [e["digest"] for e in MANIFEST["entries"]]


def batch(digest: str = DIGESTS[0]) -> dict[str, Any]:
    return dict(json.loads((DATA / (digest + ".json")).read_bytes()))


def example(field: str = "observations") -> dict[str, Any]:
    return next(batch(d) for d in DIGESTS if batch(d)[field])


def envelope(data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "consent_version": "fictional-admission-consent-v1",
        "consent_epoch": 1,
        "expected_revision": 1,
        "batch": data if data is not None else example(),
    }


@asynccontextmanager
async def harness(
    *, consent: bool = True
) -> AsyncIterator[tuple[AdmissionFixture, AsyncClient, AsyncClient, Clock]]:
    clock = Clock()
    fixture = create_admission_fixture(enabled=True, clock=clock, wall_clock=Clock(2_000_000_000))
    try:
        async with (
            AsyncClient(
                transport=fixture.transport, base_url=BFF, headers=ORIGIN, trust_env=False
            ) as a,
            AsyncClient(
                transport=fixture.transport, base_url=BFF, headers=ORIGIN, trust_env=False
            ) as b,
        ):
            for client, subject in ((a, "fictional-a"), (b, "fictional-b")):
                handle = await login(fixture.session, client, subject)
                assert fixture.authority
                principal = fixture.authority.resolve(handle)
                if consent:
                    fixture.controls[principal.owner_id] = FictionalConsent(
                        True, 1, 1, principal.auth_epoch
                    )
            yield fixture, a, b, clock
    finally:
        fixture.clear()


async def submit(
    client: AsyncClient,
    data: Any = None,
    *,
    raw: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> Response:
    response = await client.get("/_admission/csrf")
    token = response.json().get("csrf", "0" * 64)
    return await client.post(
        "/_admission/validate",
        content=raw
        if raw is not None
        else json.dumps(envelope() if data is None else data).encode(),
        headers={"content-type": "application/json", "x-csrf-token": token, **(headers or {})},
    )


async def exchange(
    fixture: AdmissionFixture,
    client: AsyncClient,
    chunks: list[bytes],
    *,
    headers: list[tuple[bytes, bytes]] | None = None,
    path: str = "/_admission/validate",
    method: str = "POST",
    query: bytes = b"",
) -> tuple[int, bytes, int]:
    csrf = (await client.get("/_admission/csrf")).json().get("csrf", "0" * 64)
    raw_headers = [
        (b"host", b"127.0.0.1:9444"),
        (b"cookie", (SESSION_COOKIE + "=" + client.cookies[SESSION_COOKIE]).encode()),
        (b"x-csrf-token", csrf.encode()),
        *[(k.encode(), v.encode()) for k, v in ORIGIN.items()],
    ]
    raw_headers.extend(
        headers
        if headers is not None
        else [
            (b"content-type", b"application/json"),
            (b"content-length", str(sum(map(len, chunks))).encode()),
        ]
    )
    scope: Any = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "https",
        "path": path,
        "raw_path": path.encode(),
        "query_string": query,
        "root_path": "",
        "headers": raw_headers,
        "client": ("127.0.0.1", 1234),
        "server": ("127.0.0.1", 9444),
    }
    messages: list[Any] = []
    reads = 0

    async def receive() -> Any:
        nonlocal reads
        reads += 1
        index = reads - 1
        if index >= len(chunks):
            return {"type": "http.disconnect"}
        return {"type": "http.request", "body": chunks[index], "more_body": reads < len(chunks)}

    async def send(message: Any) -> None:
        messages.append(message)

    await fixture.bff(scope, receive, send)
    return messages[0]["status"], b"".join(m.get("body", b"") for m in messages[1:]), reads
