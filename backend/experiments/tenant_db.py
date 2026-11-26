"""Synthetic-only PostgreSQL helpers. Unimported by every application route.

No identity integration or persistence repository. Caller supplies fictional owner
UUIDs. This is privileged test tooling, not a production connection factory.
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import UUID

from alembic import command
from alembic.config import Config
from sqlalchemy import URL, Connection, Engine, create_engine, text

DATABASE = "fp6c02_synthetic"
MARKER = "phase6c02-disposable-fictional-only-v1"
ROOT = Path(__file__).resolve().parents[1]
ROLES = ("fp6_owner", "fp6_migrator", "fp6_runtime", "fp6_auth", "fp6_restore")


def test_engine(user: str = "fp6_bootstrap", *, pooled: bool = False) -> Engine:
    if os.environ.get("FP6_SYNTHETIC_ONLY") != MARKER:
        raise RuntimeError("Explicit disposable synthetic opt-in required")
    password = os.environ["FP6_TEST_PASSWORD"]
    return create_engine(
        URL.create(
            "postgresql+psycopg",
            username=user,
            password=password,
            host="127.0.0.1",
            port=int(os.environ.get("FP6_TEST_PORT", "55433")),
            database=DATABASE,
        ),
        pool_size=1 if pooled else 5,
        max_overflow=0,
        hide_parameters=True,
    )


def require_disposable(conn: Connection) -> None:
    """Fail before DDL when the independent opt-in, marker or inventory differs."""
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
    if schemas - {
        "public",
        "fp6_guard",
        "fp6_auth",
        "fp6_data",
        "fp6_reference",
        "fp6_context",
        "fp6_ledger",
    }:
        raise RuntimeError("Unexpected schema; refuse migration/downgrade")
    # Exact versioned table allowlist prevents destructive rollback of unrelated
    # objects even if someone creates them inside an experiment-owned schema.
    tables = set(
        conn.execute(
            text(
                "SELECT schemaname, tablename FROM pg_tables WHERE schemaname !~ '^pg_' "
                "AND schemaname <> 'information_schema'"
            )
        ).all()
    )
    if tables - EXPECTED_TABLES:
        raise RuntimeError("Unexpected table; refuse migration/downgrade")
    unexpected_objects = conn.scalar(
        text(
            "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname LIKE 'fp6_%' AND c.relkind IN ('v','m','f','p','S')"
        )
    )
    if unexpected_objects:
        raise RuntimeError("Unexpected view/foreign/partition/sequence object")
    routines = set(
        conn.execute(
            text(
                "SELECT n.nspname,p.proname FROM pg_proc p JOIN pg_namespace n "
                "ON n.oid=p.pronamespace "
                "WHERE n.nspname LIKE 'fp6_%'"
            )
        ).all()
    )
    allowed_routines = {("fp6_auth", "lookup_session")} | {
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
    if routines - allowed_routines:
        raise RuntimeError("Unexpected routine; refuse migration/downgrade")


DATA_TABLES = (
    "tenant_state",
    "consents",
    "collections",
    "generations",
    "import_sources",
    "observations",
    "observation_features",
    "context_evidence",
    "excluded_rows",
    "evidence_groups",
    "evidence_equivalence",
    "commercial_groups",
    "commercial_alias_members",
    "findings",
    "finding_evidence",
    "assessments",
    "rationale_evidence",
    "assessment_limitations",
    "unknown_claims",
    "user_actions",
    "deletion_requests",
    "outbox",
    "idempotency_records",
)
EXPECTED_TABLES = (
    {("fp6_data", table) for table in DATA_TABLES}
    | {("fp6_auth", table) for table in ("users", "identity_links", "sessions")}
    | {
        ("fp6_reference", table)
        for table in ("organizations", "directory_versions", "action_eligibility")
    }
    | {
        ("fp6_guard", "disposable"),
        ("fp6_guard", "tenant_alembic_version"),
        ("fp6_ledger", "deletion_journal"),
    }
)


def provision_fresh(conn: Connection) -> None:
    """Once only, as bootstrap on a NEW database in a dedicated test cluster."""
    if os.environ.get("FP6_SYNTHETIC_ONLY") != MARKER:
        raise RuntimeError("Synthetic opt-in required")
    if conn.scalar(text("SELECT current_database()")) != DATABASE:
        raise RuntimeError("Unrecognized database")
    objects = conn.scalar(
        text(
            "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'"
        )
    )
    schemas = set(
        conn.scalars(
            text(
                "SELECT nspname FROM pg_namespace WHERE nspname !~ '^pg_' "
                "AND nspname <> 'information_schema'"
            )
        )
    )
    if objects or schemas != {"public"}:
        raise RuntimeError("Fresh database required; no existing objects may be adopted")
    for role in (*ROLES, "fp6_migration_login", "fp6_runtime_login", "fp6_auth_login"):
        if conn.scalar(text("SELECT 1 FROM pg_roles WHERE rolname=:role"), {"role": role}):
            raise RuntimeError("Existing experiment roles; use a fresh dedicated cluster")
    for role in ROLES:
        conn.exec_driver_sql(
            f"CREATE ROLE {role} NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE "
            "NOREPLICATION NOINHERIT"
        )
    conn.exec_driver_sql("GRANT fp6_owner TO fp6_migrator")
    raw = conn.connection.driver_connection
    if raw is None:
        raise RuntimeError("Missing driver connection")
    from psycopg import sql

    for capability in ("migrator", "runtime", "auth"):
        login = "migration" if capability == "migrator" else capability
        raw.execute(
            sql.SQL(
                "CREATE ROLE {} LOGIN INHERIT NOSUPERUSER NOBYPASSRLS NOCREATEDB "
                "NOCREATEROLE NOREPLICATION PASSWORD {}"
            ).format(
                sql.Identifier(f"fp6_{login}_login"), sql.Literal(os.environ["FP6_TEST_PASSWORD"])
            )
        )
        conn.exec_driver_sql(f"GRANT fp6_{capability} TO fp6_{login}_login")
    conn.exec_driver_sql(f"REVOKE ALL ON DATABASE {DATABASE} FROM PUBLIC")
    conn.exec_driver_sql(
        f"GRANT CONNECT ON DATABASE {DATABASE} TO fp6_migration_login, "
        "fp6_runtime_login, fp6_auth_login"
    )
    conn.exec_driver_sql(f"GRANT CREATE ON DATABASE {DATABASE} TO fp6_owner")
    conn.exec_driver_sql("REVOKE ALL ON SCHEMA public FROM PUBLIC")
    conn.exec_driver_sql("CREATE SCHEMA fp6_guard AUTHORIZATION fp6_owner")
    conn.exec_driver_sql("SET LOCAL ROLE fp6_owner")
    conn.exec_driver_sql("CREATE TABLE fp6_guard.disposable (marker varchar(64) PRIMARY KEY)")
    conn.execute(text("INSERT INTO fp6_guard.disposable VALUES (:marker)"), {"marker": MARKER})


def migrate(engine: Engine, target: str = "head", *, down: bool = False) -> None:
    with engine.begin() as conn:
        conn.exec_driver_sql("SET LOCAL ROLE fp6_owner")
        require_disposable(conn)
        config = Config(str(ROOT / "tenant-alembic.ini"))
        config.attributes["connection"] = conn
        if down:
            command.downgrade(config, target)
        else:
            command.upgrade(config, target)


def set_owner(conn: Connection, owner: UUID) -> None:
    if not conn.in_transaction():
        raise RuntimeError("Explicit transaction required before owner context")
    if not isinstance(owner, UUID):
        raise TypeError("Fictional owner must be a UUID")
    conn.execute(
        text(
            "SELECT set_config('app.owner_id', :owner, true), "
            "set_config('app.owner_xid', pg_current_xact_id()::text, true)"
        ),
        {"owner": str(owner)},
    )


@contextmanager
def owner_transaction(engine: Engine, owner: UUID) -> Iterator[Connection]:
    with engine.begin() as conn:
        set_owner(conn, owner)
        yield conn
