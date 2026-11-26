# Phase 6C-02 AI-assisted assurance evidence review

The review below is preserved as the **pre-remediation record** at `10982a5`.
The appended credential-remediation section records the subsequently authorized
fix, fresh results and current F01 disposition. Statements about an uncommitted
report, no active tests and unresolved F01 in the original record describe that
earlier evidence-only continuation, not the later remediation.

Date: 2026-11-26 (Asia/Calcutta).
PR: [#12](https://github.com/ankit8github/FootPrint/pull/12).
Reviewed implementation head: `10982a537c189677764d1d6fa8678ad8a956d540`.
Expected and verified PR base: `110b3c6353d155943bbf53798f5ec2b623dd3dd0`.

**Evidence review only. Production G-S3 remains OPEN. This is not independent
human security approval, permission to merge, or a completed adversarial audit.**
One synthetic fixture credential-separation defect is confirmed by source review.
Additional scenarios below are NOT TESTED; passing baseline tests do not resolve
them. No implementation fix is made by this report.

## Scope, provenance and repository state

The latest user instruction superseded the earlier active testing request after
a cybersecurity safety restriction interrupted that session. This continuation
only read existing source, reports and test receipts, queried existing GitHub PR
and CI records, and ran the existing read-only preservation checker. It did not
execute credential probes, authorization-bypass attempts, new database tests,
network attack simulations, migrations or rollback. No blocked activity was
retried through another tool or identity.

At entry, `git status --short --branch` showed a clean tracked worktree on
`experiment/phase6c02-tenant-schema-rls`. HEAD and its locally recorded upstream
both equal the reviewed head above; locally recorded `origin/main` equals the
expected base. Live GitHub metadata independently confirmed the same PR head and
base, `state=open`, `draft=true`, and `merged=false`. No fetch, commit, push, PR
metadata change or merge was performed in this continuation.

Existing ignored `.local/phase6c02-assurance/` and
`.local/phase6c02-validation/` artifacts were preserved, including completed logs,
helper scripts and fictional database directories. No pre-existing assurance
Markdown file or uncommitted tracked change was present. This report is the only
new repository file from the continuation and is left uncommitted. Credentials
and database contents are not copied into this report.

Evidence labels used here:

- **Verified now:** direct read of existing source/logs or live CI metadata/logs,
  or execution of the read-only preservation checker during this continuation.
- **Recorded execution:** an existing completed test log, not a newly executed
  test. Local logs are retained working artifacts, not signed attestations.
- **Prior-session observation:** retained conversation evidence with the limits
  identified below; not a fresh test or an independent verification.
- **NOT TESTED:** no adequate executed evidence was established for this review.
  Source concerns in this category are not presented as demonstrated exploits.

Inputs reviewed: the Phase 6C-02 plan and security report; Phase 6A task 6C-02,
S6A-03/04/08 and TM-01/02/04; experimental migration SQL/environment/revision;
role/context/disposal helpers; database runner, fixtures and 410-case test source;
preservation checker; and both CI workflows. The original design candidate and
ADR statuses are unchanged. No production functionality or Phase 6C-03 work was
added.

## Existing results actually verified

The following counts were read from completed evidence. No new database cases,
strict xfails, skips, or regression changes were added in this continuation.

| Evidence | Verified recorded result | Boundary |
| --- | --- | --- |
| `.local/phase6c02-assurance/baseline-410.log` | 410 passed in 64.09s; 410 passed in 64.91s; final roundtrip/ledger PASS line | Existing local run of the unchanged runner; not rerun now |
| `.local/phase6c02-assurance/backend.json` | All nine commands exit 0; pytest 1,061 passed in 449.78s | Existing Ruff lint/format, mypy, tests, OpenAPI/Phase 2/minimized contract checks, corpus validation and pip-audit records |
| `.local/phase6c02-assurance/frontend.json` | All ten commands exit 0; 284 unit tests, nine Chromium tests, seven preservation scenarios passed | Existing admission generation/type checks, contracts, lint, types, build and npm audit records |
| Existing scaffold CI logs | Upgrade, constraint enforcement, downgrade and re-upgrade PASS; no personal tables | Separate original scaffold, not a substitute for tenant tests |
| Read-only preservation checker, executed now | 193 historical blobs and all 252 base files unchanged | Git-filtered blob equality; no protected files regenerated |

The local frontend build retains a chunk-size warning. Its preservation command
explicitly reports that proposed performance budgets remain **FAILED**. A passing
preservation result does not close P5-F01 or establish acceptable performance.
The recorded dependency audits found no known vulnerabilities at execution time;
they are not a fresh vulnerability assessment.

Live GitHub job summaries and decoded logs were read again. Every listed job and
step reports success. The PR-triggered workflow lookup was made for the exact
reviewed head; the retained `delivery.json` also associates all four runs with
that head.

| Existing run | Job | Verified log evidence |
| --- | --- | --- |
| [PR tenant 45755964300](https://github.com/ankit8github/FootPrint/actions/runs/45755964300) | 139694521433 | 410 passed in 13.36s and 13.11s; roundtrip, ledger and preservation PASS |
| [Push tenant 45755958978](https://github.com/ankit8github/FootPrint/actions/runs/45755958978) | 139694503698 | 410 passed in 14.28s and 14.34s; roundtrip, ledger and preservation PASS |
| [PR regressions 45755964223](https://github.com/ankit8github/FootPrint/actions/runs/45755964223) | 139694521414 | 1,061 backend, 284 frontend, nine Chromium, seven preservation; scaffold roundtrip and audits PASS |
| [Push regressions 45755958704](https://github.com/ankit8github/FootPrint/actions/runs/45755958704) | 139694502939 | Same regression counts and scaffold/audit results PASS |

The tenant workflow uses PostgreSQL 17.12; the implementation report records
native local PostgreSQL 17.5. Frozen lint/format and both default and `db_tests`
mypy scopes passed in the existing tenant jobs. The unchanged original workflow
also passed contracts/corpus/minimized schema/registry, frontend checks and build.
Its decoded logs show **70 profiles / 32 complete batches** and admission manifest
SHA-256 `333c513165273846a4645c74ba604900266d88e10fb6eda1848e0195949b0699`.
The read-only preservation check reproduced that hash now. All 252 base files,
including the original scaffold workflow, corpus, source gate, engines, proposed
ADRs and Phase 6C-01 files, remain unchanged. The existing corpus-manifest pin
`53b4ff49c5b31e4fa5b2670c757c02058d0ffab3f6b0472fe8d198a86bdd36b1`
is preserved through that baseline equality.

These are implementation-head receipts. They do not constitute CI for a new
assurance commit: this documentation has not been committed or pushed.

## Role, RLS and integrity evidence

| Role | Existing implementation and exercised boundary |
| --- | --- |
| `fp6_owner` | NOLOGIN schema/table/function owner; unavailable through runtime membership |
| `fp6_migrator` / `fp6_migration_login` | Controlled owner membership for DDL; runtime cannot SET ROLE into it |
| `fp6_runtime` / `fp6_runtime_login` | Scoped footprint DML, reference SELECT and append-only ledger grants; no SUPERUSER/BYPASSRLS/ownership/DDL/TRUNCATE rights |
| `fp6_auth` / `fp6_auth_login` | Only fixed session-digest lookup; no direct session enumeration or footprint access |
| `fp6_restore` | NOLOGIN reserved capability with no data grants; restore workflow unimplemented |

The baseline makes actual restricted-login connections and asserts current_user;
it does not use a superuser SET ROLE to impersonate runtime for tenant SQL.
Catalog checks and negative operations substantiate the SQL privilege graph.
Credential separation is a different boundary and is deficient as F01 explains.

All **23 `fp6_data` tables plus `fp6_ledger.deletion_journal`** are enumerated by
the baseline. Existing catalog assertions require ENABLE + FORCE RLS, owner
`fp6_owner`, one policy to `fp6_runtime`, and identical owner-equality USING and
WITH CHECK expressions. Coverage includes consent/lifecycle controls, exclusions,
generations, deletion requests, outbox and idempotency. Auth bootstrap, shared
synthetic references and migration metadata are explicit grant-based exceptions.

The existing cases cover foreign reads/counts/joins and INSERT/UPDATE/DELETE in
both A-to-B and B-to-A directions, with before/after foreign snapshots and owned
positive controls. Immutable-table mutation rejection can be a grant denial,
not evidence that an UPDATE row policy was reached. Owner/collection/generation/
reference/domain/type negatives include INSERT, UPDATE and UPSERT. Forty fresh-key
FK cases specifically require SQLSTATE `23503`, avoiding duplicate-key rejection
as substitute FK evidence. Other association cases intentionally allow a set of
denial codes; their passing status alone does not identify which constraint fired.
CHECK/length cases accept `23514`/`22001`; explicit privilege cases use `42501`.

`set_owner` installs owner UUID and the current transaction ID through local,
parameterized settings. The invoker helper returns NULL for missing, empty,
malformed or stale context. Existing tests read all 24 tables under those states
and test a denied tenant-state INSERT. A one-slot SQLAlchemy pool verifies the
same backend PID after commit, rollback, application exception, SQL error and
statement-timeout cancellation, then no inherited owner and correct B context.
Deferred checks also require owner context until commit. This supports the stated
direct-pool behavior, not all failure modes or every missing-context mutation.

The sole SECURITY DEFINER function is `fp6_auth.lookup_session(bytea)`, with fixed
`pg_catalog` search_path and fully qualified static auth queries. It filters digest,
account state/epoch, revocation and expiry. Existing runtime/auth denials exercise
the intended grants. No footprint definer function or unrestricted worker role is
installed. No dynamic shadowing or new privileged-function attack was run now.

Typed finite domains, bounded columns, CHECKs, owner-scoped keys and composite FKs
cover the minimized evidence and projection graph. They do not implement semantic
classification, active-generation publishing, consent authorization or durable
deletion. No unrestricted JSON/arrays were found by the existing catalog check.

## Findings and disposition

### 6C02-AI-F01 — shared synthetic login password defeats credential separation

**Status:** unresolved; source-confirmed fixture/assurance defect.
**Severity:** Medium within this disposable experiment, with privileged-login
consequences if a synthetic runtime credential is treated as isolated. No deployed
production credential exposure or production exploit is demonstrated.

**Affected source:** `backend/experiments/tenant_db.py:26` uses the same
`FP6_TEST_PASSWORD` for every engine identity; provisioning at line 196 assigns
that value to migration, runtime and auth logins. The tenant workflow at lines
16 and 24 supplies that same fictional value to bootstrap PostgreSQL and the
helper. The retained local setup similarly initializes bootstrap and the helper
from one generated synthetic value. No credential value is reproduced here.

**Invariant violated:** the implementation plan's promise that ephemeral test
LOGIN roles use distinct passwords, and the intended separation between runtime,
auth and migration credentials. Separate role memberships remain meaningful for
an already authenticated runtime connection, but those checks do not establish
that possession of its password cannot authenticate as another test login.

**Conditions and source reproduction:** inspect the engine password selection,
the loop creating the three LOGIN roles, and the bootstrap environment assignment.
All select one value without a role-specific secret. An actor who knows that
synthetic value and can reach the disposable listener can supply another known
login identity; whether bootstrap authentication is reachable depends on that
cluster's authentication configuration. This source trace is sufficient to
confirm password reuse without making a new connection attempt.

**Existing observation and its limit:** the interrupted session recorded that
reuse authenticated as runtime, auth, migration and bootstrap in the fictional
local cluster, with bootstrap reporting superuser/BYPASSRLS and migration able to
assume the owner role. The helper script was retained, but its stdout was not
saved in a separate result artifact. This is prior-session conversation evidence,
not a newly verified machine receipt. It was not rerun and is not counted as a
baseline test. The finding's independently reviewable basis is the source above.

**Impact:** existing direct SQL results still describe the role under which each
test connected. They do not prove separation of credentials or containment of a
compromised test connection factory. The plan's distinct-password claim is false
at this head. The documented arbitrary-SQL owner-context trust limitation is a
separate issue. Public fictional CI credentials are intentional; this finding is
not a claim that a production secret was leaked.

**Proposed minimal remediation, not applied:** separate bootstrap, migrator,
runtime and auth credential inputs and provisioning values; keep privileged
credentials out of the runtime helper's environment/connection factory. Correct
the evidence and plan after implementation. A separately authorized regression
should verify distinct assigned credentials and their non-interchangeability
under the intended disposable authentication configuration. No new credential
test or strict xfail is introduced under this continuation's restrictions.

**Scope:** synthetic harness today; S6A-08/TM-04 credential design would require
review before any future production use. No application persistence is activated.
Return this for a separate remediation decision; successful CI does not close it.

### Historical finding — aggregate write skew, repaired before reviewed head

The implementation report documents concurrent source-budget excess and group
minimum violations at initial head
`833fd3423cc554f234a7525207e8928b2d2cff8a`. The retained
`concurrency-before.log` records two failed Repeatable Read reproductions with
both transactions committed. `concurrency-after.log` records six passing cases.
The reviewed SQL uses parent row-version UPDATEs for source, row-slot, alias and
deferred group checks; six committed baseline cases cover source inserts and
group-member deletes under Read Committed, Repeatable Read and Serializable.
They require exactly one commit, only `23514`/`40001` as alternative outcomes,
and a valid final bound. This was a within-owner integrity defect, not a recorded
cross-tenant leak. It is historical repaired evidence, not a new unresolved
finding. Broader concurrency coverage remains NOT TESTED below.

## Migration evidence and NOT TESTED scenarios

The existing runner first provisions a fresh explicitly opted-in fictional DB,
upgrades as migrator, runs all 410 cases, snapshots committed ledger rows ordered
by owner/event, downgrades, compares complete ledger tuples, re-upgrades, compares
again, and reruns all 410 cases. The preserved local log and live CI logs end in
the corresponding PASS line. The downgrade source retains `fp6_context`,
`fp6_guard` and `fp6_ledger`; it drops experimental data/auth/reference schemas
with CASCADE after the disposal guard. No destructive operation was run now.
This proves the exercised ledger roundtrip, not a production rollback strategy.

The existing guard test only creates an unexpected table inside `fp6_data` in a
rolled-back transaction and checks missing opt-in. It does not execute a full
object-corruption/downgrade refusal matrix. The broader report language about
inventory rejection must be read with that narrower executed coverage.

| Scenario | Status and resulting limitation |
| --- | --- |
| New credential or authorization-bypass reproductions | **NOT TESTED in this continuation** by explicit user restriction. F01 relies on source and qualified prior evidence; no fresh exploit claim |
| Unexpected schema, view, sequence, function or corrupted marker followed by downgrade | **NOT TESTED** as a complete dynamic matrix. Only the existing unexpected-table and missing-opt-in guard cases have recorded passing evidence |
| Non-table objects outside experimental schemas | **NOT TESTED.** `require_disposable` filters view/sequence/routine queries with `LIKE 'fp6_%'`, while `public` is an allowed schema. Behavior with external objects or dependencies is not established; no demonstrated CASCADE loss is claimed |
| Allowlisted routine-name overloads | **NOT TESTED.** Routine comparison uses schema/name, not full signatures. Whether an added overload survives the guard and affects rollback needs separate review |
| Missing expected tables or extra marker rows | **NOT TESTED.** Table guard rejects extras, not missing entries; marker uses one scalar result. A state-aware inventory/corruption assessment is needed; some missing tables are legitimate before upgrade/after downgrade |
| Concurrent source updates/deletes, alias insertion limits, observation/excluded-row collision, mixed mutations and orphan scenarios across all isolation levels | **NOT TESTED** beyond existing sequential integrity tests and the six source-insert/group-delete schedules. Shared parent-update code is not a substitute for each executed schedule |
| Reconnect after physical connection loss, process kill, PgBouncer/proxy modes or distributed jobs | **NOT TESTED.** Existing one-slot direct PostgreSQL pool/cancellation evidence does not establish these modes |
| Every table and mutation under every malformed/missing context variant | **NOT TESTED** as an exhaustive Cartesian matrix. Baseline covers all-table reads, a denied tenant-state INSERT, ordinary cross-tenant DML and deferred-commit context checks |
| Database error DETAIL, server logs, notices, statistics or monitoring disclosure | **NOT TESTED** as a complete disclosure audit. `hide_parameters=True` alone does not establish redaction of server-generated diagnostics; direct SQL errors remain an acknowledged TM-02 residual |
| Production auth/session integration, endpoint errors, lifecycle workers, restore/PITR, key custody and hosting controls | **NOT TESTED / unimplemented** in this experiment. Existing fictional API regressions do not provide DB-backed endpoint or operational assurance |

These omissions reflect the bounded existing evidence and the explicit stop on
further active security testing. None was silently converted into a pass or an
expected failure. Unverified guard concerns have no assigned exploit severity.
They require a separate review decision; this report makes no automatic fix.

## Threat mapping, residual risks and review gates

| Threat / gate | Supported conclusion | Residual or outstanding gate |
| --- | --- | --- |
| TM-01 | Existing restricted-login A/B CRUD, counts and joins exercise all 24 RLS tables | No DB-backed list/detail/filter/cursor/delete/receipt API exists; full endpoint isolation remains unproven |
| TM-02 | Composite associations, owner uniqueness, finite bounds, fresh-key FK negatives and unchanged snapshots have recorded passing evidence | Detailed SQL errors and semantic/service eligibility are unresolved; broader concurrency and disposal matrix remain NOT TESTED |
| TM-04 | SQL role flags/grants, FORCE RLS, local transaction context, direct-pool error/cancellation reuse and privilege denials have recorded passing evidence | F01 credential separation unresolved; arbitrary SQL can select owner context; other deployment pool/reconnect modes untested |
| G-S3 | Useful synthetic database evidence supports part of the gate | **Production OPEN**; no independent human approval, session-to-DB endpoint proof, deployment-pool proof or production operational assurance |

Owner context is deliberately selected by trusted server code. Runtime can set
custom settings and a compromised program able to issue arbitrary SQL can choose
another owner. This is already explicit in S6A-03/TM-04 and the implementation
report, and is not reported as a newly discovered production vulnerability or a
resolved attack. The transaction ID is a pool-safety fence, not authentication.
Superusers/authorized DB operators are also outside the row-policy guarantee.

The local retained ledger is not independent durable deletion delivery, backup
erasure, restore reconciliation or a completed deletion service. Encryption
envelopes are fictional placeholders; no real identity/provider, production
auth, storage activation, public route, save UI, deployment or beta is supplied.
Restore has no serving bypass, but its functional workflow is absent. Retention,
legal/hosting/vendor, operator and key-custody gates remain outstanding. Proposed
ADR statuses and prior open findings remain unchanged. Do not infer permission
to start 6C-03/04/05 or merge from these results.

## Evidence preservation and review commands

The implementation diff from base is still exactly 13 added files / 2,738
insertions with no base file modification. This continuation adds only this
report; it does not alter test assertions or prior evidence. After creation, HEAD
remains `10982a537c189677764d1d6fa8678ad8a956d540`, with this report untracked
until a separately chosen commit. There is no new push or CI run to report.

The following are read-only review commands, not database probes:

```powershell
Set-Location I:\FootPrint
git -c safe.directory=I:/FootPrint status --short --branch
git -c safe.directory=I:/FootPrint rev-parse HEAD
git -c safe.directory=I:/FootPrint diff --name-status 110b3c6353d155943bbf53798f5ec2b623dd3dd0 HEAD
Get-Content .local/phase6c02-assurance/baseline-410.log
Get-Content .local/phase6c02-assurance/backend.json
Get-Content .local/phase6c02-assurance/frontend.json
Set-Location backend
uv run --frozen python -m scripts.check_phase6c02_preservation
```

For traceability, the historical database runner command was
`uv run --frozen python -m scripts.check_tenant_database` from `backend`, only
after fresh disposable-cluster setup. It was **not executed in this continuation**.
Existing setup details remain in the security report and workflow; their presence
is not permission to rerun restricted testing or downgrade an existing database.

SHA-256 fingerprints of retained non-secret evidence, verified now:

| Local artifact | SHA-256 |
| --- | --- |
| `.local/phase6c02-assurance/baseline-410.log` | `e70398007e7b8f86047057137c198b506614182b53bbf568d3ed48a9ca385bb5` |
| `.local/phase6c02-assurance/backend.json` | `61a9b4cf622330fd5e2b757e119dd3b3f56c7e2e6d04c378f1be5b9591160ada` |
| `.local/phase6c02-assurance/frontend.json` | `6e748f02043cf8a50aeff0081f21f404aa3775b139ddeff45a4d361128683765` |
| `.local/phase6c02-validation/concurrency-before.log` | `5982cebc057d823fb74d00ecfb892c49681474aaa6355ec7e76f73b1c7a7d0cc` |
| `.local/phase6c02-validation/concurrency-after.log` | `e12c7615f225ebde4966ab75310a614ea7b0f10c081b0021da2f3ff1c3a8fb88` |
| `.local/phase6c02-validation/decoded-ci-evidence.json` | `cd035b45082373886964fdea61b7f5600c7f4c29ad5e008cc125a49d3d0d0e32` |
| `.local/phase6c02-validation/delivery.json` | `a567ceb0e5482172d49d58717d52ce60546712be1ac68311e039d93af9400de6` |

Local ignored evidence must remain available for review; it is not included in
the PR by this document. Public CI receipts provide the reviewable implementation
baseline. Fresh qualified technical/security and product-owner review, a separate
decision on F01 and untested concerns, and any expressly permitted follow-up
evidence are required. PR #12 remains draft, open and unmerged.

## Credential isolation remediation (subsequently authorized)

The user explicitly authorized F01 remediation and bounded synthetic-role
authentication regressions after the evidence-only review above. That authority
does not extend to other credential attacks, new bypass testing, production
integration or any of the unexecuted scenarios. This section supersedes F01's
earlier unresolved disposition only when its fresh results are recorded below.
The original report was backed up byte-for-byte before editing at
`.local/phase6c02-remediation/AI-ASSURANCE-before.md`, SHA-256
`f063ee8ffb2ae7bc2b8405fbef4f9326bd617545496c9561ec078946aed2f7fc`.
Its findings, qualifications, evidence fingerprints and NOT TESTED matrix remain
in this file as the historical record.

### F01 reproduction and applied fix

At the exact pre-remediation head `10982a537c189677764d1d6fa8678ad8a956d540`,
`test_engine` read one `FP6_TEST_PASSWORD` regardless of username, provisioning
assigned it to all three restricted logins, and CI initialized bootstrap with
that same value. The source trace and qualified prior-session observation above
are preserved. No additional old-credential probe was performed. The new
regression constructs only the four fixed synthetic login identities on the
recognized loopback fictional database, using each of their three other generated
credentials in turn. Successful authentication in any of those 12 cases is a
failure; refusal/timeout alone is insufficient, because each negative must report
password-authentication rejection. No credential guessing or unbounded loop exists.

The fix is limited to the synthetic harness:

- `LOGIN_ENV` explicitly maps bootstrap, migration, runtime and auth identities to
  `FP6_BOOTSTRAP_PASSWORD`, `FP6_MIGRATION_PASSWORD`, `FP6_RUNTIME_PASSWORD` and
  `FP6_AUTH_PASSWORD`. Every connection selects its login explicitly and reads
  only that login's credential. Unknown identities and missing/invalid inputs
  fail with fixed messages. `FP6_TEST_PASSWORD` supplies no fallback.
- `scripts.run_tenant_database` calls `secrets.token_hex(32)` independently four
  times and rejects any collision. Fresh provisioning independently rejects
  shared credentials before DDL. All actual restricted-role connections, grants,
  memberships and RLS behavior remain intact.
- The launcher supplies values through child-process environment, never command
  arguments, GITHUB_ENV, tracked files or uploaded artifacts. Setup diagnostics
  are suppressed and child regression output is redacted for all four generated
  values before printing. SQLAlchemy hides parameters. Provisioning suppresses
  statement/error/slow-query sampling for password DDL and replaces driver DDL
  exceptions with a fixed message.
- CI starts its own PostgreSQL 17.12 Docker container with a generated bootstrap
  credential, binds only loopback, and removes that new container/volume in its
  cleanup. The original scaffold workflow is unchanged. Native Windows setup
  uses PostgreSQL 17, an exclusive new `.local/fp6c02-disposable-<uuid>` directory,
  and a temporary initdb pwfile removed in a finally block. It stops its own
  server and retains database/log evidence, with no plaintext credential file.

The trusted fixture controller still needs all four credentials for bootstrap,
migrations and catalog assertions. This is not process isolation against that
controller, a host administrator or Docker administrator. A dedicated regression
removes the other three inputs and confirms a runtime-only connection still works.
No production connection factory, secret manager or identity provider is added.
Broader diagnostic disclosure remains NOT TESTED as recorded above; the narrow
password-DDL handling does not close that assessment.

`backend/db_tests/test_tenant_credentials.py` adds exactly **24 cases**: one
distinctness check, four successful own-credential connections, 12 ordered
wrong-role credential rejections, one runtime-only environment check, four
missing-input/no-legacy-fallback checks, one duplicate rejection and one unknown
login rejection. Authentication startup errors from libpq do not reliably expose
SQLSTATE, so those 12 tests require the explicit password-authentication failure
diagnostic; the original SQLSTATE-specific authorization/integrity assertions
are unchanged. The original 410-case suite only changes its bootstrap call to
name that identity explicitly; its security assertions are preserved.

### Fresh regression evidence and publication

**F01 disposition:** remediated in the synthetic harness, with the fresh local
regressions below passing. Independent technical/human review remains required.
No production vulnerability closure or production G-S3 completion is claimed.

| Fresh local validation | Result / retained artifact |
| --- | --- |
| PostgreSQL 17.5 fresh upgrade and full suite | **434 passed in 27.84s** in `.local/phase6c02-remediation/database-roundtrip.log` |
| Guarded downgrade, re-upgrade and full suite | **434 passed in 26.83s**, complete committed ledger tuples equal before/after; final runner PASS |
| Existing backend tests | **1,061 passed in 267.54s**; `.local/phase6c02-remediation/backend.json`, all nine commands exit 0 |
| Frontend / Chromium / preservation | **284 / nine / seven passed**; `.local/phase6c02-remediation/frontend.json`, all ten commands exit 0 |
| Frozen quality checks | Ruff lint/format, default and explicit DB-test mypy, contracts, corpus/minimized export, admission checks, build, pip-audit and npm audit pass |
| Baseline preservation | Read-only checker passes **193 historical / 252 base files**, admission pin unchanged; original scaffold workflow and all tenant migration files unchanged |

No skips, xfails or assertion relaxations were introduced. Existing performance
budgets remain **FAILED**, despite the seven passing preservation scenarios.
Fresh CI will be checked after publication; no pre-remediation run is substituted
for remediation CI. Exact published head and current push/PR receipts are recorded
in PR metadata and the delivery response, avoiding a commit embedding its own SHA.

Unexecuted guard corruption, concurrency combinations, physical
reconnect/proxy, diagnostic-channel, production endpoint and operational scenarios
remain explicitly **NOT TESTED** in the retained matrix. The new bounded
credential matrix does not authorize those activities or close production G-S3.

An initial native launcher attempt stalled before running DB tests because a
background PostgreSQL process inherited a captured setup-output pipe on Windows.
The launcher now sends setup output to DEVNULL. The newly created cluster was
stopped after checking its path and port; its files and failure log
`.local/phase6c02-remediation/database.log` were retained. A fresh cluster is used
for the corrected run. This failed setup is not counted as a passing DB run.
