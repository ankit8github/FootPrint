"""Isolated clients and view-generation model, not a frontend login implementation."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

from httpx2 import AsyncClient, Response
from session_test_support import ORIGIN, Clock, login

from experiments.oidc_protocol import BFF
from experiments.ownership_fixture import OwnershipFixture, create_ownership_fixture


@asynccontextmanager
async def harness() -> AsyncIterator[tuple[OwnershipFixture, AsyncClient, AsyncClient, Clock]]:
    clock = Clock()
    fixture = create_ownership_fixture(enabled=True, clock=clock, wall_clock=Clock(2_000_000_000))
    try:
        async with (
            AsyncClient(
                transport=fixture.transport, base_url=BFF, headers=ORIGIN, trust_env=False
            ) as a,
            AsyncClient(
                transport=fixture.transport, base_url=BFF, headers=ORIGIN, trust_env=False
            ) as b,
        ):
            await login(fixture.session, a, "fictional-a")
            await login(fixture.session, b, "fictional-b")
            yield fixture, a, b, clock
    finally:
        fixture.clear()


async def mutation(
    client: AsyncClient,
    action: str,
    path: str = "/_ownership/records",
    data: Any = None,
    headers: dict[str, str] | None = None,
) -> Response:
    tokens = await client.get("/_ownership/csrf")
    assert tokens.status_code == 200, tokens.text
    method = {"create": "POST", "update": "PATCH", "delete": "DELETE", "batch": "POST"}[action]
    return await client.request(
        method,
        path,
        json=data if data is not None else {"generation": 1, "links": []},
        headers={"x-csrf-token": tokens.json()["tokens"][action], **(headers or {})},
    )


@dataclass
class TabView:
    generation: int = 0
    rows: list[dict[str, Any]] = field(default_factory=list)

    def invalidate(self) -> None:
        self.generation += 1
        self.rows.clear()

    def accept(self, ticket: int, rows: list[dict[str, Any]]) -> None:
        if ticket == self.generation:
            self.rows = rows


def broadcast(tabs: tuple[TabView, ...], message: str) -> None:
    # Only invalidation control signal; no owner, record, token or footprint data.
    assert message == "invalidate"
    for tab in tabs:
        tab.invalidate()
