"""Barrier-controlled validation versus revocation/consent, no durable-lock claim."""

import asyncio
import copy
from dataclasses import replace

import pytest
from admission_test_support import envelope, harness
from session_test_support import token

from experiments.admission_fixture import RECEIPT
from experiments.minimized_contract import AdmissionEnvelope
from experiments.session_fixture import SESSION_COOKIE
from experiments.session_store import IDLE, Denied


@pytest.mark.parametrize("subject", ["fictional-a", "fictional-b"])
@pytest.mark.parametrize(
    "invalidator", ["logout", "logout_all", "recovery", "mfa_reset", "consent", "revision"]
)
@pytest.mark.parametrize("first", ["admission", "invalidation"])
def test_both_owner_fence_orders(subject: str, invalidator: str, first: str) -> None:
    async def run() -> None:
        async with harness() as (f, a, b, _):
            assert f.authority and f.session.store and f.session.events
            client = a if subject == "fictional-a" else b
            principal = f.authority.resolve(client.cookies[SESSION_COOKIE])
            store, events = f.session.store, f.session.events
            csrf = f.csrf(principal)
            data = AdmissionEnvelope.model_validate(envelope())
            other = {k: v for k, v in f.controls.items() if k != principal.owner_id}
            logout_csrf = await token(
                client,
                "POST:/_session/" + ("logout-all" if invalidator == "logout_all" else "logout"),
            )
            handle = client.cookies[SESSION_COOKIE]
            action = "event" if invalidator in {"recovery", "mfa_reset"} else invalidator
            locked, release, prelock, proceed, queued = (asyncio.Event() for _ in range(5))

            async def hook(stage: str, owner: str) -> None:
                if owner != subject:
                    return
                if first == "invalidation" and stage == "waiting:admission":
                    prelock.set()
                    await proceed.wait()
                held = "admission" if first == "admission" else action
                waiting = action if first == "admission" else "admission"
                if stage == "locked:" + held:
                    locked.set()
                    await release.wait()
                if stage == "waiting:" + waiting:
                    queued.set()

            async def invalidate() -> None:
                if invalidator in {"consent", "revision"}:
                    async with store.fence.hold(subject, action):
                        await store.fence.hook("locked:" + action, subject)
                        state = f.controls[principal.owner_id]
                        f.controls[principal.owner_id] = (
                            replace(state, granted=False, epoch=2)
                            if invalidator == "consent"
                            else replace(state, revision=2)
                        )
                elif action == "event":
                    await events.apply(events.sign(subject, 1, invalidator))
                else:
                    await store.revoke(
                        handle, logout_csrf, all_sessions=invalidator == "logout_all"
                    )

            store.fence.hook = hook
            admission = asyncio.create_task(f.validate(principal, data, csrf))
            if first == "invalidation":
                await asyncio.wait_for(prelock.wait(), 3)
                invalidation = asyncio.create_task(invalidate())
                await asyncio.wait_for(locked.wait(), 3)
                release.set()
                await asyncio.wait_for(invalidation, 3)
                proceed.set()
                with pytest.raises(Denied):
                    await asyncio.wait_for(admission, 3)
            else:
                await asyncio.wait_for(locked.wait(), 3)
                invalidation = asyncio.create_task(invalidate())
                await asyncio.wait_for(queued.wait(), 3)
                release.set()
                receipt, _ = await asyncio.wait_for(asyncio.gather(admission, invalidation), 3)
                assert receipt == RECEIPT
            assert {k: v for k, v in f.controls.items() if k != principal.owner_id} == other
            with pytest.raises(Denied):
                await f.validate(principal, data, csrf)

    asyncio.run(run())


@pytest.mark.parametrize(
    "failure",
    [
        "cancel",
        "cancel_swallowed",
        "expired",
        "epoch",
        "consent_epoch",
        "revision",
        "withdraw",
        "corrupt",
        "missing",
        "outage",
        "registry",
        "token",
    ],
)
def test_post_fence_guard_never_returns_stale_receipt(failure: str) -> None:
    async def run() -> None:
        async with harness() as (f, a, _, clock):
            assert f.authority and f.session.store
            principal = f.authority.resolve(a.cookies[SESSION_COOKIE])
            store = f.session.store
            csrf = f.csrf(principal)
            before = copy.deepcopy(f.controls)
            entered, release = asyncio.Event(), asyncio.Event()

            async def hook(stage: str, owner: str) -> None:
                if stage != "locked:admission":
                    return
                entered.set()
                if failure in {"cancel", "cancel_swallowed"}:
                    try:
                        await release.wait()
                    except asyncio.CancelledError:
                        if failure == "cancel":
                            raise
                elif failure == "expired":
                    clock.value += IDLE
                elif failure == "epoch":
                    store.controls[owner] = replace(store.controls[owner], epoch=1)
                elif failure == "consent_epoch":
                    f.controls[principal.owner_id] = replace(before[principal.owner_id], epoch=2)
                elif failure == "revision":
                    f.controls[principal.owner_id] = replace(before[principal.owner_id], revision=2)
                elif failure == "withdraw":
                    f.controls[principal.owner_id] = replace(
                        before[principal.owner_id], granted=False
                    )
                elif failure == "corrupt":
                    f.controls[principal.owner_id] = replace(before[principal.owner_id], granted=1)  # type: ignore[arg-type]
                elif failure == "missing":
                    store.sessions.pop(principal.session_key)
                elif failure == "outage":
                    store.available = False
                elif failure == "registry":
                    f.registry = None
                elif failure == "token":
                    store.sessions[principal.session_key] = replace(
                        store.sessions[principal.session_key], tokens=()
                    )

            store.fence.hook = hook
            task = asyncio.create_task(
                f.validate(principal, AdmissionEnvelope.model_validate(envelope()), csrf)
            )
            await asyncio.wait_for(entered.wait(), 3)
            if failure.startswith("cancel"):
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await asyncio.wait_for(task, 3)
            else:
                with pytest.raises(Denied):
                    await asyncio.wait_for(task, 3)
            # No admitted batch map, durable write or receipt publication exists.
            assert not hasattr(f, "batches")
            assert {k: v for k, v in f.controls.items() if k != principal.owner_id} == {
                k: v for k, v in before.items() if k != principal.owner_id
            }

    asyncio.run(run())
