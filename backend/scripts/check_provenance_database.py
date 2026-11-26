"""Fresh synthetic C03-COMP-01 migration receipts; never executes the adapter."""

import subprocess
import sys

from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import DBAPIError

from experiments.provenance_schema import migrate_candidate, require_candidate_database
from experiments.tenant_db import migrate, provision_fresh, require_disposable
from experiments.tenant_db import test_engine as make_engine


def tests(*args: str) -> None:
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", *args], check=False)
    if result.returncode:
        raise SystemExit(result.returncode)


def journal(conn: Connection) -> list[tuple[object, ...]]:
    return [
        tuple(row)
        for row in conn.exec_driver_sql(
            "SELECT * FROM fp6_ledger.deletion_journal ORDER BY owner_id,event_id"
        ).all()
    ]


def old_definition(conn: Connection) -> list[tuple[object, ...]]:
    """All original columns, policies, constraints, grants and routines unchanged.

    Only the named added generation FK/trigger are excluded. Catalog identity
    OIDs change during the explicitly permitted old disposable roundtrip.
    """
    queries = (
        "SELECT table_schema,table_name,column_name,data_type,is_nullable,column_default "
        "FROM information_schema.columns WHERE table_schema LIKE 'fp6_%' "
        "AND table_name NOT IN ('implementation_packages','generation_implementations',"
        "'provenance_alembic_version') ORDER BY 1,2,ordinal_position",
        "SELECT n.nspname,c.relname,k.conname,pg_get_constraintdef(k.oid) "
        "FROM pg_constraint k JOIN pg_class c ON k.conrelid=c.oid "
        "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname LIKE 'fp6_%' "
        "AND c.relname NOT IN ('implementation_packages','generation_implementations',"
        "'provenance_alembic_version') AND k.conname <> 'implementation_required' ORDER BY 1,2,3",
        "SELECT schemaname,tablename,policyname,roles::text,cmd,qual,with_check "
        "FROM pg_policies WHERE schemaname LIKE 'fp6_%' "
        "AND tablename NOT IN ('implementation_packages','generation_implementations') "
        "ORDER BY 1,2,3",
        "SELECT table_schema,table_name,grantee,privilege_type,is_grantable "
        "FROM information_schema.table_privileges WHERE table_schema LIKE 'fp6_%' "
        "AND table_name NOT IN ('implementation_packages','generation_implementations',"
        "'provenance_alembic_version') ORDER BY 1,2,3,4",
        "SELECT pg_get_functiondef(p.oid) FROM pg_proc p "
        "JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname LIKE 'fp6_%' "
        "AND p.proname NOT IN ('bind_implementation','immutable_implementation') "
        "ORDER BY n.nspname,p.proname",
    )
    return [tuple(row) for sql in queries for row in conn.execute(text(sql)).all()]


def no_loss_on_denied_downgrade(bootstrap: Engine, migrator: Engine) -> None:
    with bootstrap.connect() as conn:
        before = conn.exec_driver_sql(
            "SELECT * FROM fp6_data.generation_implementations "
            "ORDER BY owner_id,collection_id,generation"
        ).all()
        receipts = journal(conn)
        assert before
    try:
        migrate_candidate(migrator, down=True)
    except DBAPIError as error:
        assert error.orig.sqlstate == "23514"  # type: ignore[union-attr]
    else:
        raise AssertionError("Nonempty provenance downgrade must fail")
    with bootstrap.connect() as conn:
        assert (
            conn.exec_driver_sql(
                "SELECT * FROM fp6_data.generation_implementations "
                "ORDER BY owner_id,collection_id,generation"
            ).all()
            == before
        )
        assert journal(conn) == receipts
        require_candidate_database(conn)
    print("PASS: nonempty downgrade refused (23514), every binding and ledger row retained")


def main() -> None:
    bootstrap = make_engine("fp6_bootstrap")
    migrator = make_engine("fp6_migration_login")
    try:
        with bootstrap.begin() as conn:
            provision_fresh(conn)
        migrate(migrator)
        tests("db_tests")  # Unmodified 434-case baseline, no compatibility plugin.
        with bootstrap.connect() as conn:
            before = journal(conn)
            assert before
            generations = conn.exec_driver_sql(
                "SELECT count(*) FROM fp6_data.generations"
            ).scalar_one()
            assert generations > 0
            print(
                f"PRE-UPGRADE: {generations} existing synthetic generations (bootstrap inventory)"
            )
        try:
            migrate_candidate(migrator)
        except DBAPIError as error:
            assert error.orig.sqlstate == "23514"  # type: ignore[union-attr]
        else:
            raise AssertionError(
                "Refuse to invent implementation identity for existing generations"
            )
        with bootstrap.connect() as conn:
            require_disposable(conn)
            assert journal(conn) == before
        print("PASS: upgrade over unbound historical generations refused atomically (23514)")

        # Use only the original documented disposable-fixture reset. There is no
        # C03 binding to delete: the preceding upgrade rolled back completely.
        migrate(migrator, "base", down=True)
        migrate(migrator)
        with bootstrap.connect() as conn:
            assert journal(conn) == before
            original = old_definition(conn)
        migrate_candidate(migrator)
        with bootstrap.connect() as conn:
            assert old_definition(conn) == original
            assert journal(conn) == before
        migrate_candidate(migrator, down=True)  # Safe: no generations/bindings exist.
        with bootstrap.connect() as conn:
            require_disposable(conn)
            assert old_definition(conn) == original
            assert journal(conn) == before
        migrate_candidate(migrator)
        with bootstrap.connect() as conn:
            require_candidate_database(conn)
            assert old_definition(conn) == original
            assert journal(conn) == before
        print(
            "PASS: empty candidate upgrade/downgrade/re-upgrade; old schema and journal unchanged"
        )
        tests("db_tests", "-p", "experiments.provenance_legacy_compat")
        tests("provenance_tests", "-vv", "-s", "-p", "experiments.provenance_legacy_compat")
        no_loss_on_denied_downgrade(bootstrap, migrator)
        with bootstrap.connect() as conn:
            assert old_definition(conn) == original
        print("PASS: C03-COMP-01 synthetic schema candidate; no adapter/application activation")
    finally:
        bootstrap.dispose()
        migrator.dispose()


if __name__ == "__main__":
    main()
