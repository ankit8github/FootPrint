"""Barrier-controlled in-process ordering, not database/distributed lock tests."""

import asyncio
import copy

import pytest
from session_test_support import authorize, harness, login, pending, token

from experiments.session_store import Denied


@pytest.mark.parametrize("invalidator", ["logout", "logout_all", "event"])
@pytest.mark.parametrize("first", ["marker", "invalidator"])
def test_both_owner_lock_orders(invalidator: str, first: str) -> None:
    async def run() -> None:
        async with harness() as (f, c, _, _):
            handle = await login(f, c)
            assert f.store and f.events
            store, events = f.store, f.events
            marker_csrf = await token(c)
            logout_csrf = await token(
                c, "POST:/_session/" + ("logout-all" if invalidator == "logout_all" else "logout")
            )
            entered, release, queued = asyncio.Event(), asyncio.Event(), asyncio.Event()

            async def hook(stage: str, owner: str) -> None:
                held = "marker" if first == "marker" else invalidator
                waiting = invalidator if first == "marker" else "marker"
                if stage == "locked:" + held:
                    entered.set()
                    await release.wait()
                if stage == "waiting:" + waiting:
                    queued.set()

            store.fence.hook = hook

            async def mutate() -> None:
                await store.marker(handle, "POST:/_session/marker", marker_csrf)

            async def revoke() -> None:
                if invalidator == "event":
                    await events.apply(events.sign("fictional-a", 1))
                else:
                    await store.revoke(
                        handle, logout_csrf, all_sessions=invalidator == "logout_all"
                    )

            # For invalidator-first, take the mutation's initial snapshot before the
            # invalidator quarantines the owner, then pause at its lock boundary.
            if first == "invalidator":
                original_hook = store.fence.hook
                marker_waiting, let_marker_wait = asyncio.Event(), asyncio.Event()

                async def prelock(stage: str, owner: str) -> None:
                    if stage == "waiting:marker":
                        marker_waiting.set()
                        await let_marker_wait.wait()
                    await original_hook(stage, owner)

                store.fence.hook = prelock
                mt = asyncio.create_task(mutate())
                await asyncio.wait_for(marker_waiting.wait(), 1)
                rt = asyncio.create_task(revoke())
                await asyncio.wait_for(entered.wait(), 1)
                release.set()
                await asyncio.wait_for(rt, 1)
                let_marker_wait.set()
                with pytest.raises(Denied):
                    await asyncio.wait_for(mt, 1)
                assert store.controls["fictional-a"].markers == 0
            else:
                mt = asyncio.create_task(mutate())
                await asyncio.wait_for(entered.wait(), 1)
                rt = asyncio.create_task(revoke())
                await asyncio.wait_for(queued.wait(), 1)
                release.set()
                await asyncio.wait_for(asyncio.gather(mt, rt), 1)
                assert store.controls["fictional-a"].markers == 1
            store.fence.hook = no_pause
            with pytest.raises(Denied):
                await store.marker(handle, "POST:/_session/marker", marker_csrf)
            with pytest.raises(Denied):
                store.lookup(handle)

    asyncio.run(run())


async def no_pause(stage: str, owner: str) -> None:
    pass


@pytest.mark.parametrize("action", ["marker", "logout", "logout_all", "event"])
@pytest.mark.parametrize("failure", ["cancel", "store_failure"])
def test_failure_and_cancellation_under_fence(action: str, failure: str) -> None:
    async def run() -> None:
        async with harness() as (f, c, _, _):
            handle = await login(f, c)
            assert f.store and f.events
            store = f.store
            csrf_action = "POST:/_session/" + ("logout-all" if action == "logout_all" else action)
            csrf = await token(c, csrf_action if action != "event" else "POST:/_session/logout")
            snapshot = copy.deepcopy(store.sessions)
            entered, release = asyncio.Event(), asyncio.Event()

            async def hook(stage: str, owner: str) -> None:
                if stage == "locked:" + action:
                    entered.set()
                    await release.wait()

            store.fence.hook = hook

            async def operation() -> None:
                assert f.events
                if action == "event":
                    await f.events.apply(f.events.sign("fictional-a", 1))
                elif action == "marker":
                    await store.marker(handle, "POST:/_session/marker", csrf)
                else:
                    await store.revoke(handle, csrf, all_sessions=action == "logout_all")

            task = asyncio.create_task(operation())
            await asyncio.wait_for(entered.wait(), 1)
            if failure == "cancel":
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
            else:
                store.fail_on = action
                release.set()
                with pytest.raises(Denied):
                    await asyncio.wait_for(task, 1)
                store.fail_on = None
            assert store.sessions == snapshot and store.controls["fictional-a"].markers == 0
            store.fence.hook = no_pause
            if action == "marker":
                assert store.lookup(handle)
            else:
                assert store.controls["fictional-a"].quarantined
                with pytest.raises(Denied):
                    store.lookup(handle)
                with pytest.raises(Denied):
                    await store.marker(handle, "POST:/_session/marker", csrf)

    asyncio.run(run())


@pytest.mark.parametrize("change", ["epoch", "expiry", "inactive", "missing", "unavailable"])
def test_final_marker_recheck(change: str) -> None:
    async def run() -> None:
        async with harness() as (f, c, clock, _):
            handle = await login(f, c)
            csrf = await token(c)
            assert f.store
            store = f.store
            from dataclasses import replace

            async def hook(stage: str, owner: str) -> None:
                if stage != "locked:marker":
                    return
                if change == "epoch":
                    store.controls[owner] = replace(store.controls[owner], epoch=1)
                if change == "expiry":
                    clock.value += 1800
                if change == "inactive":
                    store.controls[owner] = replace(store.controls[owner], active=False)
                if change == "missing":
                    store.sessions.clear()
                if change == "unavailable":
                    store.available = False

            store.fence.hook = hook
            with pytest.raises(Denied):
                await store.marker(handle, "POST:/_session/marker", csrf)
            assert store.controls["fictional-a"].markers == 0

    asyncio.run(run())


def test_recovery_during_oidc_cannot_issue_stale_session() -> None:
    async def run() -> None:
        async with harness() as (f, c, _, _):
            await login(f, c)
            start = await pending(f, c)
            assert f.events and f.store
            await f.events.apply(f.events.sign("fictional-a", 1))
            response = await authorize(f, c, start)
            assert response.headers["location"] == "/_spike/rejected"
            assert not f.store.sessions

    asyncio.run(run())


def test_cancelled_revocation_before_lock_does_not_claim_success_or_change_state() -> None:
    async def run() -> None:
        async with harness() as (f, c, _, _):
            handle = await login(f, c)
            csrf = await token(c, "POST:/_session/logout")
            assert f.store
            store = f.store
            snapshot = copy.deepcopy((store.sessions, store.controls))
            entered = asyncio.Event()

            async def hook(stage: str, owner: str) -> None:
                if stage == "waiting:logout":
                    entered.set()

            store.fence.hook = hook
            async with store.fence.locks["fictional-a"]:
                task = asyncio.create_task(store.revoke(handle, csrf, all_sessions=False))
                await asyncio.wait_for(entered.wait(), 1)
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
            assert snapshot == (store.sessions, store.controls) and store.lookup(handle)

    asyncio.run(run())


def test_same_action_csrf_cannot_commit_twice_concurrently() -> None:
    async def run() -> None:
        async with harness() as (f, c, _, _):
            handle = await login(f, c)
            csrf = await token(c)
            assert f.store
            store = f.store
            entered, release = asyncio.Event(), asyncio.Event()

            async def hook(stage: str, owner: str) -> None:
                if stage == "locked:marker":
                    entered.set()
                    await release.wait()

            store.fence.hook = hook
            first = asyncio.create_task(store.marker(handle, "POST:/_session/marker", csrf))
            await asyncio.wait_for(entered.wait(), 1)
            second = asyncio.create_task(store.marker(handle, "POST:/_session/marker", csrf))
            release.set()
            results = await asyncio.wait_for(
                asyncio.gather(first, second, return_exceptions=True), 1
            )
            assert sum(isinstance(r, Denied) for r in results) == 1
            assert store.controls["fictional-a"].markers == 1

    asyncio.run(run())
