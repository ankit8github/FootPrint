"""Committed fictional A/B graphs; every tenant INSERT uses the runtime login."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Connection, Engine, text

from experiments.tenant_db import owner_transaction, require_disposable
from experiments.tenant_db import test_engine as make_engine

NOW = datetime.now(UTC)


def insert(conn: Connection, table: str, row: dict[str, Any]) -> None:
    # Identifiers are test-source constants, values always parameters.
    columns = ", ".join(row)
    params = ", ".join(":" + key for key in row)
    conn.execute(text(f"INSERT INTO {table} ({columns}) VALUES ({params})"), row)


@pytest.fixture(scope="session")
def runtime() -> Iterator[Engine]:
    engine = make_engine("fp6_runtime_login", pooled=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def bootstrap() -> Iterator[Engine]:
    engine = make_engine()
    with engine.connect() as conn:
        require_disposable(conn)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def tenants(bootstrap: Engine, runtime: Engine) -> list[dict[str, Any]]:
    result = []
    for domain in ("fictional-clinic.test", "fictional-shop.test"):
        ids: dict[str, Any] = {
            key: uuid4()
            for key in (
                "owner_id",
                "collection_id",
                "source_id",
                "history",
                "empty",
                "group_id",
                "commercial",
                "finding_id",
                "unresolved",
                "transaction",
                "visit",
                "request_id",
                "event_id",
                "key",
                "directory_id",
                "o1",
                "o2",
                "o3",
                "o4",
                "o5",
            )
        }
        ids["domain"] = domain
        ids["digest"] = uuid4().bytes + uuid4().bytes
        with bootstrap.begin() as conn:
            insert(
                conn,
                "fp6_auth.users",
                {
                    "owner_id": ids["owner_id"],
                    "state": "active",
                    "auth_epoch": 1,
                },
            )
            # Placeholder ciphertext is explicitly synthetic; no encryption/key
            # custody integration is implemented or represented as validated.
            insert(
                conn,
                "fp6_auth.identity_links",
                {
                    "owner_id": ids["owner_id"],
                    "issuer_config": "synthetic-idp-v1",
                    "subject_lookup": ids["digest"],
                    "subject_ciphertext": bytes(48),
                    "nonce": bytes(12),
                    "key_version": 1,
                },
            )
            insert(
                conn,
                "fp6_auth.sessions",
                {
                    "digest": ids["digest"],
                    "owner_id": ids["owner_id"],
                    "auth_epoch": 1,
                    "created_at": NOW,
                    "last_seen_at": NOW,
                    "idle_expires_at": NOW + timedelta(minutes=30),
                    "absolute_expires_at": NOW + timedelta(hours=12),
                    "strength": "synthetic_mfa",
                },
            )
            conn.execute(
                text(
                    "INSERT INTO fp6_reference.organizations VALUES (:domain,'synthetic') "
                    "ON CONFLICT (domain) DO NOTHING"
                ),
                {"domain": domain},
            )
            insert(
                conn,
                "fp6_reference.directory_versions",
                {
                    "directory_id": ids["directory_id"],
                    "version": 1,
                    "domain": domain,
                    "realm": "synthetic",
                    "state": "active",
                    "expires_at": NOW + timedelta(days=1),
                },
            )
            insert(
                conn,
                "fp6_reference.action_eligibility",
                {
                    "directory_id": ids["directory_id"],
                    "version": 1,
                    "domain": domain,
                    "relationship_type": "likely_account",
                    "realm": "synthetic",
                },
            )
        with owner_transaction(runtime, ids["owner_id"]) as conn:
            owner = {"owner_id": ids["owner_id"]}
            base = {**owner, "collection_id": ids["collection_id"]}
            insert(
                conn,
                "fp6_data.tenant_state",
                {
                    **owner,
                    "consent_epoch": 1,
                    "revision": 0,
                    "lifecycle": "active",
                },
            )
            insert(
                conn,
                "fp6_data.consents",
                {
                    **owner,
                    "consent_epoch": 1,
                    "event_id": uuid4(),
                    "decision": "accepted",
                    "purpose": "synthetic-test-only",
                    "policy_version": "synthetic-policy-v1",
                    "notice_version": "synthetic-notice-v1",
                    "accepted_at": NOW,
                    "expires_at": NOW + timedelta(days=1),
                },
            )
            insert(
                conn,
                "fp6_data.collections",
                {
                    **base,
                    "current_generation": 1,
                    "lifecycle": "active",
                    "expires_at": NOW + timedelta(days=1),
                    "schema_version": "minimized-evidence-v1",
                    "parser_version": "phase2-normalized-v1",
                    "feature_version": "email_features_v1",
                    "context_version": "email_context_v1",
                    "fusion_version": "relationship_fusion_v1",
                    "assessment_version": "sensitivity_rules_v1",
                    "explanation_version": "phase4-explanations-v1",
                },
            )
            for generation in (1, 2):
                insert(conn, "fp6_data.generations", {**base, "generation": generation})
            for source, ordinal, count, adapter in (
                (ids["source_id"], 1, 5, "email_eml_v1"),
                (ids["history"], 2, 1, "browser_chrome_json_v1"),
                (ids["empty"], 3, 0, "email_eml_v1"),
            ):
                insert(
                    conn,
                    "fp6_data.import_sources",
                    {
                        **base,
                        "source_id": source,
                        "ordinal": ordinal,
                        "record_count": count,
                        "adapter": adapter,
                        "lifecycle": "active",
                    },
                )
            for index, key in enumerate(("o1", "o2", "o3", "o4", "o5")):
                history = key == "o5"
                unresolved = key == "o4"
                adapter = "browser_chrome_json_v1" if history else "email_eml_v1"
                kind = (
                    "site_visit_observed"
                    if history
                    else (
                        "unclassified_observation"
                        if unresolved
                        else (
                            "transaction_email_detected"
                            if key == "o3"
                            else "registration_email_detected"
                        )
                    )
                )
                insert(
                    conn,
                    "fp6_data.observations",
                    {
                        **base,
                        "observation_id": ids[key],
                        "source_id": ids["history"] if history else ids["source_id"],
                        "record_index": 0 if history else index,
                        "source_count": 1 if history else 5,
                        "adapter": adapter,
                        "kind": kind,
                        "domain": None if unresolved else domain,
                        "occurred_at": NOW,
                        "time_status": "valid",
                        "attribution": "browser_record" if history else "unverified_sender",
                        "issue_code": "NO_SUPPORTED_FEATURE" if unresolved else None,
                    },
                )
                if not unresolved:
                    feature = (
                        "VISIT_RECORDED"
                        if history
                        else ("PAID_RECEIPT_CLAIM" if key == "o3" else "ACCOUNT_REQUEST")
                    )
                    insert(
                        conn,
                        "fp6_data.observation_features",
                        {
                            **base,
                            "observation_id": ids[key],
                            "adapter": adapter,
                            "feature": feature,
                        },
                    )
                if key in ("o1", "o2"):
                    insert(
                        conn,
                        "fp6_data.context_evidence",
                        {
                            **base,
                            "observation_id": ids[key],
                            "required_feature": "ACCOUNT_REQUEST",
                            "code": "CLINIC_APPOINTMENT_PORTAL_CONTEXT",
                        },
                    )
            insert(
                conn,
                "fp6_data.excluded_rows",
                {
                    **base,
                    "source_id": ids["source_id"],
                    "record_index": 4,
                    "source_count": 5,
                    "adapter": "email_eml_v1",
                    "code": "INVALID_RECORD",
                },
            )
            insert(
                conn,
                "fp6_data.evidence_groups",
                {
                    **base,
                    "group_id": ids["group_id"],
                    "primary_observation_id": ids["o1"],
                },
            )
            for key in ("o1", "o2"):
                insert(
                    conn,
                    "fp6_data.evidence_equivalence",
                    {
                        **base,
                        "group_id": ids["group_id"],
                        "observation_id": ids[key],
                    },
                )
            insert(
                conn,
                "fp6_data.commercial_groups",
                {
                    **base,
                    "group_id": ids["commercial"],
                    "domain": domain,
                },
            )
            insert(
                conn,
                "fp6_data.commercial_alias_members",
                {
                    **base,
                    "group_id": ids["commercial"],
                    "domain": domain,
                    "observation_id": ids["o3"],
                    "required_feature": "PAID_RECEIPT_CLAIM",
                },
            )
            for finding, relation, observation, rationale in (
                ("finding_id", "likely_account", "o1", "ACCOUNT_RELATIONSHIP"),
                ("transaction", "transaction", "o3", "TRANSACTION_INDICATION"),
                ("visit", "visited", "o5", "VISIT_ONLY"),
                ("unresolved", None, "o4", "AMBIGUOUS_EVIDENCE"),
            ):
                root = {**base, "generation": 1, "finding_id": ids[finding]}
                insert(
                    conn,
                    "fp6_data.findings",
                    {
                        **root,
                        "kind": "relationship" if relation else "unresolved",
                        "domain": domain if relation else None,
                        "relationship_type": relation,
                        "issue_code": None if relation else "NO_SUPPORTED_FEATURE",
                    },
                )
                insert(
                    conn,
                    "fp6_data.finding_evidence",
                    {
                        **root,
                        "observation_id": ids[observation],
                        "evidence_role": "primary",
                    },
                )
                insert(
                    conn,
                    "fp6_data.assessments",
                    {
                        **root,
                        "evidence_state": "inferred" if relation else "unknown",
                        "confidence": "medium" if relation else "insufficient",
                        "priority": "medium" if relation else "unknown",
                        "rule_id": "unknown",
                        "retention_status": "unknown",
                        "data_sale_status": "unknown",
                        "evaluated_at": NOW,
                    },
                )
                insert(
                    conn,
                    "fp6_data.rationale_evidence",
                    {
                        **root,
                        "observation_id": ids[observation],
                        "code": rationale,
                    },
                )
                insert(conn, "fp6_data.assessment_limitations", {**root, "code": "UNKNOWN_CLAIMS"})
                for claim in (
                    "sender_authenticity",
                    "current_account",
                    "payment_completed",
                    "payment_credentials_retained",
                    "company_retention",
                    "data_sale",
                    "breach_status",
                ):
                    insert(
                        conn,
                        "fp6_data.unknown_claims",
                        {
                            **root,
                            "claim": claim,
                            "evidence_state": "unknown",
                            "confidence": "insufficient",
                        },
                    )
            insert(
                conn,
                "fp6_data.user_actions",
                {
                    **base,
                    "generation": 1,
                    "finding_id": ids["finding_id"],
                    "domain": domain,
                    "relationship_type": "likely_account",
                    "directory_id": ids["directory_id"],
                    "directory_version": 1,
                    "realm": "synthetic",
                    "status": "not_started",
                },
            )
            insert(
                conn,
                "fp6_data.deletion_requests",
                {
                    **base,
                    "request_id": ids["request_id"],
                    "source_id": ids["empty"],
                    "consent_epoch": 1,
                    "revision": 0,
                    "operation": "source",
                    "state": "pending",
                    "affected_count": 0,
                },
            )
            insert(
                conn,
                "fp6_data.outbox",
                {
                    **owner,
                    "event_id": ids["event_id"],
                    "request_id": ids["request_id"],
                    "consent_epoch": 1,
                    "revision": 0,
                    "state": "pending",
                    "journal_sequence": None,
                },
            )
            insert(
                conn,
                "fp6_data.idempotency_records",
                {
                    **owner,
                    "consent_epoch": 1,
                    "revision": 0,
                    "key": ids["key"],
                    "operation": "source",
                    "request_hmac": bytes(32),
                    "request_id": ids["request_id"],
                    "state": "pending",
                },
            )
            insert(
                conn,
                "fp6_ledger.deletion_journal",
                {
                    **owner,
                    "event_id": ids["event_id"],
                    "journal_sequence": 1,
                    "operation": "source",
                    "consent_epoch": 1,
                    "revision": 0,
                },
            )
        result.append(ids)
    return result


@pytest.fixture(params=[0, 1], ids=["A-to-B", "B-to-A"])
def pair(
    tenants: list[dict[str, Any]], request: pytest.FixtureRequest
) -> tuple[dict[str, Any], dict[str, Any]]:
    return tenants[request.param], tenants[1 - request.param]


def tenant_snapshot(engine: Engine, owner: UUID) -> dict[str, list[Any]]:
    from experiments.tenant_db import DATA_TABLES

    with owner_transaction(engine, owner) as conn:
        return {
            table: list(
                conn.exec_driver_sql(
                    f"SELECT to_jsonb(t) FROM {table} t ORDER BY to_jsonb(t)::text"
                )
                .scalars()
                .all()
            )
            for table in (*("fp6_data." + t for t in DATA_TABLES), "fp6_ledger.deletion_journal")
        }
