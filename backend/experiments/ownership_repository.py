"""Bounded synthetic owner-scoped repository. No SQL, persistence or app import."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Protocol, TypeVar
from uuid import UUID, uuid4

from experiments.ownership_principal import (
    CSRF_BASE,
    IDENTITIES,
    AuthenticatedPrincipal,
    PrincipalAuthority,
)
from experiments.session_store import HANDLE, MAX_MARKERS, Denied, random_value

MAX_RECORDS = 8  # Per owner: B capacity cannot affect A.
MAX_CURSORS = 16  # Per owner; no live eviction.
B_SENTINEL = "SYNTHETIC_B_ONLY_SENTINEL"
CODES = {"SYNTHETIC_A", B_SENTINEL, "SYNTHETIC_CREATED", "SYNTHETIC_UPDATED"}
T = TypeVar("T")


@dataclass(frozen=True, repr=False)
class SyntheticRecord:
    id: UUID
    owner: UUID
    code: str
    links: tuple[UUID, ...] = ()
    synthetic: bool = True


@dataclass(frozen=True, repr=False)
class Lifecycle:
    generation: int = 1
    consent_epoch: int = 1
    active: bool = True


@dataclass(frozen=True, repr=False)
class Cursor:
    principal: AuthenticatedPrincipal
    generation: int
    related_to: UUID | None
    limit: int
    offset: int


@dataclass(repr=False)
class _Memory:
    """Trusted seeding/teardown container, deliberately not a repository API."""

    records: dict[UUID, SyntheticRecord]
    lifecycle: dict[UUID, Lifecycle]
    cursors: dict[UUID, dict[str, Cursor]]
    available: bool = True

    def clear(self) -> None:
        self.available = False
        self.records.clear()
        self.lifecycle.clear()
        self.cursors.clear()


def _seed() -> _Memory:
    records: dict[UUID, SyntheticRecord] = {}
    for index, owner in enumerate(IDENTITIES.values(), 1):
        root, child = UUID(int=index * 100 + 1), UUID(int=index * 100 + 2)
        code = "SYNTHETIC_A" if index == 1 else B_SENTINEL
        records[root] = SyntheticRecord(root, owner, code, (child,))
        records[child] = SyntheticRecord(child, owner, code)
    return _Memory(
        records,
        dict.fromkeys(IDENTITIES.values(), Lifecycle()),
        {owner: {} for owner in IDENTITIES.values()},
    )


class OwnerRepository(Protocol):
    """Future adapters must preserve mandatory constructor-bound principal scope.

    Auth/session bootstrap is the explicit exception and has no footprint access.
    No unscoped find/count/batch/join method or fallback is permitted.
    """

    async def read(self, record_id: UUID) -> SyntheticRecord: ...
    async def page(
        self, *, limit: int = 2, cursor: str | None = None, related_to: UUID | None = None
    ) -> tuple[tuple[SyntheticRecord, ...], str | None, int]: ...
    async def count(self, *, related_to: UUID | None = None) -> int: ...
    async def join(self, parent: UUID) -> tuple[SyntheticRecord, ...]: ...
    async def nested(self, parent: UUID, child: UUID) -> SyntheticRecord: ...
    async def create(
        self, generation: int, links: tuple[UUID, ...], csrf: str
    ) -> SyntheticRecord: ...
    async def update(
        self, record_id: UUID, generation: int, links: tuple[UUID, ...], csrf: str
    ) -> SyntheticRecord: ...
    async def delete(self, record_id: UUID, generation: int, csrf: str) -> None: ...
    async def batch(self, ids: tuple[UUID, ...], generation: int, csrf: str) -> None: ...


class SyntheticRepository:
    def __init__(
        self, principal: AuthenticatedPrincipal, authority: PrincipalAuthority, memory: _Memory
    ) -> None:
        if type(authority) is not PrincipalAuthority or type(memory) is not _Memory:
            raise Denied()
        authority.validate(principal)
        self.__principal, self.__authority, self.__memory = principal, authority, memory

    def __valid(self, memory: _Memory) -> None:
        try:
            self.__shape(memory)
        except Denied:
            raise
        except Exception:
            raise Denied(503) from None

    def __shape(self, memory: _Memory) -> None:
        # Validate before filtering: an absent/corrupt owner never means global scope.
        owners = set(IDENTITIES.values())
        if (
            type(memory.available) is not bool
            or not memory.available
            or set(memory.lifecycle) != owners
            or set(memory.cursors) != owners
            or len(memory.records) > MAX_RECORDS * 2
        ):
            raise Denied(503)
        for state in memory.lifecycle.values():
            if (
                type(state) is not Lifecycle
                or type(state.active) is not bool
                or any(
                    type(v) is not int or not 1 <= v <= MAX_MARKERS
                    for v in (state.generation, state.consent_epoch)
                )
            ):
                raise Denied(503)
        for key, row in memory.records.items():
            if (
                type(row) is not SyntheticRecord
                or type(key) is not UUID
                or type(row.id) is not UUID
                or row.id != key
                or type(row.owner) is not UUID
                or row.owner not in owners
                or row.synthetic is not True
                or row.code not in CODES
                or (
                    row.code == B_SENTINEL
                    and row.owner != IDENTITIES[(self.__principal.issuer, "fictional-b")]
                )
                or (
                    row.code == "SYNTHETIC_A"
                    and row.owner != IDENTITIES[(self.__principal.issuer, "fictional-a")]
                )
                or type(row.links) is not tuple
                or len(row.links) > MAX_RECORDS
                or len(set(row.links)) != len(row.links)
            ):
                raise Denied(503)
            for link in row.links:
                other = memory.records.get(link)
                if (
                    type(link) is not UUID
                    or type(other) is not SyntheticRecord
                    or other.owner != row.owner
                ):
                    raise Denied(503)
        for owner in owners:
            if sum(row.owner == owner for row in memory.records.values()) > MAX_RECORDS:
                raise Denied(503)
            cursors = memory.cursors[owner]
            if type(cursors) is not dict or len(cursors) > MAX_CURSORS:
                raise Denied(503)
            for cursor_key, value in cursors.items():
                if (
                    type(cursor_key) is not str
                    or not HANDLE.fullmatch(cursor_key)
                    or type(value) is not Cursor
                    or type(value.principal) is not AuthenticatedPrincipal
                    or type(value.principal.owner_id) is not UUID
                    or type(value.principal.auth_epoch) is not int
                    or not 0 <= value.principal.auth_epoch <= MAX_MARKERS
                    or type(value.principal.session_key) is not str
                    or len(value.principal.session_key) != 64
                    or value.principal.owner_id != owner
                    or IDENTITIES.get((value.principal.issuer, value.principal.subject)) != owner
                    or type(value.generation) is not int
                    or not 1 <= value.generation <= MAX_MARKERS
                    or (value.related_to is not None and type(value.related_to) is not UUID)
                    or type(value.limit) is not int
                    or not 1 <= value.limit <= MAX_RECORDS
                    or type(value.offset) is not int
                    or not 1 <= value.offset <= MAX_RECORDS
                ):
                    raise Denied(503)

    @staticmethod
    def __id(value: UUID) -> None:
        if type(value) is not UUID:
            raise Denied(422)

    def __row(self, memory: _Memory, record_id: UUID) -> SyntheticRecord:
        self.__id(record_id)
        row = memory.records.get(record_id)
        if row is None or row.owner != self.__principal.owner_id:
            raise Denied(404)
        return row

    async def __run(
        self,
        action: str,
        work: Callable[[_Memory], T],
        *,
        generation: int | None = None,
        csrf: str = "",
    ) -> T:
        principal, authority, memory = self.__principal, self.__authority, self.__memory
        authority.validate(principal)
        self.__valid(memory)
        initial_lifecycle = memory.lifecycle[principal.owner_id]
        async with authority.store.fence.hold(principal.subject, "ownership"):
            authority.validate(principal)
            if action in {"create", "update", "delete", "batch"}:
                authority.csrf(principal, action, csrf)
            await authority.store.fence.hook("locked:ownership", principal.subject)
            session = authority.validate(principal)
            self.__valid(memory)
            lifecycle = memory.lifecycle[principal.owner_id]
            if not lifecycle.active or lifecycle != initial_lifecycle:
                raise Denied(409)
            mutation = action in {"create", "update", "delete", "batch"}
            if mutation:
                authority.csrf(principal, action, csrf)
                if type(generation) is not int or not 1 <= generation <= MAX_MARKERS:
                    raise Denied(422)
                if generation != lifecycle.generation or generation == MAX_MARKERS:
                    raise Denied(409)
            # Never publish draft state when work, auth, publication or cancellation fails.
            draft = _Memory(
                dict(memory.records),
                dict(memory.lifecycle),
                {owner: dict(values) for owner, values in memory.cursors.items()},
            )
            result = work(draft)
            if mutation:
                draft.lifecycle[principal.owner_id] = replace(
                    lifecycle, generation=lifecycle.generation + 1
                )
            self.__valid(draft)
            authority.validate(principal)
            task = asyncio.current_task()
            if task is not None and task.cancelling():
                raise asyncio.CancelledError
            if mutation:
                tokens = tuple(
                    (a, random_value() if a == CSRF_BASE else t) for a, t in session.tokens
                )
                session = replace(session, tokens=tokens)
            sessions = {
                **authority.store.sessions,
                session.key: replace(session, last_seen=authority.store.clock()),
            }
            # Final validation and publication have no suspension; same fence as revocation.
            authority.validate(principal)
            authority.store.publish("ownership", sessions, dict(authority.store.controls))
            memory.records, memory.lifecycle, memory.cursors = (
                draft.records,
                draft.lifecycle,
                draft.cursors,
            )
            return result

    async def read(self, record_id: UUID) -> SyntheticRecord:
        return await self.__run("read", lambda m: self.__row(m, record_id))

    def __rows(self, memory: _Memory, related_to: UUID | None) -> tuple[SyntheticRecord, ...]:
        links = self.__row(memory, related_to).links if related_to is not None else None
        return tuple(
            sorted(
                (
                    row
                    for row in memory.records.values()
                    if row.owner == self.__principal.owner_id and (links is None or row.id in links)
                ),
                key=lambda row: row.id.int,
            )
        )

    async def page(
        self, *, limit: int = 2, cursor: str | None = None, related_to: UUID | None = None
    ) -> tuple[tuple[SyntheticRecord, ...], str | None, int]:
        def work(m: _Memory) -> tuple[tuple[SyntheticRecord, ...], str | None, int]:
            if type(limit) is not int or not 1 <= limit <= MAX_RECORDS:
                raise Denied(422)
            generation = m.lifecycle[self.__principal.owner_id].generation
            cursors = m.cursors[self.__principal.owner_id]
            offset = 0
            if cursor is not None:
                if type(cursor) is not str or not HANDLE.fullmatch(cursor):
                    raise Denied(422)
                saved = cursors.get(cursor)
                if (
                    saved is None
                    or saved.principal != self.__principal
                    or saved.related_to != related_to
                    or saved.limit != limit
                ):
                    raise Denied(404)
                if saved.generation != generation:
                    raise Denied(409)
                offset = saved.offset
            rows = self.__rows(m, related_to)
            next_cursor = None
            if offset + limit < len(rows):
                # Discard only cursors already stale for this owner/session.
                cursors = {
                    k: v
                    for k, v in cursors.items()
                    if v.generation == generation
                    and v.principal.session_key in self.__authority.store.sessions
                }
                if len(cursors) >= MAX_CURSORS:
                    raise Denied(429)
                next_cursor = random_value()
                cursors[next_cursor] = Cursor(
                    self.__principal, generation, related_to, limit, offset + limit
                )
                m.cursors[self.__principal.owner_id] = cursors
            return rows[offset : offset + limit], next_cursor, generation

        return await self.__run("page", work)

    async def count(self, *, related_to: UUID | None = None) -> int:
        return await self.__run("count", lambda m: len(self.__rows(m, related_to)))

    async def join(self, parent: UUID) -> tuple[SyntheticRecord, ...]:
        return await self.__run("join", lambda m: self.__rows(m, parent))

    async def nested(self, parent: UUID, child: UUID) -> SyntheticRecord:
        def work(m: _Memory) -> SyntheticRecord:
            row = self.__row(m, parent)
            other = self.__row(m, child)
            if child not in row.links:
                raise Denied(404)
            return other

        return await self.__run("nested", work)

    def __links(self, m: _Memory, links: tuple[UUID, ...]) -> None:
        if type(links) is not tuple or len(links) > MAX_RECORDS:
            raise Denied(422)
        for link in links:
            self.__id(link)
        if len(set(links)) != len(links):
            raise Denied(422)
        for link in links:
            self.__row(m, link)

    async def create(self, generation: int, links: tuple[UUID, ...], csrf: str) -> SyntheticRecord:
        def work(m: _Memory) -> SyntheticRecord:
            self.__links(m, links)
            if len(self.__rows(m, None)) >= MAX_RECORDS:
                raise Denied(429)
            row = SyntheticRecord(uuid4(), self.__principal.owner_id, "SYNTHETIC_CREATED", links)
            if row.id in m.records:
                raise Denied(503)
            m.records[row.id] = row
            return row

        return await self.__run("create", work, generation=generation, csrf=csrf)

    async def update(
        self, record_id: UUID, generation: int, links: tuple[UUID, ...], csrf: str
    ) -> SyntheticRecord:
        def work(m: _Memory) -> SyntheticRecord:
            row = self.__row(m, record_id)
            self.__links(m, links)
            row = replace(row, code="SYNTHETIC_UPDATED", links=links)
            m.records[row.id] = row
            return row

        return await self.__run("update", work, generation=generation, csrf=csrf)

    def __delete(self, m: _Memory, ids: tuple[UUID, ...]) -> None:
        if type(ids) is not tuple or not 1 <= len(ids) <= MAX_RECORDS or len(set(ids)) != len(ids):
            raise Denied(422)
        # Validate the whole batch before modifying the private draft.
        for record_id in ids:
            self.__row(m, record_id)
        for record_id in ids:
            del m.records[record_id]
        for key, row in tuple(m.records.items()):
            if row.owner == self.__principal.owner_id:
                m.records[key] = replace(
                    row, links=tuple(link for link in row.links if link not in ids)
                )

    async def delete(self, record_id: UUID, generation: int, csrf: str) -> None:
        await self.__run(
            "delete", lambda m: self.__delete(m, (record_id,)), generation=generation, csrf=csrf
        )

    async def batch(self, ids: tuple[UUID, ...], generation: int, csrf: str) -> None:
        await self.__run("batch", lambda m: self.__delete(m, ids), generation=generation, csrf=csrf)
