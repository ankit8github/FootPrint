"""Ephemeral SQLite architecture model, NOT PostgreSQL/RLS or a deletion service.

Only random synthetic identities, package tuples and minimal control states.
There is no classification, HTTP, application persistence, migration, auth,
independent journal, source parser or implementation of Phase 6C-04 here.
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "backend/experiments/rule_packages/manifest.json"


class Rejected(Exception):
    pass


class Model:
    def __init__(self) -> None:
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
          CREATE TABLE packages(revision TEXT, manifest TEXT, worker TEXT, pure TEXT,
            PRIMARY KEY(revision,manifest,worker,pure));
          CREATE TABLE controls(owner TEXT PRIMARY KEY, epoch INTEGER NOT NULL,
            revision INTEGER NOT NULL, highwater INTEGER NOT NULL, state TEXT NOT NULL);
          CREATE TABLE collections(owner TEXT, collection TEXT, current INTEGER NOT NULL,
            PRIMARY KEY(owner,collection), FOREIGN KEY(owner) REFERENCES controls,
            FOREIGN KEY(owner,collection,current)
            REFERENCES generations(owner,collection,generation)
            DEFERRABLE INITIALLY DEFERRED);
          CREATE TABLE generations(owner TEXT, collection TEXT, generation INTEGER,
            revision TEXT NOT NULL, manifest TEXT NOT NULL,
            worker TEXT NOT NULL, pure TEXT NOT NULL,
            PRIMARY KEY(owner,collection,generation),
            FOREIGN KEY(owner,collection) REFERENCES collections,
            FOREIGN KEY(revision,manifest,worker,pure) REFERENCES packages);
          CREATE TRIGGER immutable_live_generation BEFORE UPDATE ON generations
            BEGIN SELECT RAISE(ABORT,'IMMUTABLE_LIVE_GENERATION'); END;
          CREATE TABLE sources(owner TEXT, collection TEXT, source TEXT, ordinal INTEGER NOT NULL,
            PRIMARY KEY(owner,collection,source),
            FOREIGN KEY(owner,collection) REFERENCES collections);
          CREATE TABLE observations(owner TEXT, collection TEXT, observation TEXT,
            source TEXT NOT NULL, row_index INTEGER NOT NULL,
            PRIMARY KEY(owner,collection,observation),
            FOREIGN KEY(owner,collection,source) REFERENCES sources);
          CREATE TABLE support(owner TEXT, collection TEXT, generation INTEGER, observation TEXT,
            PRIMARY KEY(owner,collection,generation,observation),
            FOREIGN KEY(owner,collection,generation) REFERENCES generations,
            FOREIGN KEY(owner,collection,observation) REFERENCES observations);
          -- Deliberately no FK from control receipts to deletable collections/sources.
          CREATE TABLE intents(owner TEXT, event TEXT, epoch INTEGER, revision INTEGER,
            state TEXT NOT NULL, PRIMARY KEY(owner,event));
          CREATE TABLE receipt_model(owner TEXT, event TEXT, operation TEXT, epoch INTEGER,
            revision INTEGER, state TEXT NOT NULL, PRIMARY KEY(owner,event));
        """)
        manifest = json.loads(MANIFEST.read_bytes())
        for revision, row in manifest["packages"].items():
            self.db.execute(
                "INSERT INTO packages VALUES (?,?,?,?)",
                (
                    revision,
                    "7485ac86c2cd9502e1414d68df7a930ae531b209706d44b8161a736ec7e24055",
                    row["worker_sha256"],
                    row["pure_sha256"],
                ),
            )

    def close(self) -> None:
        self.db.close()

    @contextmanager
    def transaction(self) -> Any:
        self.db.execute("BEGIN")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def package(self) -> tuple[str, str, str, str]:
        row = self.db.execute("SELECT * FROM packages WHERE revision='indexed-r1'").fetchone()
        assert row is not None
        return tuple(row)

    def initial(self, owner: str, collection: str, sources: tuple[str, ...]) -> None:
        with self.transaction():
            self.db.execute("INSERT INTO controls VALUES (?,1,0,1,'active')", (owner,))
            self.db.execute("INSERT INTO collections VALUES (?,?,1)", (owner, collection))
            self.db.execute(
                "INSERT INTO generations VALUES (?,?,1,?,?,?,?)",
                (owner, collection, *self.package()),
            )
            for ordinal, source in enumerate(sources):
                self.db.execute(
                    "INSERT INTO sources VALUES (?,?,?,?)", (owner, collection, source, ordinal)
                )
                # One observation per model source. This is not a classifier.
                self.db.execute(
                    "INSERT INTO observations VALUES (?,?,?,?,0)",
                    (owner, collection, source, source),
                )
                self.db.execute("INSERT INTO support VALUES (?,?,1,?)", (owner, collection, source))

    def snapshot(self) -> dict[str, list[tuple[Any, ...]]]:
        return {
            table: self.db.execute(f"SELECT * FROM {table} ORDER BY 1,2").fetchall()
            for table in (
                "controls",
                "collections",
                "generations",
                "sources",
                "observations",
                "support",
                "intents",
                "receipt_model",
            )
        }

    def fence(self, owner: str, event: str, withdrawal: bool = False) -> tuple[int, int]:
        with self.transaction():
            row = self.db.execute(
                "SELECT epoch,revision FROM controls WHERE owner=?", (owner,)
            ).fetchone()
            if row is None:
                raise Rejected("OWNER_UNKNOWN")
            epoch, revision = row[0] + int(withdrawal), row[1] + 1
            self.db.execute(
                "UPDATE controls SET epoch=?,revision=?,state='fenced' WHERE owner=?",
                (epoch, revision, owner),
            )
            self.db.execute(
                "INSERT INTO intents VALUES (?,?,?,?,'pending')", (owner, event, epoch, revision)
            )
        return epoch, revision

    def stale_writer(self, owner: str, epoch: int, revision: int) -> None:
        row = self.db.execute(
            "SELECT epoch,revision,state FROM controls WHERE owner=?", (owner,)
        ).fetchone()
        if row != (epoch, revision, "active"):
            raise Rejected("STALE_WRITER")

    def readable(self, owner: str) -> bool:
        row = self.db.execute("SELECT state FROM controls WHERE owner=?", (owner,)).fetchone()
        return bool(row == ("active",))

    def remove(
        self,
        owner: str,
        collection: str,
        source: str | None,
        event: str,
        fail_at: str = "",
        operation: str = "source",
    ) -> None:
        with self.transaction():
            intent = self.db.execute(
                "SELECT epoch,revision,state FROM intents WHERE owner=? AND event=?", (owner, event)
            ).fetchone()
            control = self.db.execute(
                "SELECT epoch,revision,highwater,state FROM controls WHERE owner=?", (owner,)
            ).fetchone()
            if not intent or not control or control[3] != "fenced" or intent[:2] != control[:2]:
                raise Rejected("INVALID_INTENT")
            if (
                self.db.execute(
                    "SELECT 1 FROM collections WHERE owner=? AND collection=?", (owner, collection)
                ).fetchone()
                is None
            ):
                raise Rejected("FOREIGN_COLLECTION")
            if (
                source is not None
                and self.db.execute(
                    "SELECT 1 FROM sources WHERE owner=? AND collection=? AND source=?",
                    (owner, collection, source),
                ).fetchone()
                is None
            ):
                raise Rejected("FOREIGN_SOURCE")
            self.db.execute(
                "DELETE FROM support WHERE owner=? AND collection=?", (owner, collection)
            )
            if fail_at == "support":
                raise Rejected("INJECTED_SUPPORT")
            # Deferred current pointer is repaired in the same model transaction.
            self.db.execute(
                "DELETE FROM generations WHERE owner=? AND collection=?", (owner, collection)
            )
            if source is not None:
                self.db.execute(
                    "DELETE FROM observations WHERE owner=? AND collection=? AND source=?",
                    (owner, collection, source),
                )
                self.db.execute(
                    "DELETE FROM sources WHERE owner=? AND collection=? AND source=?",
                    (owner, collection, source),
                )
                generation = control[2] + 1
                self.db.execute(
                    "INSERT INTO generations VALUES (?,?,?,?,?,?,?)",
                    (owner, collection, generation, *self.package()),
                )
                self.db.execute(
                    "UPDATE collections SET current=? WHERE owner=? AND collection=?",
                    (generation, owner, collection),
                )
                self.db.execute(
                    "INSERT INTO support SELECT owner,collection,?,observation FROM observations "
                    "WHERE owner=? AND collection=?",
                    (generation, owner, collection),
                )
                self.db.execute(
                    "UPDATE controls SET highwater=? WHERE owner=?", (generation, owner)
                )
            else:
                self.db.execute(
                    "DELETE FROM observations WHERE owner=? AND collection=?", (owner, collection)
                )
                self.db.execute(
                    "DELETE FROM sources WHERE owner=? AND collection=?", (owner, collection)
                )
                self.db.execute(
                    "DELETE FROM collections WHERE owner=? AND collection=?", (owner, collection)
                )
            if fail_at == "replacement":
                raise Rejected("INJECTED_REPLACEMENT")
            self.db.execute(
                "INSERT INTO receipt_model VALUES (?,?,?,?,?,'live_data_removed')",
                (owner, event, operation, intent[0], intent[1]),
            )
            self.db.execute(
                "UPDATE intents SET state='live_data_removed' WHERE owner=? AND event=?",
                (owner, event),
            )
            self.db.execute(
                "UPDATE controls SET state=? WHERE owner=?",
                ("active" if source else "disabled", owner),
            )
            if fail_at == "commit":
                raise Rejected("INJECTED_PRE_COMMIT")

    def acknowledge_model(self, owner: str, event: str) -> None:
        # Models only a state transition, NOT independent journal durability.
        self.db.execute(
            "UPDATE receipt_model SET state='completed' WHERE owner=? AND event=?", (owner, event)
        )
