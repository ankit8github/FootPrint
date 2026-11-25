"""Barrier-controlled synthetic writes versus revocation; no database lock claims."""

import asyncio
import copy
from dataclasses import replace
from typing import Any
from uuid import UUID

import pytest
from ownership_test_support import harness
from session_test_support import login, token

from experiments.ownership_repository import B_SENTINEL
from experiments.session_fixture import SESSION_COOKIE
from experiments.session_store import IDLE, Denied


async def no_pause(stage: str, owner: str) -> None:
    pass


@pytest.mark.parametrize("subject", ["fictional-a", "fictional-b"])
@pytest.mark.parametrize("invalidator", ["logout", "logout_all", "recovery", "mfa_reset"])
@pytest.mark.parametrize("first", ["write", "revoke"])
@pytest.mark.parametrize("operation", ["create", "update", "delete", "batch"])
def test_both_lock_orders(subject: str, invalidator: str, first: str, operation: str) -> None:
    async def run() -> None:
        async with harness() as (f, a, b, _):
            assert f.authority and f.session.store and f.session.events and f._memory
            c = a if subject == "fictional-a" else b
            store, events, memory = f.session.store, f.session.events, f._memory
            handle = c.cookies[SESSION_COOKIE]
            principal = f.authority.resolve(handle)
            repo = f.repository(principal)
            csrf = f.authority.tokens(principal)[operation]
            logout_csrf = await token(
                c, "POST:/_session/" + ("logout-all" if invalidator == "logout_all" else "logout")
            )
            root = UUID(int=101 if subject == "fictional-a" else 201)
            before = copy.deepcopy(memory.records)
            other = {k: v for k, v in before.items() if v.owner != principal.owner_id}
            entered, release, queued = asyncio.Event(), asyncio.Event(), asyncio.Event()
            prelock, allow_wait = asyncio.Event(), asyncio.Event()
            revoke_action = "event" if invalidator in {"recovery", "mfa_reset"} else invalidator

            async def hook(stage: str, owner: str) -> None:
                if owner != subject:
                    return
                if first == "revoke" and stage == "waiting:ownership":
                    prelock.set()
                    await allow_wait.wait()
                held = "ownership" if first == "write" else revoke_action
                waiting = revoke_action if first == "write" else "ownership"
                if stage == "locked:" + held:
                    entered.set()
                    await release.wait()
                if stage == "waiting:" + waiting:
                    queued.set()

            store.fence.hook = hook

            async def write() -> None:
                if operation == "create":
                    await repo.create(1, (), csrf)
                elif operation == "update":
                    await repo.update(root, 1, (), csrf)
                elif operation == "delete":
                    await repo.delete(root, 1, csrf)
                else:
                    await repo.batch((root,), 1, csrf)

            async def revoke() -> None:
                if revoke_action == "event":
                    await events.apply(events.sign(subject, 1, invalidator))
                else:
                    await store.revoke(
                        handle, logout_csrf, all_sessions=invalidator == "logout_all"
                    )

            writer = asyncio.create_task(write())
            if first == "revoke":
                await asyncio.wait_for(prelock.wait(), 3)
                revoker = asyncio.create_task(revoke())
                await asyncio.wait_for(entered.wait(), 3)
                release.set()
                await asyncio.wait_for(revoker, 3)
                allow_wait.set()
                with pytest.raises(Denied) as denied:
                    await asyncio.wait_for(writer, 3)
                assert denied.value.status == 401
                assert memory.records == before
                assert memory.lifecycle[principal.owner_id].generation == 1
            else:
                await asyncio.wait_for(entered.wait(), 3)
                revoker = asyncio.create_task(revoke())
                await asyncio.wait_for(queued.wait(), 3)
                release.set()
                await asyncio.wait_for(asyncio.gather(writer, revoker), 3)
                assert memory.records != before
                assert memory.lifecycle[principal.owner_id].generation == 2
            store.fence.hook = no_pause
            after = copy.deepcopy(memory.records)
            with pytest.raises(Denied):
                await write()
            assert memory.records == after
            assert {
                k: v for k, v in memory.records.items() if v.owner != principal.owner_id
            } == other
            other_client = b if c is a else a
            assert (await other_client.get("/_ownership/records")).status_code == 200

    asyncio.run(run())


@pytest.mark.parametrize(
    "failure",
    [
        "cancel_locked",
        "cancel_waiting",
        "cancel_swallowed",
        "publication",
        "outage",
        "expired",
        "epoch",
        "missing",
        "inactive",
        "quarantined",
        "generation",
        "consent",
        "lifecycle",
    ],
)
def test_final_guard_and_failure_never_publish(failure: str) -> None:
    async def run() -> None:
        async with harness() as (f, a, _, clock):
            assert f.authority and f.session.store and f._memory
            store, memory = f.session.store, f._memory
            p = f.authority.resolve(a.cookies[SESSION_COOKIE])
            repo, csrf = f.repository(p), f.authority.tokens(p)["create"]
            before = copy.deepcopy(memory.records)
            entered, release = asyncio.Event(), asyncio.Event()

            async def hook(stage: str, owner: str) -> None:
                target = "waiting:ownership" if failure == "cancel_waiting" else "locked:ownership"
                if stage == target:
                    entered.set()
                    try:
                        await release.wait()
                    except asyncio.CancelledError:
                        if failure != "cancel_swallowed":
                            raise

            store.fence.hook = hook
            task = asyncio.create_task(repo.create(1, (), csrf))
            await asyncio.wait_for(entered.wait(), 3)
            if failure.startswith("cancel"):
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
            else:
                if failure == "publication":
                    store.fail_on = "ownership"
                elif failure == "outage":
                    store.available = False
                elif failure == "expired":
                    clock.value += IDLE
                elif failure == "missing":
                    del store.sessions[p.session_key]
                elif failure in {"epoch", "inactive", "quarantined"}:
                    kwargs: dict[str, Any] = (
                        {"epoch": 1}
                        if failure == "epoch"
                        else {"active": False}
                        if failure == "inactive"
                        else {"quarantined": True}
                    )
                    store.controls[p.subject] = replace(store.controls[p.subject], **kwargs)
                elif failure == "generation":
                    memory.lifecycle[p.owner_id] = replace(
                        memory.lifecycle[p.owner_id], generation=2
                    )
                elif failure == "consent":
                    memory.lifecycle[p.owner_id] = replace(
                        memory.lifecycle[p.owner_id], consent_epoch=2
                    )
                else:
                    memory.lifecycle[p.owner_id] = replace(
                        memory.lifecycle[p.owner_id], active=False
                    )
                release.set()
                with pytest.raises(Denied):
                    await asyncio.wait_for(task, 3)
            assert memory.records == before
            assert not memory.cursors[p.owner_id]
            assert B_SENTINEL not in repr(repo)
            store.fence.hook = no_pause

    asyncio.run(run())


@pytest.mark.parametrize("invalidator", ["logout", "logout_all", "recovery", "mfa_reset", "rotate"])
def test_cached_handles_and_other_owner_after_invalidation(invalidator: str) -> None:
    async def run() -> None:
        async with harness() as (f, a, b, _):
            assert f.authority and f.session.store and f.session.events and f._memory
            store, memory = f.session.store, f._memory
            p = f.authority.resolve(a.cookies[SESSION_COOKIE])
            repo, csrf = f.repository(p), f.authority.tokens(p)
            if invalidator in {"recovery", "mfa_reset"}:
                await f.session.events.apply(f.session.events.sign("fictional-a", 1, invalidator))
            elif invalidator == "rotate":
                await login(f.session, a)
            else:
                await store.revoke(
                    a.cookies[SESSION_COOKIE],
                    await token(
                        a,
                        "POST:/_session/"
                        + ("logout-all" if invalidator == "logout_all" else "logout"),
                    ),
                    all_sessions=invalidator == "logout_all",
                )
            before = copy.deepcopy(memory.records)
            calls = [
                repo.read(UUID(int=101)),
                repo.count(),
                repo.page(),
                repo.join(UUID(int=101)),
                repo.nested(UUID(int=101), UUID(int=102)),
                repo.create(1, (), csrf["create"]),
                repo.update(UUID(int=101), 1, (), csrf["update"]),
                repo.delete(UUID(int=101), 1, csrf["delete"]),
                repo.batch((UUID(int=101),), 1, csrf["batch"]),
            ]
            for call in calls:
                with pytest.raises(Denied) as denied:
                    await call
                assert denied.value.status == 401
            assert memory.records == before
            assert (await b.get("/_ownership/records")).status_code == 200

    asyncio.run(run())
