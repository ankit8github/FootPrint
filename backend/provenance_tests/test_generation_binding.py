"""Direct SQL through restricted logins; no provenance adapter imports or execution."""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError

from db_tests.conftest import insert
from db_tests.test_tenant_security import denied
from experiments.provenance_schema import (
    ADDED_TABLES,
    migrate_candidate,
    require_candidate_database,
)
from experiments.tenant_db import migrate, owner_transaction, require_disposable, set_owner
from experiments.tenant_db import test_engine as make_engine

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "backend/experiments/rule_packages/manifest.json"
MANIFEST = json.loads(MANIFEST_PATH.read_bytes())
MANIFEST_HASH = hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
PACKAGE = MANIFEST["packages"]["indexed-r1"]
Pair = tuple[dict[str, Any], dict[str, Any]]
BINDINGS = "fp6_data.generation_implementations"
PACKAGES = "fp6_reference.implementation_packages"


def row(tenant: dict[str, Any], generation: int = 999) -> dict[str, Any]:
    return {
        "owner_id": tenant["owner_id"],
        "collection_id": tenant["collection_id"],
        "generation": generation,
        "package_revision": "indexed-r1",
        "manifest_sha256": MANIFEST_HASH,
        "worker_sha256": PACKAGE["worker_sha256"],
        "pure_sha256": PACKAGE["pure_sha256"],
    }


def insert_sql(table: str, values: dict[str, Any]) -> str:
    return f"INSERT INTO {table} ({','.join(values)}) VALUES ({','.join(':' + k for k in values)})"


def test_sql_pins_match_the_unchanged_manifest() -> None:
    assert MANIFEST_HASH == "7485ac86c2cd9502e1414d68df7a930ae531b209706d44b8161a736ec7e24055"
    sql = (ROOT / "backend/provenance_migrations/versions/c03_comp01_0001.sql").read_text(
        encoding="utf-8"
    )
    for revision, package in MANIFEST["packages"].items():
        assert revision in sql
        assert package["worker_sha256"] in sql
        assert package["pure_sha256"] in sql
    assert MANIFEST_HASH in sql
    assert "SECURITY DEFINER" not in sql
    assert "ON DELETE CASCADE" not in sql


def test_catalog_controls_and_no_new_definer(bootstrap: Engine, runtime: Engine) -> None:
    with bootstrap.connect() as conn:
        require_candidate_database(conn)
        with pytest.raises(RuntimeError, match="Unexpected table"):
            require_disposable(conn)  # Legacy guard still rejects candidate objects.
        for table in (BINDINGS, PACKAGES):
            assert tuple(
                conn.execute(
                    text(
                        "SELECT relrowsecurity,relforcerowsecurity,pg_get_userbyid(relowner) "
                        "FROM pg_class WHERE oid=CAST(:table AS regclass)"
                    ),
                    {"table": table},
                ).one()
            ) == (True, True, "fp6_owner")
            for privilege in ("UPDATE", "DELETE", "TRUNCATE", "TRIGGER", "REFERENCES"):
                assert not conn.scalar(
                    text("SELECT has_table_privilege('fp6_runtime_login',:table,:privilege)"),
                    {"table": table, "privilege": privilege},
                )
        definitions = conn.exec_driver_sql(
            "SELECT conname,convalidated,condeferrable,condeferred,pg_get_constraintdef(oid) "
            "FROM pg_constraint WHERE conname IN "
            "('bound_generation','implementation_required','exact_package') ORDER BY conname"
        ).all()
        assert len(definitions) == 3 and all(r.convalidated for r in definitions)
        assert definitions[0].conname == "bound_generation"
        assert definitions[0].condeferrable and definitions[0].condeferred
        assert definitions[2].conname == "implementation_required"
        assert not definitions[2].condeferrable
        assert conn.execute(
            text(
                "SELECT n.nspname,p.proname FROM pg_proc p JOIN pg_namespace n "
                "ON n.oid=p.pronamespace WHERE n.nspname LIKE 'fp6_%' AND p.prosecdef"
            )
        ).all() == [("fp6_auth", "lookup_session")]
        policies = conn.exec_driver_sql(
            "SELECT roles,qual,with_check FROM pg_policies "
            "WHERE schemaname='fp6_data' AND tablename='generation_implementations'"
        ).one()
        assert policies.roles == ["fp6_runtime"]
        assert policies.qual == policies.with_check
        assert "owner_id = fp6_context.owner_id()" in policies.qual
        for role in ("fp6_runtime_login", "fp6_auth_login", "fp6_restore"):
            for table_parts in ADDED_TABLES:
                if table_parts[1] != "provenance_alembic_version" and role == "fp6_runtime_login":
                    continue
                assert not conn.scalar(
                    text("SELECT has_table_privilege(:role,:table,'SELECT')"),
                    {"role": role, "table": ".".join(table_parts)},
                )
    with runtime.connect() as conn:
        packages = conn.exec_driver_sql(f"SELECT * FROM {PACKAGES}").mappings().all()
        assert len(packages) == 2
        for package in packages:
            pinned = MANIFEST["packages"][package["package_revision"]]
            assert package["manifest_sha256"] == MANIFEST_HASH
            assert package["worker_sha256"] == pinned["worker_sha256"]
            assert package["pure_sha256"] == pinned["pure_sha256"]


def test_zero_finding_generation_is_bound_immediately(runtime: Engine, pair: Pair) -> None:
    own, _ = pair
    with runtime.connect() as conn:
        transaction = conn.begin()
        try:
            set_owner(conn, own["owner_id"])
            values = row(own)
            insert(
                conn,
                "fp6_data.generations",
                {k: values[k] for k in ("owner_id", "collection_id", "generation")},
            )
            assert (
                dict(
                    conn.execute(text(f"SELECT * FROM {BINDINGS} WHERE generation=999"))
                    .mappings()
                    .one()
                )
                == values
            )
            assert (
                conn.scalar(text("SELECT count(*) FROM fp6_data.findings WHERE generation=999"))
                == 0
            )
            conn.exec_driver_sql("UPDATE fp6_data.collections SET current_generation=999")
            conn.exec_driver_sql("SET CONSTRAINTS ALL IMMEDIATE")
        finally:
            transaction.rollback()


def test_atomic_visibility(runtime: Engine, pair: Pair) -> None:
    own, _ = pair
    other = make_engine("fp6_runtime_login")
    try:
        with runtime.connect() as writer:
            transaction = writer.begin()
            set_owner(writer, own["owner_id"])
            writer.execute(
                text("INSERT INTO fp6_data.generations VALUES (:owner_id,:collection_id,998)"), own
            )
            with owner_transaction(other, own["owner_id"]) as reader:
                assert (
                    reader.scalar(text(f"SELECT count(*) FROM {BINDINGS} WHERE generation=998"))
                    == 0
                )
                assert (
                    reader.scalar(
                        text("SELECT count(*) FROM fp6_data.generations WHERE generation=998")
                    )
                    == 0
                )
            transaction.commit()
        with owner_transaction(other, own["owner_id"]) as reader:
            assert reader.scalar(text(f"SELECT count(*) FROM {BINDINGS} WHERE generation=998")) == 1
            assert (
                reader.scalar(
                    text("SELECT count(*) FROM fp6_data.generations WHERE generation=998")
                )
                == 1
            )
    finally:
        other.dispose()


def test_foreign_read_count_join_and_insert(runtime: Engine, pair: Pair) -> None:
    own, foreign = pair
    with owner_transaction(runtime, own["owner_id"]) as conn:
        assert conn.scalar(text("SELECT current_user")) == "fp6_runtime_login"
        assert set(conn.scalars(text(f"SELECT owner_id FROM {BINDINGS}"))) == {own["owner_id"]}
        assert (
            conn.scalar(
                text(
                    f"SELECT count(*) FROM {BINDINGS} b JOIN fp6_data.generations g "
                    "USING(owner_id,collection_id,generation) WHERE b.owner_id=:owner"
                ),
                {"owner": foreign["owner_id"]},
            )
            == 0
        )
    values = row(foreign)
    denied(runtime, own["owner_id"], insert_sql(BINDINGS, values), values, ("42501",))


@pytest.mark.parametrize(
    "patch,code",
    [
        ({"collection_id": "new"}, "23503"),
        ({"generation": 997}, "23503"),
        ({"package_revision": "missing"}, "23514"),
        ({"package_revision": ""}, "23514"),
        ({"package_revision": "historical-v1"}, "23514"),
        ({"manifest_sha256": "0" * 64}, "23503"),
        ({"worker_sha256": "0" * 64}, "23503"),
        ({"worker_sha256": "malformed"}, "23503"),
        ({"worker_sha256": "0" * 65}, "22001"),
        ({"pure_sha256": "0" * 64}, "23503"),
        ({"worker_sha256": MANIFEST["packages"]["historical-v1"]["worker_sha256"]}, "23503"),
        ({"package_revision": None}, "23502"),
        ({"manifest_sha256": None}, "23502"),
        ({"owner_id": "invalid-uuid"}, "22P02"),
        ({"generation": 0}, "23514"),
        ({"generation": 1000001}, "23514"),
        ({"generation": 1}, "23505"),
    ],
)
def test_invalid_binding(runtime: Engine, pair: Pair, patch: dict[str, Any], code: str) -> None:
    own, _ = pair
    values = {**row(own), **patch}
    if values["collection_id"] == "new":
        values["collection_id"] = uuid4()
    denied(runtime, own["owner_id"], insert_sql(BINDINGS, values), values, (code,))
    with owner_transaction(runtime, own["owner_id"]) as conn:
        assert conn.scalar(text(f"SELECT count(*) FROM {BINDINGS} WHERE generation=999")) == 0


@pytest.mark.parametrize("column", ["owner_id", "collection_id", "generation"])
def test_generation_identity_cannot_move(runtime: Engine, pair: Pair, column: str) -> None:
    own, _ = pair
    denied(
        runtime,
        own["owner_id"],
        f"UPDATE fp6_data.generations SET {column}=:value WHERE generation=2",
        {"value": 999 if column == "generation" else uuid4()},
        ("42501",),
    )


def test_own_owner_cannot_reference_foreign_collection(runtime: Engine, pair: Pair) -> None:
    own, foreign = pair
    values = {**row(own), "collection_id": foreign["collection_id"]}
    denied(runtime, own["owner_id"], insert_sql(BINDINGS, values), values, ("23503",))


@pytest.mark.parametrize("table", [BINDINGS, PACKAGES])
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE", "TRUNCATE"])
def test_runtime_mutation_denied(runtime: Engine, pair: Pair, table: str, operation: str) -> None:
    own, _ = pair
    sql = (
        f"UPDATE {table} SET package_revision=package_revision"
        if operation == "UPDATE"
        else f"DELETE FROM {table}"
        if operation == "DELETE"
        else f"TRUNCATE {table}"
    )
    denied(runtime, own["owner_id"], sql, codes=("42501",))


@pytest.mark.parametrize("operation", ["UPDATE", "DELETE", "TRUNCATE"])
def test_registry_immutable_even_for_privileged_test_controller(
    bootstrap: Engine, operation: str
) -> None:
    sql = (
        f"UPDATE {PACKAGES} SET worker_sha256=repeat('0',64)"
        if operation == "UPDATE"
        else f"DELETE FROM {PACKAGES}"
        if operation == "DELETE"
        else f"TRUNCATE {PACKAGES}"
    )
    # Privileged positive integrity test; NOT evidence of restricted-role isolation.
    with pytest.raises(DBAPIError) as error, bootstrap.begin() as conn:
        conn.exec_driver_sql(sql)
    # Referenced table TRUNCATE is rejected by FK before its trigger (0A000).
    assert error.value.orig.sqlstate in ("42501", "0A000")  # type: ignore[union-attr]


@pytest.mark.parametrize(
    "field", ["package_revision", "manifest_sha256", "worker_sha256", "pure_sha256"]
)
def test_checked_registry_rejects_changed_identity(bootstrap: Engine, field: str) -> None:
    values = {
        k: v
        for k, v in row({"owner_id": uuid4(), "collection_id": uuid4()}).items()
        if k not in ("owner_id", "collection_id", "generation")
    }
    values[field] = "unknown" if field == "package_revision" else "0" * 64
    # PostgreSQL evaluates row CHECKs before unique-index insertion, so the
    # recognized revision with a changed hash must fail 23514, not just 23505.
    with pytest.raises(DBAPIError) as error, bootstrap.begin() as conn:
        insert(conn, PACKAGES, values)
    assert error.value.orig.sqlstate == "23514"  # type: ignore[union-attr]


@pytest.mark.parametrize("context", ["missing", "malformed", "wrong-xid"])
def test_new_binding_context_fails_closed(runtime: Engine, pair: Pair, context: str) -> None:
    own, _ = pair
    with runtime.begin() as conn:
        if context == "malformed":
            conn.exec_driver_sql("SET LOCAL app.owner_id='invalid'")
        elif context == "wrong-xid":
            conn.execute(
                text("SELECT set_config('app.owner_id',:owner,true)"),
                {"owner": str(own["owner_id"])},
            )
            conn.exec_driver_sql("SET LOCAL app.owner_xid='0'")
        assert conn.scalar(text(f"SELECT count(*) FROM {BINDINGS}")) == 0
        with pytest.raises(DBAPIError) as error:
            insert(conn, BINDINGS, row(own))
        assert error.value.orig.sqlstate == "42501"  # type: ignore[union-attr]


def test_generation_without_trigger_still_requires_binding(bootstrap: Engine, pair: Pair) -> None:
    own, _ = pair
    with pytest.raises(DBAPIError) as error, bootstrap.begin() as conn:
        # Transactional fault injection only; no trigger weakening survives failure.
        conn.exec_driver_sql("ALTER TABLE fp6_data.generations DISABLE TRIGGER bind_implementation")
        conn.execute(
            text("INSERT INTO fp6_data.generations VALUES (:owner_id,:collection_id,996)"), own
        )
    assert error.value.orig.sqlstate == "23503"  # type: ignore[union-attr]


@pytest.mark.parametrize("second", ["insert", "delete-reinsert"])
@pytest.mark.parametrize("isolation", ["READ COMMITTED", "REPEATABLE READ"])
def test_delete_reinsert_race_preserves_binding(
    runtime: Engine, pair: Pair, second: str, isolation: str
) -> None:
    own, _ = pair
    barrier = Barrier(2)

    def attempt(operation: str) -> str:
        engine = make_engine("fp6_runtime_login")
        try:
            with engine.connect().execution_options(isolation_level=isolation) as conn:
                try:
                    with conn.begin():
                        set_owner(conn, own["owner_id"])
                        conn.exec_driver_sql("SET LOCAL lock_timeout='2s'")
                        conn.exec_driver_sql("SET LOCAL statement_timeout='4s'")
                        barrier.wait(timeout=5)
                        if operation.startswith("delete"):
                            conn.exec_driver_sql(
                                "DELETE FROM fp6_data.generations WHERE generation=2"
                            )
                        if operation != "delete":
                            conn.execute(
                                text(
                                    "INSERT INTO fp6_data.generations "
                                    "VALUES (:owner_id,:collection_id,2)"
                                ),
                                own,
                            )
                except DBAPIError as error:
                    return str(error.orig.sqlstate)  # type: ignore[union-attr]
            return "UNEXPECTED_SUCCESS"
        finally:
            engine.dispose()

    with owner_transaction(runtime, own["owner_id"]) as conn:
        before = conn.exec_driver_sql(f"SELECT * FROM {BINDINGS} ORDER BY generation").all()
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(attempt, "delete")
        other = pool.submit(attempt, second)
        first_code = first.result(timeout=12)
        other_code = other.result(timeout=12)
        assert first_code in ("23503", "40001")
        assert other_code in ("23505", "40001")
        print(f"RACE {isolation}/{second}: delete={first_code}, contender={other_code}")
    with owner_transaction(runtime, own["owner_id"]) as conn:
        assert conn.exec_driver_sql(f"SELECT * FROM {BINDINGS} ORDER BY generation").all() == before
        assert (
            conn.scalar(text("SELECT count(*) FROM fp6_data.generations WHERE generation=2")) == 1
        )


@pytest.mark.parametrize(
    "object_sql",
    [
        "CREATE TABLE fp6_data.unrecognized (id integer)",
        "CREATE VIEW fp6_data.unrecognized AS SELECT 1",
        "CREATE FUNCTION fp6_context.unrecognized() RETURNS int LANGUAGE sql AS 'SELECT 1'",
        "CREATE FUNCTION fp6_context.bind_implementation(int) "
        "RETURNS int LANGUAGE sql AS 'SELECT 1'",
        "CREATE SCHEMA unexpected",
    ],
)
def test_candidate_guard_rejects_additional_objects(bootstrap: Engine, object_sql: str) -> None:
    with bootstrap.connect() as conn:
        transaction = conn.begin()
        try:
            conn.exec_driver_sql(object_sql)
            with pytest.raises(RuntimeError, match="Unexpected"):
                require_candidate_database(conn)
        finally:
            transaction.rollback()


def test_nonempty_downgrade_is_fail_closed() -> None:
    migrator = make_engine("fp6_migration_login")
    try:
        with pytest.raises(DBAPIError) as error:
            migrate_candidate(migrator, down=True)
        assert error.value.orig.sqlstate == "23514"  # type: ignore[union-attr]
    finally:
        migrator.dispose()


def test_old_migration_guard_cannot_erase_candidate() -> None:
    migrator = make_engine("fp6_migration_login")
    try:
        with pytest.raises(RuntimeError, match="Unexpected table"):
            migrate(migrator, "base", down=True)
    finally:
        migrator.dispose()


def test_force_rls_owner_count_is_not_an_emptiness_proof(bootstrap: Engine) -> None:
    with bootstrap.connect() as conn:
        assert conn.exec_driver_sql(f"SELECT count(*) FROM {BINDINGS}").scalar_one() > 0
    migrator = make_engine("fp6_migration_login")
    try:
        with migrator.begin() as conn:
            conn.exec_driver_sql("SET LOCAL ROLE fp6_owner")
            assert conn.exec_driver_sql(f"SELECT count(*) FROM {BINDINGS}").scalar_one() == 0
    finally:
        migrator.dispose()
