# Phase 6C-02 implementation plan

Date: 2026-11-26 (Asia/Calcutta). Base: `110b3c6353d155943bbf53798f5ec2b623dd3dd0`.
Scope: repository-only synthetic PostgreSQL experiment and an open, unmerged PR.
The requesting user's Phase 6C-02 instruction supersedes the consumed 6C-01
exception only for this work. No ADR approval, deployment, real identities,
provider integration, public write route, save UI or 6C-03/04/05 work is implied.
Fresh technical and product-owner review is required before merge.

## Preflight and reviewed inputs

Clean main and fetched origin/main matched the exact base above. No AGENTS.md was
found. Read 6C-02 in PHASE6A-IMPLEMENTATION-PLAN, S6A-03/04/08 and TM-01/02/04.
`03-pv1-schema.sql` is an unchanged, unapproved candidate: its JSON metadata,
unbounded labels, hashes, relationship-only assessment target and action-domain
gap are rejected. ADR-015 through ADR-022 remain PROPOSED.

Existing `backend/migrations` has only `0001_scaffold`, a loopback pv1_dev Alembic
environment and metadata table. `scripts.check_database` rejects personal tables.
`.github/workflows/phase0.yml` runs frozen backend/client/corpus/registry checks,
the original scaffold roundtrip, nine browser and seven preservation scenarios.
All these files and the Phase 6C-01 contract/catalog/source/oracle bytes stay intact.

## Schema inventory and constraints

A separate Alembic configuration and version table install the following schemas;
they are never discovered by the scaffold environment or normal HTTP application.

| Schema / tables | Required integrity |
| --- | --- |
| auth bootstrap: users, identity_links, sessions | Random internal owner, bounded states/epochs; configured synthetic issuer, encrypted subject envelope plus keyed digest, session digest only, bounded times/strength/revocation; no email/profile/token |
| footprint: tenant_state, consents | Owner fence, epochs/revision, finite lifecycle, synthetic-only policy/notice/purpose, immutable consent events |
| collections, generations, import_sources | One collection per owner, bounded source ordinal/count, pinned contract/rule versions, explicit expiry/lifecycle; composite collection/generation keys |
| observations, observation_features, context_evidence, excluded_rows | Six kinds; exact synthetic domains and finite codes; adapter/time/attribution consistency; bounded row positions; context references an eligible feature |
| evidence_groups, evidence_equivalence, commercial_groups, commercial_alias_members | Collection-local random UUIDs; composite member/source/collection/domain keys, no raw hash/order identifier |
| findings, finding_evidence, assessments, rationale_evidence | Unified relationship/unresolved union; generation-scoped roots/support; rationale must reference both assessment and support membership; finite assessment/rationale/unknown vocabulary |
| reference: organizations, directory_versions, action_eligibility | Migrator-owned synthetic reference rows only; exact domain/type/realm/version eligibility, no arbitrary URL/prose or live checking |
| user_actions | Relationship-only composite root/domain/type FK plus matching reference eligibility; not_started/opened only |
| deletion_requests, outbox, idempotency_records | Owner/epoch/revision scope, source/collection references, finite operations/states/counts, UUID receipt, bounded journal sequence and keyed digest only; no jobs carrying observations |

Use NOT NULL, finite CHECKs, owner-scoped PK/UNIQUE and composite FKs throughout.
No unrestricted JSON, arrays of prose, raw identifiers or generic metadata column.
Referential structure is not rule classification, consent enforcement, atomic
recomputation or a working deletion journal. These remain later phases.

## Role and privilege matrix

| Role | Login / rights | Explicit exclusions |
| --- | --- | --- |
| fp6_owner | NOLOGIN schema/table/function owner | Never granted to runtime/auth/restore |
| fp6_migrator | NOLOGIN membership in owner; SET ROLE during controlled migrations | No application use; no superuser/BYPASSRLS |
| fp6_runtime | NOLOGIN capability; synthetic test login inherits only it; scoped footprint DML and reference SELECT | No auth usage, ownership, DDL, TRUNCATE, role creation, owner membership, BYPASSRLS |
| fp6_auth | NOLOGIN capability; separate synthetic login; auth lookup function only | No footprint rights or bulk session table grants |
| fp6_restore | NOLOGIN reserved offline role, no data grants | No runtime bypass or serving; restore/reconciliation not implemented |

Provision cluster roles only in a fresh recognized disposable cluster/database.
Ephemeral test LOGIN roles use distinct connections/passwords, never SET ROLE from
the superuser for adversarial evidence. Bootstrap superuser only provisions roles
and executes fixture setup; migrations execute as owner through migrator context.
Revoke PUBLIC schema/function defaults, schema CREATE and database TEMP/CREATE
for test logins; inspect memberships and privileges, not just role flags.

## RLS and owner context

Every footprint table, including controls, consent, generations, exclusions,
deletion requests/outbox/idempotency, has ENABLE + FORCE RLS with owner equality
in USING and WITH CHECK. Auth bootstrap and shared immutable reference tables
are explicit exceptions protected by grants, not tenant policies.
The helper uses parameterized transaction-local owner and transaction identity;
context missing, empty, malformed or from a previous transaction denies access.
Tests also deliberately install session-level stale settings to prove fail-closed
behavior. No SECURITY DEFINER footprint reader or unrestricted worker bypass.
Workers must establish the same owner-scoped transaction context as runtime.
The trusted server would select owner after authentication; arbitrary SQL or a
compromised app able to choose context remains outside RLS's security guarantee.

## Executable evidence

Separate disposable PostgreSQL 17 CI job: fresh database allowlist + explicit
synthetic opt-in + marker; reject unexpected schemas/tables before migration or
downgrade. Upgrade, seed fictional A/B through actual runtime logins, execute
direct SQL CRUD/joins/UPSERT negatives in both directions, compare complete B
state after failed A mutations, inspect every policy and role, test composite
owner/collection/generation/domain/type references and finite constraints.
Exercise a one-connection pool after commit/rollback/exception and failed
transaction, malformed/missing/stale context, auth/footprint privilege separation,
DDL/TRUNCATE/role denial. Test safe auth digest lookup without session enumeration.
Run downgrade and re-upgrade only in this marked synthetic database; retain
outbox evidence across downgrade. Add read-only historical/6C-01 preservation
verification. Run the existing frozen pipeline unchanged and record exact counts.

TM-01 maps to owner-scoped CRUD/joins and unchanged API fixture regressions;
TM-02 to composite FKs, unions and negative association writes; TM-04 to actual
restricted connections, catalog privilege inspection and pool/error reuse.
G-S3 receives synthetic database evidence only: no durable API endpoints are
built or certified and production G-S3 remains OPEN.

## Compatibility and rollback

Existing application 0.1.0 continues using no new schema; scaffold 0001 is
unchanged. Experimental schema `6c02_0001` is consumed only by synthetic helpers.
Expand is additive, with no app configuration wiring. App rollback disables the
experiment without dropping anything. Contract removal with user data is never
authorized: disable writes, preserve consent/deletion fences and journal, use a
reviewed forward repair or compatible application rollback. Test downgrade drops
only experiment footprint/auth/reference schemas after guard validation, while
retaining a separate minimal deletion ledger and migration marker; it does not
erase deletion evidence. Future retention, restore, encryption custody, endpoint
authorization and semantic service checks require independent review.
