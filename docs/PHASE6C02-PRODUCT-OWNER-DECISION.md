# Phase 6C-02 product-owner engineering-risk exception decision

Prepared 2026-11-26 (Asia/Calcutta) for [PR #12](https://github.com/ankit8github/FootPrint/pull/12).

**Owner approval: APPROVED, limited repository-only exception. Merge: conditionally
AUTHORIZED after fresh exact-head checks; not yet executed when this record was
prepared.** Qualified independent human security approval remains **MISSING**;
the normal review gate is **NOT SATISFIED**. This is the user's explicit, limited
engineering-risk acceptance, not human security approval or production certification.
Keep PR #12 draft/open until finalization gates pass; then the authorized merge
commit may proceed. The consumed Phase 6C-01 exception grants nothing here.

## Reviewed state and evidence provenance

| Item | Verified value |
| --- | --- |
| Reviewed head / local HEAD / recorded upstream | `fa6748ea2b45cd1d10015421edc129259525c593` |
| Reviewed base / remote main / local origin/main | `110b3c6353d155943bbf53798f5ec2b623dd3dd0` |
| Branch | `experiment/phase6c02-tenant-schema-rls` |
| PR state at approval preflight | OPEN, DRAFT, unmerged; mergeable |
| Worktree at preparation entry | Clean; no existing decision file |
| Reviewed PR inventory | 16 additions / 3,547 lines; none of the 252 baseline files modified |
| Credential-remediation inventory versus `10982a537c189677764d1d6fa8678ad8a956d540` | 10 files, 856 insertions / 47 deletions |

Sources: [assurance report](PHASE6C02-AI-ASSURANCE.md), including its later
credential-remediation addendum, [security report](PHASE6C02-SECURITY-REPORT.md),
[plan](PHASE6C02-PLAN.md), exact-head CI logs and retained local delivery receipts.
The assurance report preserves historical pre-remediation statements; its later
addendum supersedes the earlier unresolved F01 disposition only within the
documented synthetic scope.

Preparation rechecked Git/PR refs, live run-to-head associations, all four jobs
and steps, and current check conclusions. It read retained decoded logs and ran
the existing read-only preservation checker. No database, credential, browser or
full regression test was rerun to prepare this draft. Recorded executions below
are existing evidence, not newly invented outcomes or independent human review.
At approval preflight, the only uncommitted file was this decision draft. The
user subsequently authorized committing decision/finalization documentation and
a merge commit after the stated gates. Runtime, schema, tests and security
boundaries must stay identical to the reviewed head. No later phase is authorized.
No GitHub review submissions, inline threads or discussion comments were present
at approval preflight; no approving review is fabricated or inferred.

## F01 resolution and all 24 credential regressions

**6C02-AI-F01: remediated in the synthetic fixture; independent review pending.**
The medium-severity defect shared one password across bootstrap, migration,
runtime and auth identities. Four independent ephemeral credentials now use
explicit role-specific inputs, with no shared fallback. Provisioning rejects
duplicates. The launcher avoids credential-bearing command arguments/artifacts,
redacts child output, removes setup password aliases from the test environment,
and removes native initdb's temporary pwfile. SQL password-DDL diagnostics are
restricted. RLS, grants and actual restricted-login connections are preserved.

The trusted fixture controller still receives privileged inputs; this does not
establish isolation against that controller, a host administrator or a Docker
administrator. No production secret manager or authentication integration exists.

All cases below passed within each recorded 434-case suite. B = `fp6_bootstrap`,
M = `fp6_migration_login`, R = `fp6_runtime_login`, A = `fp6_auth_login`.
Each own-credential case removes the other three credential inputs. Each wrong-role
case requires password-authentication rejection; timeout/refusal alone is not a pass.

| Case | Regression | Recorded result |
| --- | --- | --- |
| 01 | All four credentials distinct | PASS |
| 02 | B connects using only B's input | PASS |
| 03 | M connects using only M's input | PASS |
| 04 | R connects using only R's input | PASS |
| 05 | A connects using only A's input | PASS |
| 06 | B rejects M's credential | PASS |
| 07 | B rejects R's credential | PASS |
| 08 | B rejects A's credential | PASS |
| 09 | M rejects B's credential | PASS |
| 10 | M rejects R's credential | PASS |
| 11 | M rejects A's credential | PASS |
| 12 | R rejects B's credential | PASS |
| 13 | R rejects M's credential | PASS |
| 14 | R rejects A's credential | PASS |
| 15 | A rejects B's credential | PASS |
| 16 | A rejects M's credential | PASS |
| 17 | A rejects R's credential | PASS |
| 18 | Runtime helper works without the other three credential inputs | PASS |
| 19 | Missing B input rejects despite legacy shared variable | PASS |
| 20 | Missing M input rejects despite legacy shared variable | PASS |
| 21 | Missing R input rejects despite legacy shared variable | PASS |
| 22 | Missing A input rejects despite legacy shared variable | PASS |
| 23 | Duplicate R/A credentials reject | PASS |
| 24 | Unknown login rejects | PASS |

## Recorded regression and CI receipts

All four runs below belong to the exact reviewed head above and report SUCCESS;
all job steps and GitGuardian check `139721291255` report SUCCESS.

| Exact-head run | Job | Recorded evidence |
| --- | --- | --- |
| [PR tenant 45764276598](https://github.com/ankit8github/FootPrint/actions/runs/45764276598) | 139721304344 | 434 passed before downgrade and 434 after re-upgrade (15.70s / 15.60s); ledger retained |
| [Push tenant 45764271804](https://github.com/ankit8github/FootPrint/actions/runs/45764271804) | 139721287415 | 434 passed twice (15.83s / 15.81s); ledger retained |
| [PR regressions 45764276611](https://github.com/ankit8github/FootPrint/actions/runs/45764276611) | 139721304274 | 1,061 backend, 284 frontend, nine Chromium, seven preservation; scaffold roundtrip and frozen gates pass |
| [Push regressions 45764271784](https://github.com/ankit8github/FootPrint/actions/runs/45764271784) | 139721287577 | Same counts, scaffold roundtrip and frozen gates pass |

434 = the original 410 DB cases plus the 24 new credential cases. Fresh native
PostgreSQL 17.5 evidence also records 434 twice (43.18s / 34.78s); CI uses 17.12.
Recorded local regressions confirm 1,061 backend, 284 frontend, nine Chromium and
seven preservation cases. Frozen lint/format, default and DB-test types,
contracts/corpus/schema/registry, builds and dependency audits pass. No security
assertion was weakened and no skips/xfails were introduced. Audits report no known
vulnerabilities at execution time; secret scanning is not human security approval.
The preservation logs explicitly retain **FAILED performance budgets**.

## Unchanged boundaries, migrations and retained receipts

| Boundary | Inventory / evidence |
| --- | --- |
| Tenant migration track | `backend/tenant-alembic.ini`, `tenant_migrations/env.py`, `versions/6c02_0001_tenant.py` and `versions/6c02_0001.sql` unchanged by credential remediation; separate revision `6c02_0001` |
| Existing scaffold / application | Original scaffold migration/workflow and app 0.1.0 behavior unchanged; no tenant connection or persistence API wired into the app |
| Tenant row policies | 23 `fp6_data` tables plus `fp6_ledger.deletion_journal`: ENABLE + FORCE RLS, owner-equality USING/WITH CHECK; missing/malformed/stale transaction context fails closed in exercised cases |
| Privilege boundaries | Runtime NOSUPERUSER/NOBYPASSRLS, no ownership/migrator membership/DDL/TRUNCATE; auth lookup cannot enumerate footprint data; runtime cannot enumerate sessions; restore has no serving grants |
| Auth/context trust | Sole fixed-search-path auth SECURITY DEFINER lookup; auth/reference exceptions protected by grants. Trusted server selects owner context; arbitrary SQL/DBA compromise is outside the RLS guarantee |
| Isolation/integrity evidence | Actual restricted logins, both-owner CRUD/joins, composite associations, strict fresh-key FK cases, direct pool reuse and six bounded aggregate-concurrency cases retained |
| Deletion ledger | Runner compares complete committed fictional ledger tuples before/after guarded downgrade and re-upgrade; receipts remain identical. `fp6_context`, `fp6_guard` and `fp6_ledger` survive; no journal erasure |
| Protected repository | All 252 baseline files and 193 historical blobs preserved, rechecked read-only during preparation; Phase 6C-01/source gate/contracts/catalog/oracle, previous engines/corpus/registry and ADR statuses unchanged |
| Phase 6C-01 pins | 70 profiles / 32 batches; admission SHA-256 `333c513165273846a4645c74ba604900266d88e10fb6eda1848e0195949b0699`; corpus SHA-256 `53b4ff49c5b31e4fa5b2670c757c02058d0ffab3f6b0472fe8d198a86bdd36b1` |

This supports bounded synthetic evidence for TM-01/02/04; it does not complete
production G-S3. The local ledger is not durable independent deletion delivery,
backup erasure, restore reconciliation or a functioning deletion service.

## NOT TESTED record — verbatim from the assurance report

The table below is copied exactly from the assurance report's historical
evidence-only section. Its first row describes that earlier continuation. The
later authorized 24-case credential matrix supersedes only that bounded credential
portion; broader bypass testing and all other unexecuted scenarios remain
NOT TESTED. No new testing or authorization follows from reproducing this table.

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

## Outstanding gates explicitly retained

| Gate | Current state |
| --- | --- |
| Production G-S3 | OPEN; synthetic DB results do not establish production tenant isolation |
| Qualified independent human security approval | MISSING / NOT SATISFIED; no approving human reviewer, signature or approval is supplied |
| Endpoint authorization | OPEN; no DB-backed session-to-owner endpoint proof, fixed external error proof or production integration |
| Durable deletion / restore | OPEN / unimplemented; independent journal, backup/PITR deletion, restore controls and lifecycle completion unproven |
| Performance | OPEN; P5-F01 / proposed budgets remain FAILED despite preservation passes |

Owner-context trust, untested deployment pool modes, broader diagnostic exposure,
semantic service checks, identity/key custody, retention and hosting/legal/vendor
decisions remain limitations. Proposed ADRs remain PROPOSED. AI-assisted findings,
remediation and test counts neither satisfy nor silently waive these gates.

## Approved repository-only exception and expiration

The user's explicit follow-up approval accepts the documented engineering risk
solely for disabled, fictional Phase 6C-02 repository artifacts. It authorizes
decision/finalization documentation and one merge commit after fresh successful
exact-head push/PR tenant and regression CI, GitGuardian, preservation and unchanged
runtime/schema/security verification. This is an explicit product-owner exception
despite missing independent human approval; the normal human gate remains
unsatisfied. The verbatim authorization is recorded below.

The exception permits no deployment, real-user data/identities, provider connection,
public application access, production authentication/persistence, serving worker,
save UI, beta or Phase 6C-03/04/05 work. Test listeners remain loopback-only. It
does not approve any ADR or transfer the consumed Phase 6C-01 authorization.
The authorization supplies no permission beyond this controlled repository-only
merge/finalization. It cannot be reused for further work or another phase.

**Approved expiry:** the earliest of seven calendar days after the explicit owner
approval; **2026-12-03 23:59:59 Asia/Calcutta
(2026-12-03T18:29:59Z)**; owner revocation/new decision; material security or scope
change; attempted activation/public exposure; or discovery of a blocking boundary
regression. A separately authorized one-time merge would consume its merge scope.
No approval after that longstop can activate this record; a new decision is
required. There is no automatic renewal. Completion of the one-time authorized
merge consumes its merge/finalization scope; it grants no continuing capability.

## Change control, rollback and final-head requirements

1. Keep PR #12 draft/open while finalization gates are pending. The user has supplied
   explicit conditional merge authority below. Only after the gates pass may the
   PR be marked ready as needed for its merge commit. No human review, signature or
   unconditional authority is inferred from successful CI.
2. Any later documentation commit changes the head. Before a separately authorized
   merge, bind the decision to that final head and unchanged reviewed base, verify
   documentation-only differences, and obtain fresh push AND PR tenant/scaffold
   workflows plus secret scanning for that exact SHA. Verify all steps and decoded
   counts: 434 DB cases twice per tenant job, 1,061 backend, 284 frontend, nine
   Chromium and seven preservation, frozen gates, baseline equality and retained
   ledger receipts. Earlier-head green checks cannot substitute. No merge is
   authorized while checks are pending, failing, skipped or unmatched to the head.
3. A runtime/test/schema/role/RLS/credential/scope change or changed base requires
   renewed technical review and an explicit new owner decision. Never weaken tests,
   alter protected corpus/engines/registry, relabel NOT TESTED as passed, or expand
   phase scope under a documentation-only allowance.
4. Stop the experiment on runtime bypass privileges, leaked transaction owner,
   persisted cross-tenant associations, credential leakage, changed protected
   bytes or another blocking finding. Preserve logs, receipts and relevant state;
   prepare a reviewed repository revert/forward repair. No automatic destructive
   rollback or evidence deletion is authorized.
5. Keep the application disconnected from the experiment. Application rollback
   disables experimental use without dropping schema. Destructive downgrade is
   restricted to a newly recognized fictional disposable database under the guard;
   the incomplete guard-corruption matrix is not general safety assurance. Never
   downgrade user data or erase a deletion journal/ledger to roll back. Any future
   real-data incident requires writes disabled, fences/journal preserved and a
   separately reviewed compatible rollback or forward repair.

## Product-owner approval record

| Required record | Current record |
| --- | --- |
| Product owner / signer identity | Requesting user; no legal name or signature supplied or fabricated |
| Owner approval | **APPROVED in explicit follow-up conversation**, limited scope below |
| Actual approval text / timestamp | Verbatim below; recorded 2026-11-26, not an independently authenticated message timestamp |
| Engineering exception | **GRANTED**, strictly disabled synthetic repository artifacts |
| Effective date / approved expiry | Approval received 2026-11-26; earliest-of conditions above remain binding |
| Independent human reviewer / approval | **MISSING** |
| Merge authorization / merge SHA | **CONDITIONALLY AUTHORIZED / pending execution** when this documentation was committed |
| Final publication head and fresh CI | Required after this documentation commit; authoritative receipts and resulting merge SHA are recorded in PR #12 metadata and delivery evidence |

The requesting user's actual authorization follows verbatim. It is conversation
evidence of product-owner risk acceptance, not a signature, independent human
security review or an approving GitHub review:

> I approve the limited repository-only Phase 6C-02 engineering-risk exception described in `docs/PHASE6C02-PRODUCT-OWNER-DECISION.md` for FootPrint PR #12 at reviewed head `fa6748ea2b45cd1d10015421edc129259525c593`.
> I acknowledge that qualified independent human security approval remains missing and the normal review gate is not satisfied.
> I accept the documented residual risks, explicitly NOT TESTED scenarios, prohibited capabilities, rollback conditions and exception expiration.
> I authorize committing the product-owner decision and finalization documentation. I authorize a merge commit only after fresh, successful, exact-head push/PR tenant and regression CI, GitGuardian checks, preservation verification and confirmation that the runtime, schema and security boundaries remain unchanged.
> This authorization is strictly limited to disabled, synthetic-only repository artifacts. It does not authorize Phase 6C-03, production authentication, real-user data, persistence activation, external integrations, deployment or beta access.

Earlier PENDING / NOT GRANTED statements describe the preserved draft before
this explicit approval. They are not human approval, and this owner decision
does not reclassify the missing independent gate. The approval's exact recording
time is retained in local finalization evidence; no authenticated message clock
has been invented. Its expiration and all NOT TESTED limitations remain intact.

The final documentation head necessarily differs from the reviewed code head.
Its own SHA, fresh CI receipts and any authoritative merge commit are published
in [PR #12](https://github.com/ankit8github/FootPrint/pull/12) and the delivery
record after verification, avoiding a commit embedding its own SHA. Before any
merge, the only differences may be this decision and finalization documentation.
