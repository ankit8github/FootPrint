"""Independent schema-only review; retained candidate and adapter files are untouched."""

import subprocess
import sys
from collections.abc import Sequence
from typing import Any
from unittest.mock import patch

from sqlalchemy import Engine, event, text
from sqlalchemy.exc import DBAPIError

from experiments.provenance_schema import migrate_candidate, require_candidate_database
from experiments.tenant_db import owner_transaction, require_disposable
from experiments.tenant_db import test_engine as make_engine
from scripts import check_provenance_database as baseline
from scripts import run_provenance_database as launcher


def snapshot(engine: Engine) -> list[list[tuple[Any, ...]]]:
    queries = (
        "SELECT n.nspname,c.relname,c.relkind,c.relrowsecurity,c.relforcerowsecurity,"
        "c.relowner,c.relacl::text FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
        "WHERE n.nspname LIKE 'fp6_%' ORDER BY 1,2",
        "SELECT n.nspname,c.relname,k.conname,pg_get_constraintdef(k.oid),k.convalidated "
        "FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid "
        "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname LIKE 'fp6_%' ORDER BY 1,2,3",
        "SELECT n.nspname,c.relname,t.tgname,pg_get_triggerdef(t.oid),t.tgenabled "
        "FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
        "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname LIKE 'fp6_%' ORDER BY 1,2,3",
        "SELECT pg_get_functiondef(p.oid),p.proacl::text FROM pg_proc p "
        "JOIN pg_namespace n ON n.oid=p.pronamespace "
        "WHERE n.nspname LIKE 'fp6_%' ORDER BY n.nspname,p.proname",
        "SELECT schemaname,tablename,policyname,roles::text,cmd,qual,with_check "
        "FROM pg_policies WHERE schemaname LIKE 'fp6_%' ORDER BY 1,2,3",
        "SELECT rolname,rolsuper,rolinherit,rolcreaterole,rolcreatedb,rolcanlogin,"
        "rolreplication,rolbypassrls FROM pg_roles WHERE rolname LIKE 'fp6_%' ORDER BY 1",
        "SELECT roleid,member,grantor,admin_option,inherit_option,set_option "
        "FROM pg_auth_members ORDER BY 1,2,3",
    )
    with engine.connect() as conn:
        result = [[tuple(row) for row in conn.execute(text(sql))] for sql in queries]
        tables = conn.execute(
            text(
                "SELECT schemaname,tablename FROM pg_tables WHERE schemaname LIKE 'fp6_%' "
                "ORDER BY 1,2"
            )
        ).all()
        for schema, table in tables:
            result.append(
                [
                    tuple(row)
                    for row in conn.exec_driver_sql(
                        f'SELECT to_jsonb(t)::text FROM "{schema}"."{table}" t '
                        "ORDER BY to_jsonb(t)::text"
                    )
                ]
            )
        return result


def interrupt_migration(bootstrap: Engine, migrator: Engine, *, down: bool, marker: str) -> None:
    before = snapshot(bootstrap)
    fired = False

    def terminate(conn: Any, cursor: Any, statement: str, *args: Any) -> None:
        nonlocal fired
        if not fired and marker in statement:
            fired = True
            pid = conn.connection.driver_connection.info.backend_pid
            with bootstrap.begin() as observer:
                assert observer.scalar(text("SELECT pg_terminate_backend(:pid)"), {"pid": pid})

    event.listen(migrator, "after_cursor_execute", terminate)
    try:
        try:
            migrate_candidate(migrator, down=down)
        except DBAPIError:
            assert fired, "Failure must be caused after the selected DDL interruption point"
        else:
            raise AssertionError("Terminated migration unexpectedly committed")
    finally:
        event.remove(migrator, "after_cursor_execute", terminate)
    assert snapshot(bootstrap) == before, "Interrupted DDL/version/rows/journal changed"
    with bootstrap.connect() as conn:
        (require_candidate_database if down else require_disposable)(conn)
    print(f"PASS interruption: down={down}, after={marker}; exact catalog/rows/journal retained")


def independent_negatives(bootstrap: Engine) -> None:
    runtime = make_engine("fp6_runtime_login")
    auth = make_engine("fp6_auth_login")
    with bootstrap.connect() as conn:
        binding = dict(
            conn.exec_driver_sql(
                "SELECT * FROM fp6_data.generation_implementations "
                "WHERE generation=2 ORDER BY owner_id LIMIT 1"
            )
            .mappings()
            .one()
        )
        foreign = conn.execute(
            text(
                "SELECT owner_id FROM fp6_data.generation_implementations "
                "WHERE owner_id<>:own ORDER BY owner_id LIMIT 1"
            ),
            {"own": binding["owner_id"]},
        ).scalar_one()
    owner = binding["owner_id"]
    before = snapshot(bootstrap)
    bindings = "fp6_data.generation_implementations"
    packages = "fp6_reference.implementation_packages"
    with owner_transaction(runtime, owner) as conn:
        assert conn.scalar(text("SELECT current_user")) == "fp6_runtime_login"
        assert (
            conn.scalar(
                text(f"SELECT count(*) FROM {bindings} WHERE owner_id=:owner"), {"owner": owner}
            )
            > 0
        )
        assert (
            conn.scalar(
                text(f"SELECT count(*) FROM {bindings} WHERE owner_id=:owner"), {"owner": foreign}
            )
            == 0
        )
    cases: list[tuple[Engine, str, dict[str, Any], str, bool]] = [
        (runtime, f"DELETE FROM {bindings}", {}, "42501", True),
        (runtime, f"UPDATE {bindings} SET package_revision=package_revision", {}, "42501", True),
        (runtime, f"TRUNCATE {bindings} CASCADE", {}, "42501", True),
        (runtime, "DELETE FROM fp6_data.generations WHERE generation=2", {}, "23503", True),
        (
            runtime,
            "UPDATE fp6_data.generations SET generation=991 WHERE generation=2",
            {},
            "42501",
            True,
        ),
        (runtime, "SET ROLE fp6_owner", {}, "42501", True),
        (auth, f"SELECT * FROM {bindings}", {}, "42501", False),
        (auth, f"SELECT * FROM {packages}", {}, "42501", False),
        (bootstrap, f"UPDATE {bindings} SET worker_sha256=worker_sha256", {}, "42501", False),
        (bootstrap, f"DELETE FROM {bindings}", {}, "42501", False),
        (bootstrap, f"TRUNCATE {bindings} CASCADE", {}, "42501", False),
        (bootstrap, f"UPDATE {packages} SET pure_sha256=pure_sha256", {}, "42501", False),
        (bootstrap, f"DELETE FROM {packages}", {}, "42501", False),
        (bootstrap, f"TRUNCATE {packages} CASCADE", {}, "42501", False),
    ]
    columns = ",".join(binding)
    values = ",".join(":" + key for key in binding)
    insert = f"INSERT INTO {bindings} ({columns}) VALUES ({values})"
    cases.extend(
        [
            (runtime, insert, binding, "23505", True),
            (runtime, insert, {**binding, "generation": 991}, "23503", True),
            (
                runtime,
                insert,
                {**binding, "generation": 991, "worker_sha256": "0" * 64},
                "23503",
                True,
            ),
            (runtime, insert, {**binding, "owner_id": foreign, "generation": 991}, "42501", True),
        ]
    )
    try:
        for index, (engine, sql, params, code, scoped) in enumerate(cases, 1):
            try:
                with owner_transaction(engine, owner) if scoped else engine.begin() as conn:
                    conn.execute(text(sql), params)
            except DBAPIError as error:
                assert error.orig.sqlstate == code, (index, error.orig.sqlstate, code)  # type: ignore[union-attr]
            else:
                raise AssertionError(f"Independent negative {index} unexpectedly committed")
            assert snapshot(bootstrap) == before, f"Independent negative {index} changed state"
            print(
                f"PASS independent negative {index}: exact SQLSTATE {code}; complete state retained"
            )
    finally:
        runtime.dispose()
        auth.dispose()


def controller() -> None:
    bootstrap = make_engine("fp6_bootstrap")
    original_tests = baseline.tests
    empty_upgrade_reviewed = False
    empty_downgrade_reviewed = False

    def reviewed_migrate(engine: Engine, *, down: bool = False) -> None:
        nonlocal empty_upgrade_reviewed, empty_downgrade_reviewed
        with bootstrap.connect() as conn:
            empty = conn.scalar(text("SELECT count(*) FROM fp6_data.generations")) == 0
        if empty and not down and not empty_upgrade_reviewed:
            for marker in (
                "CREATE TABLE fp6_guard.provenance_alembic_version",
                "CREATE TABLE fp6_reference.implementation_packages",
            ):
                interrupt_migration(bootstrap, engine, down=False, marker=marker)
            empty_upgrade_reviewed = True
        if empty and down and not empty_downgrade_reviewed:
            for marker in (
                "DROP TABLE fp6_data.generation_implementations",
                "DROP TABLE fp6_guard.provenance_alembic_version",
            ):
                interrupt_migration(bootstrap, engine, down=True, marker=marker)
            empty_downgrade_reviewed = True
        migrate_candidate(engine, down=down)

    def reviewed_tests(*args: str) -> None:
        original_tests(*args)
        if args[0] == "provenance_tests":
            independent_negatives(bootstrap)

    try:
        with (
            patch.object(baseline, "migrate_candidate", reviewed_migrate),
            patch.object(baseline, "tests", reviewed_tests),
        ):
            baseline.main()
        assert empty_upgrade_reviewed and empty_downgrade_reviewed
    finally:
        bootstrap.dispose()


def main() -> None:
    if sys.argv[1:] == ["--controller"]:
        controller()
        return
    original_run = subprocess.run

    def scoped_run(args: Sequence[str], **kwargs: Any) -> Any:
        if list(args) == [sys.executable, "-m", "scripts.check_provenance_database"]:
            args = [sys.executable, "-m", "scripts.review_provenance_database", "--controller"]
        return original_run(args, **kwargs)

    with patch.object(subprocess, "run", scoped_run):
        launcher.main()


if __name__ == "__main__":
    main()
