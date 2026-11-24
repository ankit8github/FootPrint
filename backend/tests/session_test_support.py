"""Fictional client helpers; separate provider cookie jar, no sockets."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from httpx2 import AsyncClient, Response

from experiments.oidc_protocol import BFF
from experiments.session_fixture import SESSION_COOKIE, SessionFixture, create_session_fixture

ORIGIN = {
    "origin": BFF,
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
}


@dataclass
class Clock:
    value: float = 1000

    def __call__(self) -> float:
        return self.value


@asynccontextmanager
async def harness() -> AsyncIterator[tuple[SessionFixture, AsyncClient, Clock, Clock]]:
    clock, wall = Clock(), Clock(2_000_000_000)
    fixture = create_session_fixture(enabled=True, clock=clock, wall_clock=wall)
    try:
        async with AsyncClient(
            transport=fixture.transport,
            base_url=BFF,
            headers=ORIGIN,
            trust_env=False,
            follow_redirects=False,
        ) as client:
            yield fixture, client, clock, wall
    finally:
        fixture.clear()


async def authorize(fixture: SessionFixture, client: AsyncClient, start: Response) -> Response:
    assert start.status_code == 303
    # Same hostname/different ports is not cookie isolation in a real browser.
    # This ASGI-only experiment has a separate issuer jar, enforced by transport.
    async with AsyncClient(
        transport=fixture.transport, trust_env=False, follow_redirects=False
    ) as provider:
        result = await provider.get(start.headers["location"])
    assert result.status_code == 303
    return await client.get(result.headers["location"])


async def pending(fixture: SessionFixture, client: AsyncClient) -> Response:
    preauth = await client.get("/_session/preauth")
    assert preauth.status_code == 200
    return await client.post(
        "/_spike/start", json={}, headers={"x-csrf-token": preauth.json()["csrf"]}
    )


async def login(fixture: SessionFixture, client: AsyncClient, subject: str = "fictional-a") -> str:
    assert fixture.oidc.issuer
    fixture.oidc.issuer.subject = subject
    response = await authorize(fixture, client, await pending(fixture, client))
    assert response.headers["location"] == "/_spike/complete"
    return str(client.cookies[SESSION_COOKIE])


async def token(client: AsyncClient, action: str = "POST:/_session/marker") -> str:
    response = await client.get("/_session/csrf")
    assert response.status_code == 200
    return str(response.json()["tokens"][action])
