"""Opt-in schema candidate controller. No adapter, rule execution or application import.

The original tenant guard deliberately does not recognize these additive objects.
This separate guard retains its complete inventory boundaries and names each
additional object; it never patches the old migration graph or runtime helper.
"""

import os

from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, Engine, text

from experiments.tenant_db import DATABASE, EXPECTED_TABLES, MARKER, ROOT

REVISION = "c03_comp01_0001"
VERSION_TABLE = ("fp6_guard", "provenance_alembic_version")
ADDED_TABLES = {
    ("fp6_data", "generation_implementations"),
    ("fp6_reference", "implementation_packages"),
    VERSION_TABLE,
}
ADDED_ROUTINES = {
    ("fp6_context", "bind_implementation"),
    ("fp6_context", "immutable_implementation"),
}
BASE_ROUTINES = {("fp6_auth", "lookup_session")} | {
    ("fp6_context", name)
    for name in (
        "owner_id",
        "immutable_owner",
        "source_budget",
        "row_slot",
        "group_bounds",
        "alias_budget",
        "context_eligible",
    )
}


def require_candidate_database(conn: Connection) -> None:
    """Recognize only the intact 6C-02 base and this explicit additive inventory."""
    if os.environ.get("FP6_SYNTHETIC_ONLY") != MARKER:
        raise RuntimeError("Synthetic opt-in required")
    if conn.scalar(text("SELECT current_database()")) != DATABASE:
        raise RuntimeError("Unrecognized database")
    if conn.scalar(text("SELECT marker FROM fp6_guard.disposable")) != MARKER:
        raise RuntimeError("Unrecognized disposable marker")
    schemas = set(
        conn.scalars(
            text(
                "SELECT nspname FROM pg_namespace WHERE nspname !~ '^pg_' "
                "AND nspname <> 'information_schema'"
            )
        )
    )
    if schemas != {
        "public",
        "fp6_guard",
        "fp6_auth",
        "fp6_data",
        "fp6_reference",
        "fp6_context",
        "fp6_ledger",
    }:
        raise RuntimeError("Unexpected schema; refuse candidate migration")
    tables = set(
        conn.execute(
            text(
                "SELECT schemaname,tablename FROM pg_tables WHERE schemaname !~ '^pg_' "
                "AND schemaname <> 'information_schema'"
            )
        ).all()
    )
    if tables - (EXPECTED_TABLES | ADDED_TABLES) or not EXPECTED_TABLES <= tables:
        raise RuntimeError("Unexpected table; refuse candidate migration")
    additions = tables - EXPECTED_TABLES
    if additions not in (set(), {VERSION_TABLE}, ADDED_TABLES):
        raise RuntimeError("Incomplete candidate inventory")
    if conn.scalar(text("SELECT version_num FROM fp6_guard.tenant_alembic_version")) != "6c02_0001":
        raise RuntimeError("Exact 6C-02 base required")
    if conn.scalar(
        text(
            "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname LIKE 'fp6_%' AND c.relkind IN ('v','m','f','p','S')"
        )
    ):
        raise RuntimeError("Unexpected view/foreign/partition/sequence object")
    routine_rows = list(
        conn.execute(
            text(
                "SELECT n.nspname,p.proname FROM pg_proc p JOIN pg_namespace n "
                "ON n.oid=p.pronamespace WHERE n.nspname LIKE 'fp6_%'"
            )
        ).all()
    )
    routines = set(routine_rows)
    if len(routines) != len(routine_rows) or routines != BASE_ROUTINES | (
        ADDED_ROUTINES if additions == ADDED_TABLES else set()
    ):
        raise RuntimeError("Unexpected routine; refuse candidate migration")
    if (
        additions == ADDED_TABLES
        and conn.scalar(text("SELECT version_num FROM fp6_guard.provenance_alembic_version"))
        != REVISION
    ):
        raise RuntimeError("Unrecognized candidate revision")


def migrate_candidate(engine: Engine, *, down: bool = False) -> None:
    """Atomic guarded candidate install/removal; no connection string or offline SQL."""
    with engine.begin() as conn:
        conn.exec_driver_sql("SET LOCAL ROLE fp6_owner")
        require_candidate_database(conn)
        config = Config(str(ROOT / "provenance-alembic.ini"))
        config.attributes["connection"] = conn
        if down:
            command.downgrade(config, "base")
            # Alembic leaves an empty version table. Remove just this known table
            # after its row deletion, restoring compatibility with the old guard.
            conn.exec_driver_sql("DROP TABLE fp6_guard.provenance_alembic_version")
        else:
            command.upgrade(config, "head")
        require_candidate_database(conn)
