# C03-COMP-01 final source review and CI isolation

Review of candidate `e70447788145638fa6a4554b1b71503c8fee2c8a` against
PR #13 head `511dfee080d3bcd3c68aaa35ec1474700ff0cf63` and main
`2038c65554501b7f0a099976ea07b75606cb7ff7`. The user's schema review and
publication instruction authorizes this isolated review branch and disposable
execution. It does not approve application adoption, persistence or merge.

**Disposition: GO for independent review of this fresh-synthetic schema candidate;
STOP for application adoption, Phase 6C-03 completion or merge.** Product-owner
acceptance of fixed selection, blocked purge and empty-only downgrade, qualified
independent security review and the remaining B-E gates are still required.

All three expected refs matched live Git/GitHub; initial worktree was clean.
PR #13 was draft/open/unmerged and is preserved at its original head. No AGENTS.md
was found. The authenticated GitHub login is the repository owner, ankit8github.
The connector's collaborator-permission endpoint returned 403; it supplies no
permission proof. Scope comes from the user's explicit review/publish instruction.
No approval to activate persistence or resolve the pending product decision is inferred.

## Preserved source and exact inventory

The reviewed commit adds exactly these 13 files and modifies none:

- `backend/experiments/provenance_legacy_compat.py`
- `backend/experiments/provenance_schema.py`
- `backend/provenance-alembic.ini`
- `backend/provenance_migrations/env.py`
- `backend/provenance_migrations/versions/c03_comp01_0001.py`
- `backend/provenance_migrations/versions/c03_comp01_0001.sql`
- `backend/provenance_tests/conftest.py`
- `backend/provenance_tests/test_generation_binding.py`
- `backend/scripts/check_provenance_database.py`
- `backend/scripts/check_provenance_preservation.py`
- `backend/scripts/run_provenance_database.py`
- `docs/PHASE6C03-SCHEMA-COMPATIBILITY-DECISION.md`
- `docs/PHASE6C03-SCHEMA-COMPATIBILITY-RECEIPTS.json`

This review adds only its own report/receipts, an independent audit controller and
`.github/workflows/phase6c03-schema.yml`. Every one of the 325 reviewed-head,
312 PR-head, 285 pre-experiment and 270 main blobs is preserved. The original
444-file raw evidence snapshot and all eleven candidate source hashes are checked
against the original receipts. Protected tenant migrations, all original tests,
registry, package manifest, roles, admission, routes, locks and workflows remain
byte-identical. The full original decision and receipt JSON were read.

| SQL object | Reviewed definition |
| --- | --- |
| Independent graph | `c03_comp01_0001`, no parent; exact tenant revision `6c02_0001`; controller-only online connection; `fp6_guard.provenance_alembic_version` |
| `fp6_reference.implementation_packages` | Revision varchar(16) PK; three non-null varchar(64) digests; unique four-field tuple; `recognized_immutable_package` permits exactly two original manifest tuples |
| `fp6_data.generation_implementations` | Owner UUID, collection UUID, generation integer 1-1000000; composite PK; non-null revision fixed to indexed-r1 and three digests |
| `exact_package` | Immediate four-field FK to the exact registered revision/manifest/worker/pure tuple |
| `bound_generation` | Deferred initially complete owner/collection/generation FK to generations; no cascade |
| `implementation_required` | Immediate validated complete composite FK from generations to binding; covers zero findings |
| `fp6_context.bind_implementation()` | Invoker, pg_catalog search path, qualified static SQL; creates indexed-r1 binding before generation INSERT; rejects key UPDATE |
| `fp6_context.immutable_implementation()` | Invoker, pg_catalog search path; rejects UPDATE/DELETE/TRUNCATE with 42501 |
| Five triggers | `bind_implementation` on generations; row `immutable_implementation` and statement `immutable_implementation_truncate` on each new data/reference table |
| Two RLS policies | Both tables ENABLE/FORCE RLS; `tenant_owner` uses original owner-context equality for runtime USING/WITH CHECK; `package_read` permits SELECT to runtime/owner |
| Grants/roles | Runtime binding SELECT/INSERT and package SELECT only; PUBLIC table/function rights revoked; no new role, membership, SECURITY DEFINER or bypass |
| Upgrade/downgrade preconditions | Exclusive locks plus physically validated temporary CHECK(false); upgrade requires no generations, downgrade requires no bindings; transaction rollback removes temporary checks |

The SQL file's normalized-LF SHA-256 is
`4776848bfb4f481c4fe642479233175941c0ec8ae5d03424be6ef7a932812530`.
The original protected tenant SQL and Python migrations retain their old Git blob
and SHA-256 identities; complete old/new file hashes are in the review receipts.

| Immutable identity | SHA-256 |
| --- | --- |
| Original semantic registry | `333c513165273846a4645c74ba604900266d88e10fb6eda1848e0195949b0699` |
| Package manifest, unchanged | `7485ac86c2cd9502e1414d68df7a930ae531b209706d44b8161a736ec7e24055` |
| historical-v1 worker | `69fcc47c8b0890c488900b4afe875aa7ce19faa6e257a691ad371fd53edff064` |
| historical-v1 pure | `73dbb73013b2a8ff0c364312adb6820b02a6de9ccb0d60ffd7adc9bc8cd58bb5` |
| indexed-r1 worker | `f4170b61857e2ae673332e4d57cd01cab5214ede7f4c3b3abef390221258670a` |
| indexed-r1 pure | `5e980c1c1856226ef6b2ce35b9b4eb651d5860139ba6041a4ffe76ffb262d1e7` |

## Separate catalog adjustment review

`provenance_legacy_compat.py` is an opt-in pytest plugin, not an application import.
It changes exactly three module bindings: `require_disposable` in the old fixture
and test module, and the test-local `EXPECTED_TABLES`. The latter unions exactly
implementation_packages, generation_implementations and provenance_alembic_version.
The original test's TABLES iteration, role flags/memberships, FORCE RLS, policies,
column checks, sole SECURITY DEFINER expectation and negative assertions remain
unchanged. The pristine baseline uses no plugin. The replacement guard requires
the complete original inventory, exact tenant revision, recognized candidate
revision and explicit routine inventory, rejecting overloads and extra objects.
The unchanged original guard and old migration still reject this candidate.
The separate full plugin diff is retained as `catalog-adjustment.patch` locally.
This necessary additive catalog accounting does not waive an original guarantee.

## Fresh local evidence

Two newly created independent fictional clusters on loopback ports 55459 and
55460 use native PostgreSQL 17.5 and frozen Python 3.11.9 dependencies. Each has
four distinct temporary role secrets, removed bootstrap password file, and server
shutdown in finally. No production connection, .env, real data or adapter runs.

| Scope | Result |
| --- | --- |
| Unchanged pristine tenant suite | 434 passed before migration |
| Guarded roundtrip, original tenant suite with explicit catalog plugin | 434 passed after migration |
| New binding suite | 93 passed; eight races return delete 23503 / contender 23505 |
| Independent fresh review matrix | Repeats 434 + 434 + 93, with four actual backend terminations and 18 independent denials |
| Existing unbound generations | Upgrade refuses 23514 atomically; old catalog/journal retained, no backfill |
| Empty guarded upgrade/downgrade/re-upgrade | Pass; old definitions and retained journal unchanged |
| Retained provenance rollback | Nonempty downgrade refuses 23514; every binding/journal row retained |
| Independent negatives | Exact 42501/23503/23505, complete before/after state equality, own/foreign positive controls; no shared denied helper |
| Original rule suite | 71 passed, including all 70 immutable profiles |
| Historical original-schema counterexample | One passed; old STOP remains true |
| Frozen quality | Full Ruff/format, strict configured typing and explicit migration/test typing pass; Linux target recorded separately |

The four interruption points terminate the actual migration backend from a
separate bootstrap connection: after Alembic version-table creation, after the
whole candidate SQL execute, after binding-table drop, and after version-table
drop. The second marker matches the multi-statement SQL execute; this is a late
upgrade interruption, not a claim of interruption inside every SQL statement.
Each failure must follow the selected hook, and the complete catalog (including
RLS, owners, grants, constraints, triggers, routines, roles/memberships), all
fp6 table contents, revision state and journal must exactly equal the pre-state.
Normal guarded migration then succeeds. Server crash, power-loss and WAL recovery
are not established by backend-session termination.

Independent denial checks cover runtime identity UPDATE/DELETE/TRUNCATE, deferred
generation deletion at commit, rebinding, role escalation, auth access, privileged
immutable UPDATE/DELETE and TRUNCATE CASCADE (forcing the trigger path), duplicate,
orphan, forged package digest and foreign owner inserts. SQLSTATE matching and
post-state checks are independent of the original negative helper. Privileged
integrity checks are labeled separately from real restricted-login evidence.

Initial review-tool failures remain retained: an invocation from the wrong cwd
could not import scripts; initial new-file lint/type issues were fixed only in
new review code; an old all-clusters-stopped checker was invoked while the new
cluster was running; an initial Linux mypy invocation lacked its backend config.
No schema test or protected assertion was changed to fix these tooling errors.
Original failed migration attempts and partial adapter evidence are preserved.

## CI publication and limits

The dedicated draft is stacked on `experiment/phase6c03-shared-rules`, making the
13-file schema candidate and additive review changes independently reviewable.
No push targets main or the PR #13 branch. All five existing workflows are
unchanged, including the original required PV1 synthetic checks workflow and
`phase6c03-completion.yml`. The latter still selects all completion_tests and
remains partial seed-codec/package evidence even if green; it does not validate
an absent durable adapter. Any fresh failure is retained as a failure, without
skip, xfail, continue-on-error, assertion relaxation or result filtering.

The added Linux job explicitly invokes the historical storage counterexample,
then db_tests (434 before and after) and provenance_tests (93) through the reviewed
controller, with four interruption controls and 18 independent negatives. It
imports no adapter, starts no rule executor, and uploads full schema logs on
success or failure. PostgreSQL 17.12 Docker execution is a fresh CI gate; local
17.5 results alone do not certify it.

Exact final publication SHA, draft URL, push/PR API results, fresh exact-head
push/PR workflow URLs, failures, complete downloaded job logs and checks are
retained in `.local/c03-comp01-adoption-review` and the draft's live description.
At this report's commit time fresh CI is pending; no historical CI is represented
as this head's result. Final delivery reports the actual completed outcomes.

The schema associates the server-selected revision and three artifact digests
losslessly and immutably with owner/collection/generation, including zero findings.
It cannot attest which worker executed. Existing generations are refused because
no trustworthy historical identity can be inferred. Runtime cannot delete/rebind;
physical purge and nonempty schema rollback are blocked. Those lifecycle limits
need explicit product acceptance and a separately reviewed forward deletion design.
Trusted owner-context setup is the original assumption, not SQL-level caller
authentication. Qualified independent security approval, crash/WAL/PITR/restore,
production operation and application behavior are outside these passing SQL tests.

## Remaining 6C-03 work, not authorized or started here

- **B, durable provenance:** complete strict scoped source/row/result bijections,
  typed duplicate/support projection and package-execution matching; reject all
  missing/extra/foreign/malformed references; design publication, consent/lifecycle
  fencing, retention and deletion with explicit owner/security acceptance.
- **C, survivor recomputation:** both deletion orders, stable primary promotion,
  per-copy context/context-only removal, alias/conflict/action/support recomputation
  and full oracle parity, with atomic publication and stale-worker rejection.
- **D, executor safety:** deadline/kill, committed-memory exhaustion, cancellation,
  abnormal exit, malformed/duplicate/truncated/oversized/exact-cap output, hostile
  descendants, OS network denial and cleanup, supported-platform enforcement.
- **E, complete validation/adoption:** resolve historical local login failures and
  native parity crash; complete resource/portability/end-to-end gates, full original
  backend/frontend/browser/privacy/database/build/audit/contracts/corpus matrix,
  independent security/product approval and fresh exact-head final acceptance CI.

No adapter completion, route change, survivor computation, persistent application
save, production endpoint, hosting, future phase or automatic merge occurred.
