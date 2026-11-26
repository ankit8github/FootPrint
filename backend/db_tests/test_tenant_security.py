"""Adversarial direct SQL as actual restricted LOGIN roles, never SET ROLE."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError

from experiments.tenant_db import (
    DATA_TABLES,
    EXPECTED_TABLES,
    migrate,
    owner_transaction,
    require_disposable,
    set_owner,
)
from experiments.tenant_db import test_engine as make_engine

from .conftest import insert, tenant_snapshot

TABLES = [*("fp6_data." + t for t in DATA_TABLES), "fp6_ledger.deletion_journal"]
Pair = tuple[dict[str, Any], dict[str, Any]]


def denied(
    engine: Engine,
    owner: Any,
    sql: str,
    params: dict[str, Any] | None = None,
    codes: tuple[str, ...] = ("42501", "23503", "23514", "23505"),
) -> None:
    with pytest.raises(DBAPIError) as error, owner_transaction(engine, owner) as conn:
        conn.execute(text(sql), params or {})
    assert error.value.orig.sqlstate in codes  # type: ignore[union-attr]


@pytest.mark.parametrize("table", TABLES)
def test_every_table_foreign_crud_and_joins(runtime: Engine, pair: Pair, table: str) -> None:
    own, foreign = pair
    before = tenant_snapshot(runtime, foreign["owner_id"])
    with owner_transaction(runtime, foreign["owner_id"]) as conn:
        foreign_row = dict(conn.execute(text(f"SELECT * FROM {table} LIMIT 1")).mappings().one())
    with owner_transaction(runtime, own["owner_id"]) as conn:
        assert conn.scalar(text("SELECT current_user")) == "fp6_runtime_login"
        rows = conn.execute(text(f"SELECT owner_id FROM {table}")).scalars().all()
        assert rows and set(rows) == {own["owner_id"]}
        assert (
            conn.scalar(
                text(f"SELECT count(*) FROM {table} WHERE owner_id=:owner"),
                {"owner": foreign["owner_id"]},
            )
            == 0
        )
        assert (
            conn.scalar(
                text(
                    f"SELECT count(*) FROM {table} x JOIN fp6_data.tenant_state y "
                    "ON x.owner_id=y.owner_id WHERE y.owner_id=:owner"
                ),
                {"owner": foreign["owner_id"]},
            )
            == 0
        )
    with pytest.raises(DBAPIError) as error, owner_transaction(runtime, own["owner_id"]) as conn:
        insert(conn, table, foreign_row)
    assert error.value.orig.sqlstate == "42501"  # type: ignore[union-attr]
    for mutation in (
        f"DELETE FROM {table} WHERE owner_id=:owner",
        f"UPDATE {table} SET owner_id=:owner WHERE owner_id=:owner",
    ):
        try:
            with owner_transaction(runtime, own["owner_id"]) as conn:
                assert conn.execute(text(mutation), {"owner": foreign["owner_id"]}).rowcount == 0
        except DBAPIError as error:
            assert error.orig.sqlstate == "42501"  # type: ignore[union-attr]
    assert tenant_snapshot(runtime, foreign["owner_id"]) == before


# Each patch keeps owner A but splices a B reference, or a wrong same-owner
# collection/generation/domain/type. These are INSERT and ON CONFLICT negatives.
ASSOCIATIONS = [
    (
        "import_sources",
        {"source_id": "new", "ordinal": 4, "collection_id": "foreign:collection_id"},
    ),
    (
        "observations",
        {"observation_id": "new", "record_index": 4, "source_id": "foreign:source_id"},
    ),
    ("observation_features", {"observation_id": "foreign:o1"}),
    ("observation_features", {"adapter": "browser_chrome_json_v1"}),
    ("context_evidence", {"observation_id": "foreign:o1"}),
    ("context_evidence", {"observation_id": "own:o3"}),
    ("evidence_groups", {"group_id": "new", "primary_observation_id": "foreign:o1"}),
    ("evidence_equivalence", {"observation_id": "foreign:o1"}),
    ("evidence_equivalence", {"group_id": "foreign:group_id"}),
    ("commercial_groups", {"group_id": "new", "collection_id": "foreign:collection_id"}),
    ("commercial_alias_members", {"observation_id": "foreign:o3"}),
    ("commercial_alias_members", {"domain": "fictional-museum.test"}),
    ("commercial_alias_members", {"observation_id": "own:o1"}),
    ("findings", {"finding_id": "new", "generation": 999}),
    ("findings", {"finding_id": "new", "collection_id": "foreign:collection_id"}),
    ("finding_evidence", {"observation_id": "foreign:o1"}),
    ("finding_evidence", {"finding_id": "foreign:finding_id"}),
    ("finding_evidence", {"generation": 2}),
    ("assessments", {"finding_id": "foreign:finding_id"}),
    ("assessments", {"generation": 2}),
    ("rationale_evidence", {"observation_id": "foreign:o1"}),
    ("rationale_evidence", {"observation_id": "own:o2"}),
    ("rationale_evidence", {"generation": 2}),
    ("assessment_limitations", {"finding_id": "foreign:finding_id"}),
    ("unknown_claims", {"finding_id": "foreign:finding_id"}),
    ("user_actions", {"finding_id": "foreign:finding_id"}),
    ("user_actions", {"generation": 2}),
    ("user_actions", {"domain": "fictional-museum.test"}),
    ("user_actions", {"relationship_type": "marketing"}),
    ("user_actions", {"directory_id": "foreign:directory_id"}),
    ("user_actions", {"directory_version": 2}),
    ("user_actions", {"finding_id": "own:unresolved"}),
    ("deletion_requests", {"request_id": "new", "source_id": "foreign:empty"}),
    ("deletion_requests", {"request_id": "new", "collection_id": "foreign:collection_id"}),
    ("outbox", {"event_id": "new", "request_id": "foreign:request_id"}),
    ("outbox", {"event_id": "new", "revision": 1}),
    ("idempotency_records", {"key": "new", "request_id": "foreign:request_id"}),
    ("idempotency_records", {"key": "new", "consent_epoch": 2}),
]


@pytest.mark.parametrize("table,patch", ASSOCIATIONS)
@pytest.mark.parametrize("method", ["insert", "upsert", "update"])
def test_composite_associations(
    runtime: Engine, pair: Pair, table: str, patch: dict[str, Any], method: str
) -> None:
    own, foreign = pair
    before = tenant_snapshot(runtime, foreign["owner_id"])
    own_before = tenant_snapshot(runtime, own["owner_id"])
    with owner_transaction(runtime, own["owner_id"]) as conn:
        row = dict(conn.execute(text(f"SELECT * FROM fp6_data.{table} LIMIT 1")).mappings().one())
    changes = {}
    for key, value in patch.items():
        if value == "new":
            changes[key] = uuid4()
        elif isinstance(value, str) and value.startswith("foreign:"):
            changes[key] = foreign[value.split(":")[1]]
        elif isinstance(value, str) and value.startswith("own:"):
            changes[key] = own[value.split(":")[1]]
        else:
            changes[key] = value
    row.update(changes)
    if method == "update":
        statement = f"UPDATE fp6_data.{table} SET " + ", ".join(f"{k}=:{k}" for k in changes)
        # Limit the UPDATE to the originally selected row via its full old values.
        with owner_transaction(runtime, own["owner_id"]) as conn:
            old = dict(
                conn.execute(text(f"SELECT * FROM fp6_data.{table} LIMIT 1")).mappings().one()
            )
        statement += " WHERE " + " AND ".join(f"{k} IS NOT DISTINCT FROM :old_{k}" for k in old)
        params = {**changes, **{"old_" + k: v for k, v in old.items()}}
    else:
        statement = (
            f"INSERT INTO fp6_data.{table} ({','.join(row)}) VALUES ("
            + ",".join(":" + k for k in row)
            + ")"
        )
        if method == "upsert":
            # Exercise the UPDATE branch too: conflicts on the actual primary key
            # update references; for changed PKs the attempted INSERT must deny.
            admin_engine = make_engine()
            with admin_engine.connect() as admin:
                pk = (
                    admin.execute(
                        text(
                            "SELECT a.attname FROM pg_index i JOIN pg_attribute a ON "
                            "a.attrelid=i.indrelid AND a.attnum=ANY(i.indkey) "
                            "WHERE i.indrelid=CAST(:table AS regclass) AND i.indisprimary "
                            "ORDER BY array_position(i.indkey, a.attnum)"
                        ),
                        {"table": "fp6_data." + table},
                    )
                    .scalars()
                    .all()
                )
            admin_engine.dispose()
            statement += (
                " ON CONFLICT ("
                + ",".join(pk)
                + ") DO UPDATE SET "
                + ",".join(f"{k}=EXCLUDED.{k}" for k in changes)
            )
        params = row
    denied(runtime, own["owner_id"], statement, params)
    assert tenant_snapshot(runtime, foreign["owner_id"]) == before
    assert tenant_snapshot(runtime, own["owner_id"]) == own_before


@pytest.mark.parametrize(
    "table,field,value",
    [
        ("import_sources", "ordinal", 0),
        ("import_sources", "ordinal", 21),
        ("import_sources", "record_count", 10001),
        ("import_sources", "adapter", "raw"),
        ("observations", "record_index", 10000),
        ("observations", "time_status", "valid-ish"),
        ("observations", "domain", "real.example"),
        ("observations", "kind", "verified_account"),
        ("observations", "occurred_at", "2101-01-01Z"),
        ("observations", "time_status", "missing"),
        ("observation_features", "feature", "secret prose"),
        ("context_evidence", "code", "diagnosis"),
        ("findings", "kind", "unresolved"),
        ("assessments", "retention_status", "verified"),
        ("assessments", "confidence", "confirmed"),
        ("rationale_evidence", "code", "arbitrary explanation"),
        ("unknown_claims", "evidence_state", "known"),
        ("user_actions", "status", "verified_external_response"),
        ("user_actions", "realm", "real"),
        ("outbox", "state", "acknowledged"),
        ("idempotency_records", "request_hmac", b"raw"),
        ("deletion_requests", "affected_count", -1),
        ("deletion_requests", "source_id", None),
    ],
)
def test_finite_checks(
    runtime: Engine, tenants: list[dict[str, Any]], table: str, field: str, value: Any
) -> None:
    owner = tenants[0]["owner_id"]
    with owner_transaction(runtime, owner) as conn:
        predicate = " WHERE kind='relationship'" if table == "findings" else ""
        row = dict(
            conn.execute(text(f"SELECT * FROM fp6_data.{table}{predicate} LIMIT 1"))
            .mappings()
            .one()
        )
    row[field] = value
    with pytest.raises(DBAPIError) as error, owner_transaction(runtime, owner) as conn:
        insert(conn, "fp6_data." + table, row)
    assert error.value.orig.sqlstate in ("23514", "22001")  # type: ignore[union-attr]


def test_uniqueness_row_bounds_and_source_budget(
    runtime: Engine, tenants: list[dict[str, Any]]
) -> None:
    own, other = tenants
    # The two owners already use ordinal 1, row index 0 and generation 1.
    for tenant in (own, other):
        with owner_transaction(runtime, tenant["owner_id"]) as conn:
            assert (
                conn.scalar(text("SELECT count(*) FROM fp6_data.import_sources WHERE ordinal=1"))
                == 1
            )
        denied(
            runtime,
            tenant["owner_id"],
            "INSERT INTO fp6_data.import_sources SELECT * FROM fp6_data.import_sources LIMIT 1",
            codes=("23505",),
        )
    params = {**own, "new": uuid4()}
    denied(
        runtime,
        own["owner_id"],
        "INSERT INTO fp6_data.import_sources VALUES "
        "(:owner_id,:collection_id,:new,4,'email_eml_v1',10000,'active')",
        params,
        codes=("23514",),
    )
    denied(
        runtime,
        own["owner_id"],
        "INSERT INTO fp6_data.excluded_rows VALUES "
        "(:owner_id,:collection_id,:source_id,0,5,'email_eml_v1','INVALID_RECORD')",
        params,
        codes=("23514",),
    )
    denied(
        runtime,
        own["owner_id"],
        "INSERT INTO fp6_data.observations SELECT owner_id,collection_id,:new,source_id,"
        "4,source_count,adapter,kind,domain,occurred_at,time_status,attribution,issue_code "
        "FROM fp6_data.observations WHERE observation_id=:o1",
        params,
        codes=("23514",),
    )


@pytest.mark.parametrize("context", ["missing", "empty", "malformed", "stale", "stale-session"])
def test_context_fail_closed(runtime: Engine, tenants: list[dict[str, Any]], context: str) -> None:
    own = tenants[0]
    with runtime.connect() as conn:
        with conn.begin():
            if context != "missing":
                owner = {"empty": "", "malformed": "not-a-uuid"}.get(context, str(own["owner_id"]))
                conn.execute(
                    text(
                        "SELECT set_config('app.owner_id',:owner,:local), "
                        "set_config('app.owner_xid',:xid,:local)"
                    ),
                    {
                        "owner": owner,
                        "local": context != "stale-session",
                        "xid": "0"
                        if context.startswith("stale")
                        else str(conn.scalar(text("SELECT pg_current_xact_id()"))),
                    },
                )
            for table in TABLES:
                assert conn.scalar(text(f"SELECT count(*) FROM {table}")) == 0
            assert conn.scalar(text("SELECT fp6_context.owner_id()")) is None
            with pytest.raises(DBAPIError):
                conn.execute(
                    text("INSERT INTO fp6_data.tenant_state VALUES (:owner,1,0,'active')"),
                    {"owner": uuid4()},
                )
        # SQLAlchemy will roll back failed transaction at exit. No context survives.
        with conn.begin():
            assert conn.scalar(text("SELECT fp6_context.owner_id()")) is None


@pytest.mark.parametrize("end", ["commit", "rollback", "exception", "sql-error", "cancel"])
def test_one_connection_pool_reuse(
    runtime: Engine, tenants: list[dict[str, Any]], end: str
) -> None:
    own, foreign = tenants
    with runtime.connect() as conn:
        tx = conn.begin()
        set_owner(conn, own["owner_id"])
        pid = conn.scalar(text("SELECT pg_backend_pid()"))
        assert conn.scalar(text("SELECT fp6_context.owner_id()")) == own["owner_id"]
        if end in ("sql-error", "cancel"):
            with pytest.raises(DBAPIError):
                if end == "cancel":
                    conn.exec_driver_sql("SET LOCAL statement_timeout='10ms'")
                    conn.exec_driver_sql("SELECT pg_sleep(1)")
                else:
                    conn.exec_driver_sql("SELECT 1/0")
            with pytest.raises(DBAPIError):
                conn.exec_driver_sql("SELECT fp6_context.owner_id()")
            tx.rollback()
        elif end == "rollback":
            tx.rollback()
        elif end == "exception":
            try:
                raise RuntimeError("fictional request exception")
            except RuntimeError:
                tx.rollback()
        else:
            tx.commit()
    with runtime.connect() as conn, conn.begin():
        assert conn.scalar(text("SELECT pg_backend_pid()")) == pid
        assert conn.scalar(text("SELECT fp6_context.owner_id()")) is None
        assert conn.scalar(text("SELECT count(*) FROM fp6_data.findings")) == 0
        set_owner(conn, foreign["owner_id"])
        assert conn.execute(
            text("SELECT DISTINCT owner_id FROM fp6_data.findings")
        ).scalars().all() == [foreign["owner_id"]]
    with runtime.connect() as conn, conn.begin():
        assert conn.scalar(text("SELECT fp6_context.owner_id()")) is None


def test_session_level_context_rejected_after_commit(
    runtime: Engine, tenants: list[dict[str, Any]]
) -> None:
    with runtime.connect() as conn:
        with conn.begin():
            conn.execute(
                text(
                    "SELECT set_config('app.owner_id',:owner,false), "
                    "set_config('app.owner_xid',pg_current_xact_id()::text,false)"
                ),
                {"owner": str(tenants[0]["owner_id"])},
            )
            assert conn.scalar(text("SELECT fp6_context.owner_id()")) == tenants[0]["owner_id"]
        with conn.begin():
            assert conn.scalar(text("SELECT fp6_context.owner_id()")) is None
            assert conn.scalar(text("SELECT count(*) FROM fp6_data.observations")) == 0


@pytest.mark.parametrize(
    "statement",
    [
        "ALTER TABLE fp6_data.findings DISABLE ROW LEVEL SECURITY",
        "TRUNCATE fp6_data.findings CASCADE",
        "DROP TABLE fp6_data.findings CASCADE",
        "CREATE TABLE fp6_data.attack (id integer)",
        "CREATE TABLE public.attack (id integer)",
        "CREATE TEMP TABLE attack (id integer)",
        "CREATE SCHEMA attack",
        "CREATE FUNCTION fp6_data.attack() RETURNS int LANGUAGE sql AS 'SELECT 1'",
        "CREATE POLICY attack ON fp6_data.findings USING (true)",
        "SET ROLE fp6_owner",
        "SET ROLE fp6_migrator",
        "SET ROLE fp6_restore",
        "GRANT fp6_owner TO fp6_runtime_login",
        "UPDATE fp6_guard.tenant_alembic_version SET version_num='attack'",
        "UPDATE fp6_reference.directory_versions SET state='active'",
        "DELETE FROM fp6_ledger.deletion_journal",
    ],
)
def test_runtime_no_ddl_or_bypass(
    runtime: Engine, tenants: list[dict[str, Any]], statement: str
) -> None:
    denied(runtime, tenants[0]["owner_id"], statement, codes=("42501",))


@pytest.mark.parametrize(
    "schema,table", [("fp6_auth", t) for t in ("users", "identity_links", "sessions")]
)
def test_runtime_no_auth_enumeration(
    runtime: Engine, tenants: list[dict[str, Any]], schema: str, table: str
) -> None:
    denied(runtime, tenants[0]["owner_id"], f"SELECT * FROM {schema}.{table}", codes=("42501",))
    denied(
        runtime,
        tenants[0]["owner_id"],
        "SELECT * FROM fp6_auth.lookup_session(:digest)",
        {"digest": tenants[0]["digest"]},
        codes=("42501",),
    )


@pytest.mark.parametrize("table", TABLES)
def test_auth_no_footprint_or_session_enumeration(
    tenants: list[dict[str, Any]], table: str
) -> None:
    engine = make_engine("fp6_auth_login")
    try:
        with engine.connect() as conn:
            assert conn.scalar(text("SELECT current_user")) == "fp6_auth_login"
        for statement in (f"SELECT * FROM {table}", "SELECT * FROM fp6_auth.sessions"):
            with pytest.raises(DBAPIError) as error, engine.begin() as conn:
                conn.exec_driver_sql(statement)
            assert error.value.orig.sqlstate == "42501"  # type: ignore[union-attr]
        with engine.begin() as conn:
            assert (
                conn.execute(
                    text("SELECT * FROM fp6_auth.lookup_session(:digest)"),
                    {"digest": tenants[0]["digest"]},
                )
                .one()
                .owner_id
                == tenants[0]["owner_id"]
            )
            for digest in (bytes(32), b"", b"malformed"):
                assert (
                    conn.execute(
                        text("SELECT * FROM fp6_auth.lookup_session(:digest)"), {"digest": digest}
                    ).all()
                    == []
                )
    finally:
        engine.dispose()


def test_catalog_role_policy_and_column_inventory(bootstrap: Engine, runtime: Engine) -> None:
    with bootstrap.connect() as conn:
        tables = set(
            conn.execute(
                text("SELECT schemaname,tablename FROM pg_tables WHERE schemaname LIKE 'fp6_%'")
            ).all()
        )
        assert tables == EXPECTED_TABLES
        for role in (
            "fp6_runtime",
            "fp6_auth",
            "fp6_restore",
            "fp6_runtime_login",
            "fp6_auth_login",
            "fp6_migrator",
            "fp6_owner",
        ):
            flags = conn.execute(
                text(
                    "SELECT rolsuper,rolbypassrls,rolcreatedb,rolcreaterole,rolreplication "
                    "FROM pg_roles WHERE rolname=:role"
                ),
                {"role": role},
            ).one()
            assert not any(flags)
        for login in ("fp6_runtime_login", "fp6_auth_login", "fp6_restore"):
            for privileged in (
                "fp6_owner",
                "fp6_migrator",
                "pg_read_all_data",
                "pg_write_all_data",
                "pg_read_server_files",
                "pg_execute_server_program",
            ):
                assert not conn.scalar(
                    text("SELECT pg_has_role(:login,:role,'MEMBER')"),
                    {"login": login, "role": privileged},
                )
        for table in TABLES:
            row = conn.execute(
                text(
                    "SELECT c.relrowsecurity,c.relforcerowsecurity,r.rolname FROM pg_class c "
                    "JOIN pg_roles r ON c.relowner=r.oid WHERE c.oid=CAST(:table AS regclass)"
                ),
                {"table": table},
            ).one()
            assert tuple(row) == (True, True, "fp6_owner")
            policies = conn.execute(
                text(
                    "SELECT roles,cmd,qual,with_check FROM pg_policies "
                    "WHERE schemaname=:schema AND tablename=:table"
                ),
                dict(zip(("schema", "table"), table.split("."), strict=True)),
            ).all()
            assert len(policies) == 1
            assert policies[0].roles == ["fp6_runtime"] and policies[0].cmd == "ALL"
            assert "owner_id = fp6_context.owner_id()" in policies[0].qual
            assert policies[0].qual == policies[0].with_check
            for privilege in ("TRUNCATE", "TRIGGER", "REFERENCES"):
                assert not conn.scalar(
                    text("SELECT has_table_privilege('fp6_runtime_login',:table,:privilege)"),
                    {"table": table, "privilege": privilege},
                )
        assert (
            conn.scalar(
                text(
                    "SELECT count(*) FROM information_schema.columns "
                    "WHERE table_schema LIKE 'fp6_%' AND data_type IN ('json','jsonb','ARRAY')"
                )
            )
            == 0
        )
        definers = conn.execute(
            text(
                "SELECT n.nspname,p.proname FROM pg_proc p JOIN pg_namespace n "
                "ON n.oid=p.pronamespace WHERE n.nspname LIKE 'fp6_%' AND p.prosecdef"
            )
        ).all()
        assert definers == [("fp6_auth", "lookup_session")]
    with runtime.begin() as conn:
        conn.exec_driver_sql("SET LOCAL row_security=off")
        with pytest.raises(DBAPIError):
            conn.exec_driver_sql("SELECT * FROM fp6_data.findings")


def test_guard_rejects_unexpected_objects_and_missing_opt_in(
    bootstrap: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Roll back the foreign table; no destructive migration is invoked.
    with bootstrap.connect() as conn:
        transaction = conn.begin()
        conn.exec_driver_sql("CREATE TABLE fp6_data.unrecognized (id integer)")
        with pytest.raises(RuntimeError, match="Unexpected table"):
            require_disposable(conn)
        transaction.rollback()
    monkeypatch.delenv("FP6_SYNTHETIC_ONLY")
    with bootstrap.connect() as conn, pytest.raises(RuntimeError, match="opt-in"):
        require_disposable(conn)


def test_runtime_cannot_migrate(runtime: Engine) -> None:
    with pytest.raises(DBAPIError):
        migrate(runtime)


# Fresh primary keys prevent a duplicate-key error from masquerading as FK
# evidence. These INSERTs must fail specifically with foreign_key_violation.
FRESH_FKS = [
    (
        "import_sources",
        {"source_id": "new", "ordinal": 4, "collection_id": "foreign:collection_id"},
    ),
    (
        "observations",
        {"observation_id": "new", "source_id": "foreign:source_id", "record_index": 0},
    ),
    ("observation_features", {"observation_id": "foreign:o1"}),
    ("context_evidence", {"observation_id": "foreign:o1"}),
    ("excluded_rows", {"source_id": "foreign:source_id"}),
    ("evidence_groups", {"group_id": "new", "primary_observation_id": "foreign:o1"}),
    ("evidence_equivalence", {"observation_id": "foreign:o1"}),
    ("commercial_groups", {"group_id": "new", "collection_id": "foreign:collection_id"}),
    ("commercial_alias_members", {"observation_id": "foreign:o3"}),
    ("generations", {"collection_id": "foreign:collection_id"}),
    (
        "findings",
        {
            "finding_id": "new",
            "generation": 999,
            "domain": "fictional-museum.test",
            "kind": "relationship",
            "relationship_type": "visited",
            "issue_code": None,
        },
    ),
    ("finding_evidence", {"observation_id": "foreign:o1"}),
    ("assessments", {"finding_id": "foreign:finding_id"}),
    ("rationale_evidence", {"observation_id": "foreign:o1"}),
    ("assessment_limitations", {"finding_id": "foreign:finding_id"}),
    ("unknown_claims", {"finding_id": "foreign:finding_id"}),
    ("user_actions", {"directory_id": "foreign:directory_id"}),
    ("deletion_requests", {"request_id": "new", "source_id": "foreign:empty"}),
    ("outbox", {"event_id": "new", "request_id": "foreign:request_id"}),
    ("idempotency_records", {"key": "new", "request_id": "foreign:request_id"}),
]


@pytest.mark.parametrize("table,patch", FRESH_FKS)
def test_fresh_insert_foreign_key_evidence(
    runtime: Engine, pair: Pair, table: str, patch: dict[str, Any]
) -> None:
    own, foreign = pair
    before = tenant_snapshot(runtime, own["owner_id"])
    with owner_transaction(runtime, own["owner_id"]) as conn:
        row = dict(conn.execute(text(f"SELECT * FROM fp6_data.{table} LIMIT 1")).mappings().one())
    if table == "observations":
        # Select the email union arm deliberately; never rely on heap order.
        with owner_transaction(runtime, own["owner_id"]) as conn:
            row = dict(
                conn.execute(
                    text("SELECT * FROM fp6_data.observations WHERE observation_id=:id"),
                    {"id": own["o1"]},
                )
                .mappings()
                .one()
            )
    for key, value in patch.items():
        row[key] = (
            uuid4()
            if value == "new"
            else foreign[value.split(":")[1]]
            if isinstance(value, str) and value.startswith("foreign:")
            else value
        )
    with pytest.raises(DBAPIError) as error, owner_transaction(runtime, own["owner_id"]) as conn:
        insert(conn, "fp6_data." + table, row)
    assert error.value.orig.sqlstate == "23503"  # type: ignore[union-attr]
    assert tenant_snapshot(runtime, own["owner_id"]) == before


def test_owned_mutations_have_positive_control(
    runtime: Engine, tenants: list[dict[str, Any]]
) -> None:
    own = tenants[0]
    source_id = uuid4()
    with owner_transaction(runtime, own["owner_id"]) as conn:
        insert(
            conn,
            "fp6_data.import_sources",
            {
                "owner_id": own["owner_id"],
                "collection_id": own["collection_id"],
                "source_id": source_id,
                "ordinal": 4,
                "record_count": 0,
                "adapter": "email_eml_v1",
                "lifecycle": "active",
            },
        )
        assert (
            conn.execute(
                text(
                    "UPDATE fp6_data.import_sources SET lifecycle='pending_delete' "
                    "WHERE source_id=:id"
                ),
                {"id": source_id},
            ).rowcount
            == 1
        )
        assert (
            conn.execute(
                text("DELETE FROM fp6_data.import_sources WHERE source_id=:id"), {"id": source_id}
            ).rowcount
            == 1
        )
    # The same statements without a context cannot touch any tenant row.
    with runtime.begin() as conn:
        assert (
            conn.exec_driver_sql(
                "UPDATE fp6_data.import_sources SET lifecycle='pending_delete'"
            ).rowcount
            == 0
        )
        assert conn.exec_driver_sql("DELETE FROM fp6_data.import_sources").rowcount == 0


@pytest.mark.parametrize(
    "operation", ["singleton-equivalence", "empty-alias", "remove-copy", "remove-alias"]
)
def test_group_lower_bounds(runtime: Engine, tenants: list[dict[str, Any]], operation: str) -> None:
    own = tenants[0]
    before = tenant_snapshot(runtime, own["owner_id"])
    with pytest.raises(DBAPIError) as error, owner_transaction(runtime, own["owner_id"]) as conn:
        base = {"owner_id": own["owner_id"], "collection_id": own["collection_id"]}
        if operation == "singleton-equivalence":
            group_id = uuid4()
            insert(
                conn,
                "fp6_data.evidence_groups",
                {
                    **base,
                    "group_id": group_id,
                    "primary_observation_id": own["o3"],
                },
            )
            insert(
                conn,
                "fp6_data.evidence_equivalence",
                {
                    **base,
                    "group_id": group_id,
                    "observation_id": own["o3"],
                },
            )
        elif operation == "empty-alias":
            insert(
                conn,
                "fp6_data.commercial_groups",
                {
                    **base,
                    "group_id": uuid4(),
                    "domain": own["domain"],
                },
            )
        elif operation == "remove-copy":
            conn.execute(
                text("DELETE FROM fp6_data.evidence_equivalence WHERE observation_id=:id"),
                {"id": own["o2"]},
            )
        else:
            conn.execute(
                text("DELETE FROM fp6_data.commercial_alias_members WHERE observation_id=:id"),
                {"id": own["o3"]},
            )
    assert error.value.orig.sqlstate == "23514"  # type: ignore[union-attr]
    assert tenant_snapshot(runtime, own["owner_id"]) == before


def test_eight_alias_limit(runtime: Engine, tenants: list[dict[str, Any]]) -> None:
    own = tenants[0]
    with pytest.raises(DBAPIError) as error, owner_transaction(runtime, own["owner_id"]) as conn:
        base = {
            "owner_id": own["owner_id"],
            "collection_id": own["collection_id"],
            "domain": own["domain"],
        }
        for _ in range(7):
            group_id = uuid4()
            insert(conn, "fp6_data.commercial_groups", {**base, "group_id": group_id})
            insert(
                conn,
                "fp6_data.commercial_alias_members",
                {
                    **base,
                    "group_id": group_id,
                    "observation_id": own["o3"],
                    "required_feature": "PAID_RECEIPT_CLAIM",
                },
            )
        conn.exec_driver_sql("SET CONSTRAINTS ALL IMMEDIATE")
        assert (
            conn.scalar(
                text(
                    "SELECT count(*) FROM fp6_data.commercial_alias_members "
                    "WHERE observation_id=:id"
                ),
                {"id": own["o3"]},
            )
            == 8
        )
        conn.exec_driver_sql("SET CONSTRAINTS ALL DEFERRED")
        group_id = uuid4()
        insert(conn, "fp6_data.commercial_groups", {**base, "group_id": group_id})
        insert(
            conn,
            "fp6_data.commercial_alias_members",
            {
                **base,
                "group_id": group_id,
                "observation_id": own["o3"],
                "required_feature": "PAID_RECEIPT_CLAIM",
            },
        )
    assert error.value.orig.sqlstate == "23514"  # type: ignore[union-attr]
    assert "alias budget" in str(error.value.orig)


def test_deferred_checks_require_owner_until_commit(
    runtime: Engine, tenants: list[dict[str, Any]]
) -> None:
    own = tenants[0]
    before = tenant_snapshot(runtime, own["owner_id"])
    with pytest.raises(DBAPIError) as error, owner_transaction(runtime, own["owner_id"]) as conn:
        group_id = uuid4()
        base = {
            "owner_id": own["owner_id"],
            "collection_id": own["collection_id"],
            "domain": own["domain"],
        }
        insert(conn, "fp6_data.commercial_groups", {**base, "group_id": group_id})
        insert(
            conn,
            "fp6_data.commercial_alias_members",
            {
                **base,
                "group_id": group_id,
                "observation_id": own["o3"],
                "required_feature": "PAID_RECEIPT_CLAIM",
            },
        )
        conn.exec_driver_sql("SELECT set_config('app.owner_id','',true)")
    assert error.value.orig.sqlstate == "23514"  # type: ignore[union-attr]
    assert "missing group owner context" in str(error.value.orig)
    assert tenant_snapshot(runtime, own["owner_id"]) == before


@pytest.mark.parametrize("kind", ["source-budget", "group-minimum"])
@pytest.mark.parametrize("isolation", ["READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"])
def test_concurrent_bounds(
    tenants: list[dict[str, Any]], runtime: Engine, kind: str, isolation: str
) -> None:
    own = tenants[0]
    engine = make_engine("fp6_runtime_login")
    barrier = Barrier(2, timeout=10)
    identifiers = [uuid4(), uuid4()]
    if kind == "group-minimum":
        with owner_transaction(runtime, own["owner_id"]) as conn:
            insert(
                conn,
                "fp6_data.evidence_equivalence",
                {
                    "owner_id": own["owner_id"],
                    "collection_id": own["collection_id"],
                    "group_id": own["group_id"],
                    "observation_id": own["o3"],
                },
            )

    def worker(index: int) -> str:
        try:
            with engine.begin() as conn:
                conn.exec_driver_sql("SET TRANSACTION ISOLATION LEVEL " + isolation)
                conn.exec_driver_sql("SET LOCAL lock_timeout='5s'")
                set_owner(conn, own["owner_id"])
                conn.exec_driver_sql("SELECT count(*) FROM fp6_data.import_sources")
                barrier.wait()
                if kind == "source-budget":
                    insert(
                        conn,
                        "fp6_data.import_sources",
                        {
                            "owner_id": own["owner_id"],
                            "collection_id": own["collection_id"],
                            "source_id": identifiers[index],
                            "ordinal": 4 + index,
                            "record_count": 6000,
                            "adapter": "email_eml_v1",
                            "lifecycle": "active",
                        },
                    )
                else:
                    conn.execute(
                        text("DELETE FROM fp6_data.evidence_equivalence WHERE observation_id=:id"),
                        {"id": own["o2"] if index == 0 else own["o3"]},
                    )
            return "committed"
        except DBAPIError as error:
            return error.orig.sqlstate  # type: ignore[union-attr,no-any-return]

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(worker, (0, 1)))
        assert results.count("committed") == 1, results
        assert set(results) <= {"committed", "23514", "40001"}, results
        with owner_transaction(runtime, own["owner_id"]) as conn:
            if kind == "source-budget":
                assert (
                    conn.scalar(text("SELECT sum(record_count) FROM fp6_data.import_sources"))
                    <= 10000
                )
            else:
                assert (
                    conn.scalar(
                        text(
                            "SELECT count(*) FROM fp6_data.evidence_equivalence WHERE group_id=:id"
                        ),
                        {"id": own["group_id"]},
                    )
                    >= 2
                )
    finally:
        engine.dispose()
        with owner_transaction(runtime, own["owner_id"]) as conn:
            if kind == "source-budget":
                for identifier in identifiers:
                    conn.execute(
                        text("DELETE FROM fp6_data.import_sources WHERE source_id=:id"),
                        {"id": identifier},
                    )
            else:
                for observation in (own["o2"], own["o3"]):
                    conn.execute(
                        text(
                            "INSERT INTO fp6_data.evidence_equivalence VALUES "
                            "(:owner,:collection,:group_id,:observation) ON CONFLICT DO NOTHING"
                        ),
                        {
                            "owner": own["owner_id"],
                            "collection": own["collection_id"],
                            "group_id": own["group_id"],
                            "observation": observation,
                        },
                    )
                conn.execute(
                    text("DELETE FROM fp6_data.evidence_equivalence WHERE observation_id=:id"),
                    {"id": own["o3"]},
                )
