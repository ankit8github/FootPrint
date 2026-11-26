"""Scoped architecture-model tests; no PostgreSQL/RLS/independent journal claim."""

import sqlite3
from collections.abc import Iterator
from uuid import uuid4

import pytest

from blocker_proofs.lifecycle_model import Model, Rejected


@pytest.fixture
def graph() -> Iterator[tuple[Model, list[str]]]:
    ids = [str(uuid4()) for _ in range(8)]
    model = Model()
    model.initial(ids[0], ids[1], (ids[2], ids[3]))
    model.initial(ids[4], ids[5], (ids[6], ids[7]))
    yield model, ids
    model.close()


@pytest.mark.parametrize("order", [(2, 3), (3, 2)])
def test_both_source_orders_and_bound_empty_generation(
    graph: tuple[Model, list[str]], order: tuple[int, int]
) -> None:
    model, ids = graph
    other = [row for row in model.snapshot()["support"] if row[0] == ids[4]]
    for index, source in enumerate(order):
        event = str(uuid4())
        model.fence(ids[0], event)
        assert not model.readable(ids[0])
        model.remove(ids[0], ids[1], ids[source], event)
        remaining = model.db.execute(
            "SELECT observation FROM support WHERE owner=?", (ids[0],)
        ).fetchall()
        assert remaining == ([(ids[order[1]],)] if index == 0 else [])
        binding = model.db.execute(
            "SELECT revision,manifest,worker,pure FROM generations WHERE owner=?", (ids[0],)
        ).fetchone()
        assert binding == model.package()
        assert (
            len(model.db.execute("SELECT * FROM generations WHERE owner=?", (ids[0],)).fetchall())
            == 1
        )
        assert [row for row in model.snapshot()["support"] if row[0] == ids[4]] == other
        assert model.readable(ids[0])
    assert model.db.execute(
        "SELECT current FROM collections WHERE owner=?", (ids[0],)
    ).fetchone() == (3,)
    assert model.db.execute("SELECT count(*) FROM sources WHERE owner=?", (ids[0],)).fetchone() == (
        0,
    )


@pytest.mark.parametrize("operation", ["collection", "account", "withdrawal", "expiry"])
def test_full_scope_purge_retains_no_generation_payload(
    graph: tuple[Model, list[str]], operation: str
) -> None:
    model, ids = graph
    event = str(uuid4())
    model.fence(ids[0], event, withdrawal=operation in ("withdrawal", "expiry"))
    model.remove(ids[0], ids[1], None, event, operation=operation)
    for table in ("collections", "generations", "sources", "observations", "support"):
        assert model.db.execute(
            f"SELECT count(*) FROM {table} WHERE owner=?", (ids[0],)
        ).fetchone() == (0,)
        assert (
            model.db.execute(f"SELECT count(*) FROM {table} WHERE owner=?", (ids[4],)).fetchone()[0]
            > 0
        )
    receipt = model.db.execute(
        "SELECT state FROM receipt_model WHERE owner=?", (ids[0],)
    ).fetchone()
    assert receipt == ("live_data_removed",)
    model.acknowledge_model(ids[0], event)
    model.acknowledge_model(ids[0], event)
    assert model.db.execute(
        "SELECT state FROM receipt_model WHERE owner=?", (ids[0],)
    ).fetchone() == ("completed",)
    # Model receipt has no source observations, package/result digests or support.
    assert {r[1] for r in model.db.execute("PRAGMA table_info(receipt_model)")} == {
        "owner",
        "event",
        "operation",
        "epoch",
        "revision",
        "state",
    }


@pytest.mark.parametrize("point", ["support", "replacement", "commit"])
def test_failure_rolls_back_payload_but_retains_prior_fence(
    graph: tuple[Model, list[str]], point: str
) -> None:
    model, ids = graph
    event = str(uuid4())
    model.fence(ids[0], event)
    fenced = model.snapshot()
    with pytest.raises(Rejected, match="^INJECTED_"):
        model.remove(ids[0], ids[1], ids[2], event, fail_at=point)
    assert model.snapshot() == fenced
    assert not model.readable(ids[0])


@pytest.mark.parametrize("withdrawal", [False, True])
def test_old_writer_rejected_after_fence(graph: tuple[Model, list[str]], withdrawal: bool) -> None:
    model, ids = graph
    model.stale_writer(ids[0], 1, 0)
    model.fence(ids[0], str(uuid4()), withdrawal)
    with pytest.raises(Rejected, match="^STALE_WRITER$"):
        model.stale_writer(ids[0], 1, 0)


@pytest.mark.parametrize("foreign", ["collection", "source"])
def test_foreign_target_does_not_change_graph(graph: tuple[Model, list[str]], foreign: str) -> None:
    model, ids = graph
    event = str(uuid4())
    model.fence(ids[0], event)
    before = model.snapshot()
    with pytest.raises(Rejected, match="^FOREIGN_"):
        model.remove(
            ids[0],
            ids[5] if foreign == "collection" else ids[1],
            ids[6] if foreign == "source" else ids[2],
            event,
        )
    assert model.snapshot() == before


@pytest.mark.parametrize("column", ["manifest", "worker", "pure", "revision"])
def test_live_generation_tuple_cannot_be_mutated(
    graph: tuple[Model, list[str]], column: str
) -> None:
    model, ids = graph
    with pytest.raises(sqlite3.IntegrityError, match="IMMUTABLE_LIVE_GENERATION"):
        model.db.execute(f"UPDATE generations SET {column}='changed' WHERE owner=?", (ids[0],))


def test_orphan_support_and_unbound_generation_rejected(graph: tuple[Model, list[str]]) -> None:
    model, ids = graph
    with pytest.raises(sqlite3.IntegrityError):
        model.db.execute("INSERT INTO support VALUES (?,?,1,?)", (ids[0], ids[1], ids[6]))
    with pytest.raises(sqlite3.IntegrityError):
        model.db.execute(
            "INSERT INTO generations VALUES (?,?,2,NULL,NULL,NULL,NULL)", (ids[0], ids[1])
        )
    with pytest.raises(sqlite3.IntegrityError):
        model.db.execute(
            "INSERT INTO generations VALUES (?,?,2,?,?,?,?)", (ids[0], ids[1], *["forged"] * 4)
        )
    with pytest.raises(sqlite3.IntegrityError):
        model.db.execute("DELETE FROM observations WHERE owner=?", (ids[0],))


def test_missing_intent_fails_closed(graph: tuple[Model, list[str]]) -> None:
    model, ids = graph
    before = model.snapshot()
    with pytest.raises(Rejected, match="^INVALID_INTENT$"):
        model.remove(ids[0], ids[1], ids[2], str(uuid4()))
    assert model.snapshot() == before
