# C03-COMP-01: generation-scoped implementation provenance candidate

Prepared 2026-11-26 for [draft PR #13](https://github.com/ankit8github/FootPrint/pull/13).

**Proposal validated on a fresh disposable synthetic database. Separate technical
and product-owner adoption decision PENDING. Do not merge or activate persistence.**
The new schema provides a typed target for implementation selection, including
zero-finding generations. It does not complete or execute the provenance adapter.
Phase 6C-03 remains incomplete; survivor implementation, executor failure work and
Phase 6C-04/05 were not started.

## Exact state and historical evidence

Preflight worktree was clean on `experiment/phase6c03-shared-rules`. Local HEAD
and the live remote branch matched
`511dfee080d3bcd3c68aaa35ec1474700ff0cf63`. Local main, origin/main, merge-base
and live remote main matched `2038c65554501b7f0a099976ea07b75606cb7ff7`.
GitHub independently reported PR #13 draft, open and unmerged with these refs.
No AGENTS.md was found. Commands used command-local Git safe-directory settings;
no global Git setting changed. The ordinary sandbox helper failed before launch;
authorized commands used the escalated helper.

Read the [completion report](PHASE6C03-COMPLETION-REPORT.md), immutable package
manifest, storage-compatibility decision and counterexample test; original
6C-03 plan/security/performance/indexing/adoption records; the 6C-02 plan and
security/migration report, SQL, guards, roles and tests; and S6A-04/06/12.
All **312 preflight blobs**, **270 main/base blobs**, **285 pre-experiment protected
blobs**, and **444 snapshotted prior source/evidence files** remain unchanged.
This includes both 6C-02 migration files, all semantic-version fields, package
identities, original registry, 70 immutable profiles and historical receipts.

The old `storage-compatibility.json` and its test retain their historical STOP:
the original schema cannot distinguish implementation packages. This separate
candidate supplies a new target without rewriting that finding or any old report.
The two historical synthetic login failures retain **cause NOT ESTABLISHED**.
Their receipts and prior Windows native page-error evidence remain unchanged.
No new full local login/backend run or cause diagnosis is claimed.

The exact candidate commit is supplied with the delivery and in ignored local
`final-state.json`; a committed document cannot contain its own commit hash.
This is a local, separately reviewable additive commit. **No push or new CI was
triggered:** the existing completion workflow automatically executes the partial
adapter tests, which this task explicitly excludes. PR #13's remote HEAD remains
`511dfee080d3bcd3c68aaa35ec1474700ff0cf63`, draft/open/unmerged. Existing CI
receipts belong to that prior head and do not validate this candidate.

## Exact SQL and migration inventory

New independent Alembic configuration: `backend/provenance-alembic.ini`;
environment: `backend/provenance_migrations/env.py`; revision
**`c03_comp01_0001`**, with its paired SQL file. The graph has no parent revision
and requires the separate tenant graph to be exactly `6c02_0001`. Its version
table is `fp6_guard.provenance_alembic_version`. Neither existing migration graph
discovers it. There is no offline URL/script mode or application connection.

| Object | Exact purpose and restrictions |
| --- | --- |
| `fp6_reference.implementation_packages` | Four bounded non-null fields: revision, manifest SHA-256, worker SHA-256 and pure-prefix SHA-256. Revision PK; unique four-field identity; CHECK permits exactly the two immutable tuples below. Both rows are seeded before RLS. |
| `fp6_data.generation_implementations` | Owner UUID, collection UUID, generation integer 1–1,000,000, plus the same four package fields. PK `(owner_id, collection_id, generation)`; non-null CHECK fixes selection to `indexed-r1`. No JSON, unrelated metadata, raw source identifiers or raw-file hashes. |
| `exact_package` FK | All four binding identity fields reference the exact recognized registry tuple. A known revision with another package's hash fails. |
| `bound_generation` FK | Binding's complete owner/collection/generation references `generations`; deferred initially to permit atomic cyclic creation. No cascade. |
| `implementation_required` FK | Added to existing `generations`, referencing the binding's complete composite PK. Immediate and validated. Every visible inserted generation already has a binding, including empty generations. |
| `fp6_context.bind_implementation()` | Invoker trigger, fixed `pg_catalog` search path, qualified static SQL. BEFORE INSERT creates the fixed binding first. BEFORE UPDATE rejects any generation key change. No caller package argument, GUC selection or fallback. |
| `fp6_context.immutable_implementation()` | Invoker trigger rejecting identity UPDATE/DELETE and TRUNCATE. Separate row and statement triggers cover both added tables. |
| RLS and grants | Both added tables ENABLE and FORCE RLS. Binding uses the original owner-context equality in USING and WITH CHECK, only for `fp6_runtime`. Runtime gets binding SELECT/INSERT, needed by the invoker trigger; no UPDATE/DELETE/TRUNCATE/DDL. Package SELECT policy permits runtime and the migration owner; runtime has SELECT only. PUBLIC rights/function execution revoked. No new SECURITY DEFINER, role, membership or bypass. |

The original owner/collection/generation cycle and one-collection-per-owner
constraint remain. The binding reaches its collection through the unchanged
generation FK. Existing seven collection version CHECKs, tenant revision/consent
bounds, ownership policies, budgets, immutable-input restrictions and ledger
remain identical. The candidate adds the generation FK/trigger; it changes no
old column, policy, grant, routine or constraint definition. Catalog snapshots
verify the old columns, constraints, policies, grants and function definitions.

New Python files are the explicit candidate guard/controller, test-only catalog
compatibility plugin, fresh-cluster launcher, SQL test controller, preservation
checker and two provenance test files. The guard recognizes only the intact old
inventory plus the three named added tables and two routines. Unknown schemas,
tables, views, foreign/partition/sequence objects, routines and overloads reject.
No source admission, original fixture values or application import is changed.

## Package identity and version selection

The existing manifest is retained byte-for-byte at
`backend/experiments/rule_packages/manifest.json`. Its hash fixes the original
semantic registry, engine/source/build/toolchain identities and both packages.
SQL tests compare the candidate's literals directly with that unchanged file.

| Identity | SHA-256 |
| --- | --- |
| Manifest, both packages | `7485ac86c2cd9502e1414d68df7a930ae531b209706d44b8161a736ec7e24055` |
| `historical-v1` worker | `69fcc47c8b0890c488900b4afe875aa7ce19faa6e257a691ad371fd53edff064` |
| `historical-v1` pure prefix | `73dbb73013b2a8ff0c364312adb6820b02a6de9ccb0d60ffd7adc9bc8cd58bb5` |
| `indexed-r1` worker | `f4170b61857e2ae673332e4d57cd01cab5214ede7f4c3b3abef390221258670a` |
| `indexed-r1` pure prefix | `5e980c1c1856226ef6b2ce35b9b4eb651d5860139ba6041a4ffe76ffb262d1e7` |

New generations under this schema select **only `indexed-r1`**, through fixed
server SQL and a CHECK. Supplying `historical-v1`, an unknown revision, an empty
revision, altered hashes or mismatched worker/prefix identity fails. Direct
runtime binding INSERT cannot commit an orphan or replace the automatic binding.
Recognizing `historical-v1` in the registry preserves its identity and offline
reproducibility; it does not allow client-selected replay into this schema.

A later implementation choice needs a separately reviewed migration with new
immutable identities, explicit selection/compatibility rules and regression
evidence. Do not update either old row/hash, reinterpret semantic versions or
silently switch this trigger. No historical package or oracle was repinned.

This records **server-selected implementation identity**, not cryptographic
proof that a worker ran. The future authorized adapter must verify actual
execution identity against the selected binding before any result publication.
No result mapper, schema projection, save endpoint or worker is run here.

## Creation, reading, deletion and rollback contract

Creation uses one owner-scoped transaction. A generation INSERT automatically
creates its binding; the immediate FK prevents an unbound generation read even
inside that transaction. The deferred reverse FK rejects orphan bindings at
commit. The original deferred collection/current-generation FK remains. A
second connection sees neither generation nor binding before commit, and both
after commit. Tests also publish an empty generation through the original
current-generation pointer and force all constraints immediately.

This establishes binding completeness. Consent/lifecycle fencing, complete
findings/support publication, active-generation serving, stale-worker rejection
and deletion recomputation still require the unfinished adapter/service design.
No such serving path exists or is certified by these SQL tests. The original
trusted-server owner-context assumption remains: arbitrary SQL that can select
another owner's context is outside its authentication guarantee.

Generation and binding identities are immutable. Runtime cannot remove a binding;
deleting its generation fails the deferred reverse FK. Deleting and reinserting
the same generation in one transaction collides with the retained binding.
There is no cascade or UUID/key reuse escape. Both owner directions and both
Read Committed/Repeatable Read races reject mutation and preserve the snapshots.
Generation cleanup, physical collection purge and retention are deliberately
**blocked pending a separately reviewed deletion design**. This stricter lifecycle
contract must be accepted explicitly; no persistent application writes may be
activated around it. It grants no deletion-completion claim or retention policy.

Upgrade takes an ACCESS EXCLUSIVE generation lock and validates a temporary
`CHECK(false)` against the physical table, then drops that temporary constraint.
It therefore requires **zero existing generations**. Existing generations have
no trustworthy execution identity to backfill, so upgrade refuses rather than
inventing historical lineage. No historical row is transformed or rewritten.

Safe schema downgrade is permitted **only with zero bindings/generations**.
Under exclusive locks it adds/validates a physical `CHECK(false)` on bindings.
Nonempty downgrade fails `23514` atomically, leaving bindings, schema/version
and deletion journal intact. A filtered owner SELECT count is never used as an
emptiness proof: FORCE RLS can report zero while physical rows exist. Empty
downgrade removes only these new objects and, after Alembic's row removal, its
empty version table. The old exact inventory guard then recognizes the base.
Re-upgrade reproduces the same immutable package identities.

The original 6C-02 downgrade refuses the candidate's extra objects, preventing a
second migration path from discarding provenance. Application rollback must leave
this schema and all bindings intact. For retained bindings use a reviewed forward
repair; never disable RLS/triggers, relabel rows, purge provenance or force a
schema downgrade to make an old application/tool run. The new guard does not
confer any production migration authority.

## Executed migration and restricted-role evidence

Complete receipts and normalized-LF new-source hashes are archived in
[SCHEMA-COMPATIBILITY-RECEIPTS.json](PHASE6C03-SCHEMA-COMPATIBILITY-RECEIPTS.json).
Full local logs and command receipts remain in `.local/c03-comp01-20261126`.
The final database receipt is `database-04.json`; full-log SHA-256:
`bcba8d6baf657fbb343d3f8d4716782fce517f1ec6fa3ebfd794c9e45f87befd`.

Fresh dedicated cluster:
`fp6c03-provenance-disposable-c588a5bc96a343fcae2e361a242de9fd`,
loopback port **55449**, Windows native PostgreSQL **17.5**, Python **3.11.9**,
frozen dependencies. Four independently generated synthetic role credentials;
none retained in an environment artifact or printed. The server stopped on exit;
its disposable files/logs remain ignored. Earlier attempts used separate fresh
clusters and their stopped files/receipts are retained too.

| Check | Actual result |
| --- | --- |
| Original tenant baseline, pristine guard and fixtures | **434 passed, 41.95 s** |
| Candidate upgrade over four existing synthetic generations | **Refused atomically, `23514`**; old inventory and journal retained |
| Original documented disposable-fixture downgrade/re-upgrade | PASS; no C03 binding had been committed; deletion journal retained exactly |
| Empty candidate upgrade / guarded downgrade / re-upgrade | **PASS**; original catalog definitions and journal snapshot unchanged at every step |
| Original tenant cases after candidate roundtrip | **434 passed, 38.89 s**, with explicit catalog compatibility plugin |
| New provenance cases, separately counted | **93 passed, 2.93 s** |
| Eight bounded delete/reinsert races | **All PASS**; delete `23503`, contender `23505`; snapshots unchanged; no retries |
| Nonempty candidate downgrade as real restricted migrator | **Refused `23514`**; complete binding and journal snapshots unchanged |
| Old migration attempts to erase candidate | **Refused by unchanged inventory guard** |
| Original immutable rule suite | **71 passed, 25.45 s**, including all 70 profiles / original and survivor oracle comparisons |
| Historical original-schema counterexample | **1 passed, 0.04 s**; its historical STOP preserved |
| Frozen full Ruff / formatting | **PASS**, 82 formatted Python files |
| Configured strict mypy, Windows and Linux target | **PASS**, 66 files each; new migration/tests separately **PASS**, four files |
| Read-only preservation | **PASS**, 312 preflight / 270 base / 285 protected Git blobs and 444 prior raw source/evidence files |

The test-only `experiments.provenance_legacy_compat` plugin names all three
additional catalog tables. It rebinds only `require_disposable` imports in the
legacy fixture/test modules and the legacy test module's `EXPECTED_TABLES`.
The candidate guard retains the full base inventory and adds exact new objects
and revision checks. The 434 test source cases and fictional fixture values are
unchanged; their catalog expectation explicitly includes these additions.
Admission, owner policies, FK rejection assertions, role privileges and budgets
are unchanged. The pristine baseline runs without this plugin. Production code
and the old migration/helper never import it.

Restricted runtime tests cover owner/collection/generation equality in both
directions; foreign reads/counts/joins and inserts; missing/malformed/stale owner
context; wrong collection/generation; nonexistent/mismatched package revision;
altered/malformed/overlong/null hashes; duplicate binding; generation key moves;
UPDATE/DELETE/TRUNCATE denial; zero-finding creation and atomic visibility.
Expected rejections include `42501`, `23503`, `23514`, `23505`, `23502`, `22001`
and `22P02`. Independent privileged fixture tests prove exact registry CHECKs
and immutable triggers, and transactional trigger-disable fault injection proves
the immediate FK still rejects an unbound generation. These privileged fault
injections are integrity tests; restricted-login evidence is counted separately
by its actual role. No injected DDL survives its test transaction.

The deletion journal receives additional fictional receipts from the repeated
tenant fixtures. Every pre-existing journal row is retained; each DDL or refused
downgrade compares an exact before/after snapshot. This does not claim the row
count stays constant while the tests intentionally insert new receipts.

Three failed database attempts remain visible. Attempt 01 had duplicate new
row/statement trigger names; distinct statement names corrected it. Attempt 02
showed that FK installation alone did not refuse the four historical generations;
the explicit physical empty-table precondition replaces that unsafe assumption.
The precise FK-validation visibility mechanism was not separately diagnosed.
Attempt 03 passed the physical refusal but failed a new catalog reader's raw `%`
placeholder handling; SQLAlchemy `text()` corrected it. Attempt 04 passed the
complete matrix. Initial new-file style/type failures were corrected without
editing old source or relaxing assertions. No failed receipt is relabeled PASS.

## Adoption gates, limitations and recommendation

| Gate | Disposition |
| --- | --- |
| Typed complete implementation identity, including empty generations | PASS for this fresh synthetic schema candidate |
| Exact immutable package identity / fixed trusted selection | PASS for `indexed-r1`; historical identity retained, no client choice |
| Ownership, scoped keys, restricted roles, FORCE RLS | PASS in the native synthetic SQL matrix; original assumptions preserved |
| No historical backfill or destructive provenance rollback | PASS through explicit refusal; empty-only roundtrip demonstrated |
| Original semantics, immutable blobs and all 70 profiles | PASS for executed original suite and preservation checks |
| Product-owner acceptance of fixed selection and blocked purge/downgrade | **PENDING** |
| Independent human security review / final CI / application adoption | **PENDING / NOT TESTED here** |

NOT TESTED: Linux/Docker/PostgreSQL 17.12 migration execution, crash recovery,
WAL/PITR/backup restore/reconciliation, hostile DBA access, production migrations,
executor-to-binding attestation, full durable provenance projection, survivor
implementation, failure/isolation matrix or any application persistence/read
route. Linux mypy is static typing evidence only. No new 1061-backend, 284-client,
Chromium, frontend performance/build, dependency-audit or full optimized-parity
run was performed for this SQL-only change. Prior measured capacity failures,
frontend proposed-budget failures, login defects and remaining Phase 6C-03 gates
retain their prior status. No new CI or GitGuardian result is claimed.

**Recommendation:** C03-COMP-01's additive representability solution is ready for
a **separate adoption decision limited to fresh disposable synthetic databases**.
Review the fixed `indexed-r1` selection, stricter generation lifecycle, empty-only
downgrade and explicit test catalog adaptation. Keep the old STOP evidence as the
baseline and adopt this candidate only through a new recorded decision. The
unfinished adapter must later prove complete result/support identity and package
matching before publication. This candidate supplies no approval to run it,
activate persistence, merge PR #13 or resume the remaining phase work.
AI-assisted tests do not satisfy independent human security review. No consumed
6C-02 exception, real data, live application DB, invite, endpoint, integration,
deployment or production capability was used.

Reproduce on a NEW recognized disposable cluster only, from `backend`:

```powershell
$env:FP6_TEST_PORT = '55449' # choose an unused loopback port
uv run --frozen python -m scripts.run_provenance_database --postgres-bin 'C:/Program Files/PostgreSQL/17/bin'
uv run --frozen pytest -q rule_tests
uv run --frozen pytest -q completion_tests/test_storage_compatibility.py
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy
uv run --frozen mypy --platform linux
uv run --frozen mypy provenance_migrations provenance_tests
uv run --frozen python -m scripts.check_provenance_preservation
uv run --frozen python -m scripts.check_indexing_preservation
```

The launcher creates/provisions its own database, runs all three SQL suites,
checks rollback/refusal and stops the server in `finally`. Do not run these
migrations against an existing application database, call generic Alembic with
production credentials, reuse old synthetic clusters or execute the full
completion suite under this task's adapter exclusion.
