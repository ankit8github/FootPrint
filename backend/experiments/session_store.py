"""Bounded single-process fictional sessions. No persistence or application import."""

import asyncio
import hashlib
import math
import re
import secrets
import time
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass, replace

from experiments.oidc_protocol import ISSUER, Identity

IDLE = 1800
ABSOLUTE = 43200
MAX_SESSIONS = 8
MAX_PER_OWNER = 4
MAX_MARKERS = 1_000_000
HANDLE = re.compile(r"[A-Za-z0-9_-]{43}\Z")
OWNERS = ("fictional-a", "fictional-b")
ACTIONS = tuple(f"{method}:/_session/marker" for method in ("POST", "PUT", "PATCH", "DELETE")) + (
    "POST:/_session/logout",
    "POST:/_session/logout-all",
    "POST:/_session/step-up",
)


class Denied(Exception):
    def __init__(self, status: int = 401) -> None:
        super().__init__("SESSION_FIXTURE_REJECTED")
        self.status = status


class Unavailable(Denied):
    def __init__(self) -> None:
        super().__init__(503)


def digest(handle: str) -> str:
    if not HANDLE.fullmatch(handle):
        raise Denied()
    return hashlib.sha256(handle.encode("ascii")).hexdigest()


def random_value() -> str:
    return secrets.token_urlsafe(32)


async def no_hook(stage: str, owner: str) -> None:
    pass


Hook = Callable[[str, str], Awaitable[None]]


class OwnerFence:
    """Fixed owner set; one asyncio loop, no distributed-lock guarantee."""

    def __init__(self) -> None:
        self.locks = {owner: asyncio.Lock() for owner in OWNERS}
        self.hook: Hook = no_hook

    @asynccontextmanager
    async def hold(self, owner: str, action: str) -> AsyncIterator[None]:
        if owner not in self.locks:
            raise Denied()
        await self.hook("waiting:" + action, owner)
        async with self.locks[owner]:
            yield

    @asynccontextmanager
    async def many(self, owners: Iterable[str], action: str) -> AsyncIterator[None]:
        async with AsyncExitStack() as stack:
            for owner in sorted(set(owners)):
                await stack.enter_async_context(self.hold(owner, action))
            yield


@dataclass(frozen=True)
class Control:
    epoch: int = 0
    active: bool = True
    quarantined: bool = False
    event_sequence: int = 0
    markers: int = 0


@dataclass(frozen=True, repr=False)
class Session:
    key: str
    owner: str
    epoch: int
    created: float
    last_seen: float
    absolute: float
    tokens: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class Previous:
    key: str
    owner: str


class SessionStore:
    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self.clock = clock
        self.sessions: dict[str, Session] = {}
        self.controls = {owner: Control() for owner in OWNERS}
        self.fence = OwnerFence()
        self.available = True
        self.fail_on: str | None = None  # Trusted fixture-only failure injection.

    def healthy(self) -> None:
        now = self.clock()
        if (
            not self.available
            or type(now) not in (int, float)
            or not math.isfinite(now)
            or now < 0
            or len(self.sessions) > MAX_SESSIONS
            or set(self.controls) != set(OWNERS)
        ):
            raise Unavailable()
        for state in self.controls.values():
            if not isinstance(state, Control):
                raise Unavailable()
            if any(type(getattr(state, k)) is not bool for k in ("active", "quarantined")):
                raise Unavailable()
            if any(
                type(getattr(state, k)) is not int or not 0 <= getattr(state, k) <= MAX_MARKERS
                for k in ("epoch", "event_sequence", "markers")
            ):
                raise Unavailable()

    def epochs(self) -> dict[str, int]:
        self.healthy()
        return {owner: state.epoch for owner, state in self.controls.items()}

    def by_key(self, key: str) -> Session:
        self.healthy()
        record = self.sessions.get(key)
        if record is None:
            raise Denied()
        if not isinstance(record, Session) or record.owner not in OWNERS or record.key != key:
            raise Unavailable()
        now = self.clock()
        if (
            not math.isfinite(now)
            or any(
                type(v) not in (int, float) or not math.isfinite(v)
                for v in (record.created, record.last_seen, record.absolute)
            )
            or record.created < 0
            or not record.created <= record.last_seen <= now
            or record.absolute != record.created + ABSOLUTE
            or type(record.epoch) is not int
            or len(record.tokens) != len(ACTIONS)
            or set(dict(record.tokens)) != set(ACTIONS)
            or len({v for _, v in record.tokens}) != len(ACTIONS)
            or any(not isinstance(v, str) or not HANDLE.fullmatch(v) for _, v in record.tokens)
        ):
            raise Unavailable()
        state = self.controls[record.owner]
        if (
            not state.active
            or state.quarantined
            or state.epoch != record.epoch
            or now >= record.absolute
            or now - record.last_seen >= IDLE
        ):
            raise Denied()
        return record

    def lookup(self, handle: str) -> tuple[str, Session]:
        key = digest(handle)
        return key, self.by_key(key)

    @staticmethod
    def csrf(record: Session, action: str, token: str) -> None:
        expected = dict(record.tokens).get(action)
        if (
            expected is None
            or not HANDLE.fullmatch(token)
            or not secrets.compare_digest(expected, token)
        ):
            raise Denied(403)

    def publish(
        self, action: str, sessions: dict[str, Session], controls: dict[str, Control]
    ) -> None:
        self.healthy()
        if self.fail_on == action:
            raise Unavailable()
        # No await between guard and the in-process atomic publication.
        self.sessions, self.controls = sessions, controls

    async def login(
        self,
        identity: Identity,
        epochs: dict[str, int],
        previous: Previous | None = None,
        *,
        step_up: bool = False,
    ) -> str:
        if identity.issuer != ISSUER or identity.subject not in OWNERS:
            raise Denied()
        owner = identity.subject
        owners = {owner} | ({previous.owner} if previous else set())
        async with self.fence.many(owners, "login"):
            self.healthy()
            for locked in owners:
                state = self.controls[locked]
                if not state.active or state.quarantined or state.epoch != epochs.get(locked):
                    raise Denied()
            old = self.by_key(previous.key) if previous else None
            if step_up and (old is None or old.owner != owner):
                raise Denied()
            await self.fence.hook("locked:login", owner)
            self.healthy()
            # Recheck after any suspension, including test/provider delays.
            for locked in owners:
                state = self.controls[locked]
                if not state.active or state.quarantined or state.epoch != epochs.get(locked):
                    raise Denied()
            if previous:
                old = self.by_key(previous.key)
            now = self.clock()
            sessions = {
                key: rec
                for key, rec in self.sessions.items()
                if now < rec.absolute and now - rec.last_seen < IDLE
            }
            if previous:
                sessions.pop(previous.key, None)
            if (
                len(sessions) >= MAX_SESSIONS
                or sum(rec.owner == owner for rec in sessions.values()) >= MAX_PER_OWNER
            ):
                raise Denied(429)
            handle = random_value()
            if digest(handle) in self.sessions:
                raise Unavailable()
            created = old.created if old else now
            sessions[digest(handle)] = Session(
                digest(handle),
                owner,
                self.controls[owner].epoch,
                created,
                now,
                created + ABSOLUTE,
                tuple((action, random_value()) for action in ACTIONS),
            )
            self.publish("login", sessions, dict(self.controls))
            return handle

    async def read(self, handle: str) -> tuple[dict[str, str], int]:
        key, initial = self.lookup(handle)
        async with self.fence.hold(initial.owner, "read"):
            record = self.by_key(key)
            await self.fence.hook("locked:read", record.owner)
            record = self.by_key(key)
            sessions = {**self.sessions, key: replace(record, last_seen=self.clock())}
            self.publish("read", sessions, dict(self.controls))
            return dict(record.tokens), self.controls[record.owner].markers

    async def marker(self, handle: str, action: str, csrf: str) -> None:
        key, initial = self.lookup(handle)
        async with self.fence.hold(initial.owner, "marker"):
            record = self.by_key(key)
            self.csrf(record, action, csrf)
            await self.fence.hook("locked:marker", record.owner)
            record = self.by_key(key)
            self.csrf(record, action, csrf)
            control = self.controls[record.owner]
            if control.markers >= MAX_MARKERS:
                raise Denied(429)
            tokens = tuple((a, random_value() if a == action else t) for a, t in record.tokens)
            sessions = {
                **self.sessions,
                key: replace(record, tokens=tokens, last_seen=self.clock()),
            }
            controls = {
                **self.controls,
                record.owner: replace(control, markers=control.markers + 1),
            }
            self.publish("marker", sessions, controls)

    async def revoke(self, handle: str, csrf: str, *, all_sessions: bool) -> None:
        key, initial = self.lookup(handle)
        action = "logout_all" if all_sessions else "logout"
        csrf_action = "POST:/_session/" + ("logout-all" if all_sessions else "logout")
        async with self.fence.hold(initial.owner, action):
            record = self.by_key(key)
            self.csrf(record, csrf_action, csrf)
            await self._invalidate(record.owner, action, key=None if all_sessions else key)

    async def event(self, owner: str, sequence: int) -> None:
        if owner not in OWNERS or type(sequence) is not int or not 1 <= sequence <= MAX_MARKERS:
            raise Denied(400)
        async with self.fence.hold(owner, "event"):
            try:
                self.healthy()
            except Unavailable:
                state = self.controls.get(owner)
                if isinstance(state, Control):
                    self.controls = {**self.controls, owner: replace(state, quarantined=True)}
                raise
            if sequence != self.controls[owner].event_sequence + 1:
                raise Denied(409)
            await self._invalidate(owner, "event", sequence=sequence)

    def consume_step_up(self, key: str, csrf: str) -> None:
        record = self.by_key(key)
        self.csrf(record, "POST:/_session/step-up", csrf)
        tokens = tuple(
            (a, random_value() if a == "POST:/_session/step-up" else v) for a, v in record.tokens
        )
        self.publish(
            "step_up", {**self.sessions, key: replace(record, tokens=tokens)}, dict(self.controls)
        )

    async def _invalidate(
        self,
        owner: str,
        action: str,
        *,
        key: str | None = None,
        sequence: int | None = None,
    ) -> None:
        control = self.controls[owner]
        # An authenticated invalidation has begun. Failure/cancellation keeps this
        # fence denied; availability restoration alone cannot resurrect access.
        self.controls = {**self.controls, owner: replace(control, quarantined=True)}
        await self.fence.hook("locked:" + action, owner)
        self.healthy()
        current = self.controls[owner]
        if current.epoch != control.epoch or current.event_sequence != control.event_sequence:
            raise Unavailable()
        sessions = {
            k: r
            for k, r in self.sessions.items()
            if (k != key if key is not None else r.owner != owner)
        }
        epoch = control.epoch + (0 if key is not None else 1)
        if epoch > MAX_MARKERS:
            raise Unavailable()
        updated = replace(
            current,
            epoch=epoch,
            quarantined=False,
            event_sequence=sequence if sequence is not None else control.event_sequence,
        )
        self.publish(action, sessions, {**self.controls, owner: updated})

    async def cleanup(self) -> None:
        async with self.fence.many(OWNERS, "cleanup"):
            self.healthy()
            now = self.clock()
            sessions = {
                k: r
                for k, r in self.sessions.items()
                if now < r.absolute and now - r.last_seen < IDLE
            }
            self.publish("cleanup", sessions, dict(self.controls))

    def clear(self) -> None:
        self.sessions.clear()
        self.available = False
