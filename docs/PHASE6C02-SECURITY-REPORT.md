# Phase 6C-02 security and migration report

Date: 2026-11-26 (Asia/Calcutta). Scope: disabled repository-only synthetic
PostgreSQL experiment. Base `110b3c6353d155943bbf53798f5ec2b623dd3dd0` was verified
against clean main and freshly fetched origin/main before branch creation.
Branch: `experiment/phase6c02-tenant-schema-rls`. The exact final head, open PR and
exact-head CI receipts are published in the PR metadata and delivery response;
embedding a commit's own SHA in its contents would be self-referential.

**Production G-S3 remains OPEN. No merge, deployment, real-data ingestion, identity
integration, provider connectivity, public route or production persistence is
authorized or demonstrated.** Fresh technical and product-owner review is still
required. AI-authored implementation/tests are not independent human approval.
ADR-015 through ADR-022 remain unchanged and PROPOSED. The prior 6C-01 merge
exception is consumed; it supplies no review approval for this change.

## Change inventory and compatibility

All changes are additions. The separate `backend/tenant-alembic.ini` and
`tenant_migrations` install experimental revision `6c02_0001`, with a separate
`fp6_guard.tenant_alembic_version`. They do not join the original Alembic graph.
`backend/experiments/tenant_db.py` supplies synthetic-only connection/context,
bootstrap, inventory and migration helpers; no normal application imports it.
`backend/db_tests` supplies committed A/B fictional graphs and direct SQL attacks.
The runner, preservation checker, separate workflow, plan and this report are
the remaining additions. No dependency, normal application, frontend, historical
test, engine, oracle, source gate, contract, registry or existing CI file changed.

| Application / schema | Compatibility and rollback |
| --- | --- |
| Existing app 0.1.0 / scaffold 0001 | Unchanged; app has no tenant connection or new repository/API; original scaffold check still sees metadata only |
| Synthetic helpers / tenant 6c02_0001 | Only tested pairing; exact pinned rule/schema versions and synthetic policies; no version fallback |
| Expand | Add isolated schemas/roles; no existing table transformation or data backfill |
| Application rollback | Stop experiment; leave schema, consent controls, outbox and ledger intact |
| Disposable test contract | Guarded downgrade drops only experimental auth/data/reference schemas; retains guard, context and entire ledger; re-upgrade restores the schema without deleting ledger receipts |
| Any future user-data contract | Destructive downgrade prohibited. Disable writes, retain accepted deletion/consent fences and journal, use reviewed forward repair or a compatible application rollback; independent restore/reconciliation review required |

The migration environment cannot independently connect, read `.env`, emit an
offline destructive script or target scaffold credentials. Provisioning requires
the exact fictional database name, explicit opt-in, no pre-existing objects or
experiment roles, and a dedicated cluster. Subsequent migrations/downgrades check
the marker and schema/table/routine inventories and reject unexpected views,
foreign tables, partitions and sequences. The marker is a test-environment guard,
not proof of data provenance or permission to mark a real database disposable.

## Role and privilege evidence

| Capability | Ownership / grants | Exclusions verified |
| --- | --- | --- |
| `fp6_owner` | NOLOGIN owner of experimental schemas, tables and functions | Not an app identity; no SUPERUSER/BYPASSRLS/CREATEDB/CREATEROLE/REPLICATION |
| `fp6_migrator` | NOLOGIN, can SET ROLE to owner through its controlled membership | No runtime/auth/restore membership in it; no superuser or RLS bypass |
| `fp6_runtime` | NOLOGIN capability inherited by actual `fp6_runtime_login`; scoped footprint CRUD, immutable input/event restrictions, reference SELECT, ledger SELECT/INSERT | No auth schema/function rights, DDL, TRUNCATE, schema/TEMP creation, policy/function creation, ownership, migration/restore role access or privileged predefined memberships |
| `fp6_auth` | NOLOGIN capability inherited by actual `fp6_auth_login`; only fixed digest lookup function | Cannot enumerate sessions, identity links or users; no footprint/ledger rights |
| `fp6_restore` | NOLOGIN reserved offline role, no data grants | No serving access or unrestricted worker/admin bypass; functional restore is not implemented |

Separate short-lived synthetic LOGIN roles exercise the real database privilege
graph. The migrator login uses SET ROLE only for DDL. Adversarial SQL connects
directly as runtime/auth logins; tests assert `current_user`, and do not impersonate
them from the bootstrap superuser. Bootstrap provisions roles and fictional
auth/reference rows and inspects catalogs; it is not used as tenant-isolation
evidence. Test credentials have no provider or production access.

PUBLIC receives no database privileges, experimental schema access or function
execution. Runtime has CONNECT only at database level and cannot create temporary
objects. Every personal table is owned by `fp6_owner`, and runtime cannot disable
RLS, TRUNCATE, DROP/ALTER, change the migration version, create policies/functions,
edit reference data or SET ROLE to owner/migrator/restore. Catalog tests inspect
flags, memberships, table privileges, policy expressions and definer functions.

The sole SECURITY DEFINER function is `fp6_auth.lookup_session(bytea)`: fixed
`pg_catalog` search path, fully qualified static query, exact digest, account
state/epoch, revocation and idle/absolute expiry checks, returning only owner,
epoch and bounded strength. It has no footprint reference or dynamic SQL. Runtime
cannot call it. No production auth repository, OIDC integration, encryption/key
custody, revocation workflow or auth writer is implemented. Encrypted-subject
columns are bounded envelopes; fixture ciphertext is explicitly placeholder bytes.

## RLS and constraint coverage

All **23 `fp6_data` tables plus `fp6_ledger.deletion_journal`** have ENABLE and
FORCE RLS, one policy restricted to `fp6_runtime`, and identical USING/WITH CHECK
owner equality. Coverage includes tenant_state, consents, collections, generations,
import_sources, observations, observation_features, context_evidence, excluded_rows,
evidence_groups, evidence_equivalence, commercial_groups, commercial_alias_members,
findings, finding_evidence, assessments, rationale_evidence,
assessment_limitations, unknown_claims, user_actions, deletion_requests, outbox
and idempotency_records. Catalog enumeration must equal the expected table set;
adding an uncovered lifecycle table cannot silently pass.

The three isolated auth tables are the bootstrap exception. The three shared
reference projections contain synthetic domains/eligibility only, are runtime
read-only, and carry no tenant activity. Guard/version metadata are DDL-only.

`owner_transaction` starts one transaction and parameterizes local owner context
and its full PostgreSQL transaction ID. The invoker-only owner function returns
NULL for missing, empty, malformed or stale context, including accidentally
session-scoped settings from an earlier transaction. Deferred group checks also
require the original owner context through commit. No footprint definer function
or worker bypass exists. PostgreSQL documents both the scope of transaction-local
settings and the limits of forced RLS, including superuser/BYPASSRLS and TRUNCATE:
[settings](https://www.postgresql.org/docs/17/functions-admin.html#FUNCTIONS-ADMIN-SET),
[RLS](https://www.postgresql.org/docs/17/ddl-rowsecurity.html).

| Data family | Executable integrity |
| --- | --- |
| Tenant/control/consent | Owner FKs; finite lifecycle/decision/purpose/policy/notice; bounded epoch/revision; unique owner/epoch and immutable consent events |
| Collection/source/rows | One collection per owner; pinned seven version fields; collection/generation cycle checked at commit; ordinals 1–20; serialized total budget 10,000; source/adapter/count composite FK; row index bounds and cross-table occupied-row rejection |
| Minimized evidence | Six kinds, exact 13 synthetic domains, adapter/attribution/time union, finite feature/issue codes, 1970–2100 timestamps; no JSON, arrays, arbitrary prose or raw identifiers |
| Context/groups | Account feature FK and unresolved-context rejection; same-collection member FKs, primary membership FK, deferred minimum two equivalence members / one alias member; at most eight aliases per observation; domain + commercial feature FKs |
| Findings/support/assessment | Relationship/unresolved discriminated union; owner/collection/generation keys; same-root support membership; rationale must reference both assessment and support; finite rules/priority/confidence/limitations; unknown-only retention/sale and seven bounded unknown-claim types |
| Actions/reference | Non-null domain/type relationship FK excludes unresolved targets; exact directory/version/domain/type/realm eligibility FK; synthetic realm only; not_started/opened only; no URL or live directory mechanism |
| Deletion/outbox/idempotency | Owner/collection/source scope, finite operation/state/counts, epoch/revision request FK, bounded 32-byte keyed digest, owner/epoch/key uniqueness; acknowledged outbox requires journal sequence; append-only local ledger |

These constraints establish relational structure, not classification truth,
complete intake admission, all seven claim-row completeness, cryptographic
ciphertext validity, active-generation serving, consent enforcement at publish,
directory freshness/revocation, or full duplicate-content equality. Those service
semantics remain later authorized work. Deletion targets are currently structural
FKs to retained source/control rows; final tombstone detachment and physical
cleanup need a reviewed 6C-04 migration/workflow, not an assertion that deletion
already works. No raw-hash deduplication or cross-collection correlation exists.

## Adversarial evidence and threat mapping

The final matrix has **404 cases**, executed in full before and after downgrade /
re-upgrade. No skips, xfails or raised limits are used. Both A→B and B→A run.
Every RLS table has populated owner rows and foreign read/count/join/INSERT/
UPDATE/DELETE attacks. Whole tenant snapshots before/after verify that foreign
data and generations remain unchanged; matching-owner writes are positive
controls. Immutable-table mutation denial is explicitly a privilege control.

| Threat / gate | Evidence and boundary |
| --- | --- |
| TM-01 / G-S3 | Direct SQL against all 24 RLS tables, foreign IDs and joins, both directions; no foreign rows/counts or mutation. Existing 6B/6C-01 ASGI ownership/auth/admission negatives also pass as part of 1,061 backend regressions. No new DB-backed API endpoint exists; full endpoint proof remains missing |
| TM-02 / G-S3 | INSERT, UPDATE and ON CONFLICT attempts against mixed owner/collection/generation/reference/domain/type. Forty fresh-key cases require SQLSTATE 23503 specifically, avoiding duplicate-key false evidence; rejected operations leave no partial owned/foreign rows. CHECK/union/uniqueness/budget/deferred-membership negatives and unresolved-action rejection pass |
| TM-04 / G-S3 | Actual restricted logins; all-table context denials; one-connection SQLAlchemy pool with identical backend PID after commit/rollback/application exception/SQL failure/statement cancellation; no inherited owner on next transaction; stale session settings fail; missing context through deferred commit fails; `row_security=off` errors instead of bypassing |
| TM-04 / privilege boundary | Catalog assertions plus attempted ALTER/TRUNCATE/DROP/CREATE POLICY/FUNCTION/SCHEMA/TEMP, migration mutation, reference mutation, journal deletion, SET ROLE and grants all deny; auth and footprint cannot enumerate each other's tables |

Generic API error behavior is covered only by the unchanged fictional ASGI tests.
Direct SQL still exposes database constraint error classes; future repositories
must map them to fixed external errors without bind/constraint details.

## Reproduction and migration results

Use a new dedicated cluster each time; the runner refuses an existing provisioned
database/role set. This example is local-only Docker, with an untracked generated
test password. The original scaffold Compose/CI job is independent and unchanged.

```powershell
$env:FP6_SYNTHETIC_ONLY = 'phase6c02-disposable-fictional-only-v1'
$env:FP6_TEST_PASSWORD = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
$env:FP6_TEST_PORT = '55433'
docker run --name fp6c02-disposable --detach `
  -e POSTGRES_USER=fp6_bootstrap -e POSTGRES_DB=fp6c02_synthetic `
  -e "POSTGRES_PASSWORD=$env:FP6_TEST_PASSWORD" `
  -p 127.0.0.1:55433:5432 postgres:17.12-bookworm
# Wait for pg_isready to succeed before running the next command.
docker exec fp6c02-disposable pg_isready -U fp6_bootstrap -d fp6c02_synthetic
Set-Location backend
uv sync --frozen
uv run --frozen python -m scripts.check_tenant_database
uv run --frozen python -m scripts.check_phase6c02_preservation
```

For already provisioned **synthetic** review databases only, set the same test
environment and run `uv run --frozen pytest db_tests -q`. Do not substitute an
application/real database or run generic Alembic downgrade. The CI workflow
`.github/workflows/phase6c02.yml` gives the equivalent fresh PostgreSQL 17.12
service setup with no production secrets. It runs lint, format, both type-check
scopes, preservation and the full migration/test runner separately from scaffold.

Local validation used PostgreSQL **17.5**, Python 3.11, Node **22.15.0**, uv
**0.9.29** and frozen dependencies. CI supplies the pinned PostgreSQL **17.12**
and Python **3.11.9**; exact-head CI receipts must be checked separately. The
native test clusters listen only on 127.0.0.1 and never connect to providers.
Local test credentials/logs/databases are ignored artifacts, not product files.

| Fresh validation | Result |
| --- | --- |
| Tenant upgrade → SQL/constraint/role matrix | 404 cases pass |
| Recognized disposable downgrade | Succeeds; data/auth/reference schemas removed, all committed ledger receipts byte-for-byte preserved |
| Re-upgrade → repeated full matrix | 404 cases pass; prior ledger receipts still identical |
| Original scaffold migration check | Unchanged script passes upgrade, CHECK, downgrade, re-upgrade on its own fresh database; no personal tables |
| Backend regressions | 1,061 passed; no skips/xfails |
| Frontend regressions | 284 passed |
| Chromium / production preservation | Nine / seven passed |
| Frozen lint/format/types/contracts/corpus/schema/registry/build/audits | Pass; both dependency audits report no known vulnerabilities |
| Historical / base preservation | 193 historical Git blobs and all 252 base files unchanged; original scaffold workflow identical |
| Phase 6C-01 pins | 70 profiles / 32 batches reproduced unchanged; admission manifest SHA-256 `333c513165273846a4645c74ba604900266d88e10fb6eda1848e0195949b0699`; corpus manifest remains `53b4ff49c5b31e4fa5b2670c757c02058d0ffab3f6b0472fe8d198a86bdd36b1` |

Early construction runs found driver percent-placeholder handling, omitted
explicit composite reference columns and a too-short strength bound. These were
corrected before final validation. A test selected an already-unresolved root and
mistook a duplicate-key denial for its intended union CHECK; selection is now
explicit. Fresh-key SQLSTATE-specific FK tests were added to prevent that class
of false evidence. Final privilege/isolation/pool tests reveal no runtime role
bypass, leaked transaction owner or persisted cross-tenant association within
the exercised model. This is bounded test evidence, not proof of absence.

## Limitations and outstanding gates

RLS assumes a trusted server chooses owner from an authenticated principal.
Runtime can set custom settings and a compromised app/arbitrary SQL can choose a
different owner; this is the documented TM-04 residual, not a claim of protection
against SQL injection or privileged DBA access. Parameterized helpers, restricted
roles and future endpoint authorization remain necessary. UUIDs/enums/bytes also
cannot eliminate every covert channel in a compromised program.

The pool evidence is for direct PostgreSQL connections and SQLAlchemy's one-slot
QueuePool, including statement-timeout cancellation. PgBouncer modes, network
loss, process kill, distributed workers and a production proxy are untested.
The owner transaction ID fence is not an authentication secret. Auth lookup is a
digest oracle only for authorized auth code, with no public endpoint; production
rate controls and identity encryption/key custody are unimplemented.

The retained ledger is a local minimal projection, not independent durable
journal delivery, backup deletion, PITR, restore release, or lifecycle completion.
There are no deletion workers, recomputation executor, production auth/persistence
API, consent UI, real directory verification or 6C-03/04/05 implementation. Retention
durations remain unresolved, and synthetic policy versions approve no real policy.

Qualified independent technical/security review, product-owner review, endpoint
integration proof, active lifecycle/epoch enforcement, semantic engine equivalence,
durable deletion/restore, operator/key custody and legal/hosting/vendor decisions
remain outstanding. G-S3 production completion is not claimed; P5-F01 performance
budgets and prior open findings remain open. No merge or next phase follows from
successful checks. Any new bypass, context leak or persisted cross-tenant
association must stop the experiment for review.
