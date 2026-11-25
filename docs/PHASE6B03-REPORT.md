# Phase 6B-03 implementation report

Initial delivery evidence is preserved below. The later explicitly authorized
PR #9 merge and finalization are recorded in the final section.

Date: 2026-11-25 (Asia/Calcutta). **Fictional ownership/authorization experiment;
not production approval.** Base main/origin/main:
`0dc69cc296a53d88353da573ed35a882c209bc3f`, including Phase 6B-02 merge
`394130d0776eca2f27d52f806d172ba5ca626117`. Clean synchronized preflight and ancestry
were verified before creating `phase6b/ownership-negative-tests`; no local changes
were reset or overwritten. See the [pre-coding plan](PHASE6B03-PLAN.md) and
[authorization contract/inventory](PHASE6B03-AUTHORIZATION.md).

## Result and changed-file inventory

Explicitly activated ASGI tests now resolve typed, current-session principals into
separate fictional internal owner UUIDs, exercise a mandatory owner-scoped mock
repository and reject cross-user reads, writes, relationships, counts and cursors.
The normal application and all previous tracked files are preserved.

Exactly ten additions, no modifications to historical tracked files:

| File | Purpose |
| --- | --- |
| [ownership_principal.py](../backend/experiments/ownership_principal.py) | Frozen principal, fixed issuer/subject registry, current session validation and action-separated fixture CSRF |
| [ownership_repository.py](../backend/experiments/ownership_repository.py) | Mandatory scoped Protocol and disposable two-owner records, relationships, pagination, atomic fenced draft publication |
| [ownership_fixture.py](../backend/experiments/ownership_fixture.py) | Default-disabled ASGI/session composition, strict input, fixed errors and scrubbed transport |
| [ownership_inventory.py](../backend/experiments/ownership_inventory.py) | Server-side inventory of current and proposed authorization families; no future route registration |
| [ownership_test_support.py](../backend/tests/ownership_test_support.py) | Two isolated ASGI clients, deterministic clock and test-only invalidation/view tickets |
| [test_ownership_security.py](../backend/tests/test_ownership_security.py) | 131 positive/negative ownership, cursor, input, failure, separation and leakage cases |
| [test_ownership_races.py](../backend/tests/test_ownership_races.py) | 82 controlled revocation/final-guard/cancellation/cached-handle cases |
| [PHASE6B03-PLAN.md](PHASE6B03-PLAN.md) | Acceptance IDs and plan written before implementation |
| [PHASE6B03-AUTHORIZATION.md](PHASE6B03-AUTHORIZATION.md) | Implemented contract, endpoint inventory, trust exceptions and future gaps |
| PHASE6B03-REPORT.md | Executed validation evidence, limitations and review gate |

No ADR was appended: the bounded experiment follows existing proposed ADR-017/022.
All previous ADR text/statuses, including ADR-015 through ADR-022 **PROPOSED**,
remain unchanged. No migrations, dependencies, workflow, normal routes, frontend,
contracts, oracle labels or synthetic input allowlist changed.

## Executed local validation

Frozen installed dependencies were reused. Ignored orchestration
`python .local/phase6b03-validation/run_checks.py backend` and `... frontend`
captured command output, status and timings under `.local/phase6b03-validation`.
The local sandbox process helper failed before launch; approved execution used
process-scoped `git -c safe.directory=I:/FootPrint`, with no global Git trust edit.
This is an execution-environment issue, not a skipped validation.

| Command (backend unless noted) | Observed result |
| --- | --- |
| `uv run --frozen ruff check .` | PASS |
| `uv run --frozen ruff format --check .` | PASS, 35 files |
| `uv run --frozen mypy` | PASS, 35 source files |
| `uv run --frozen pytest -q` | **564 passed in 94.96s**: all 351 prior tests plus 213 ownership cases |
| `uv run --frozen python -m scripts.export_openapi --check` | PASS, normal API unchanged |
| `uv run --frozen python -m scripts.export_phase2 --check` | PASS, Phase 2 unchanged |
| `uv run --frozen python -m scripts.validate_corpus` | PASS: 29 scenarios, six survivor snapshots, 27 source files, 48 events |
| `uv run --frozen pip-audit --cache-dir I:\FootPrint\.cache\pip-audit --progress-spinner off` | PASS, no known vulnerabilities |
| `npm.cmd run contracts:check` (frontend) | PASS |
| `npm.cmd run lint` (frontend) | PASS |
| `npm.cmd run typecheck` (frontend) | PASS |
| `npm.cmd test` (frontend) | PASS, 284 tests / 11 files, including discovery/assessment/survivor oracles |
| `npm.cmd run build` (frontend) | PASS; existing 527.58 kB / gzip 192.99 kB main chunk remains P5-F01 |
| `npm.cmd audit --audit-level=low --cache I:\FootPrint\.cache\npm` (frontend) | PASS, zero vulnerabilities |
| `npm.cmd run test:smoke` (frontend) | PASS, nine Chromium scenarios in 34.5s |
| `.local/phase0-validation/tools/actionlint.exe -shellcheck= -pyflakes= .github/workflows/phase0.yml` (root) | PASS, workflow unchanged |

No Docker executable is available locally. The unchanged scaffold migration
upgrade/constraint/downgrade/re-upgrade is therefore verified in fresh GitHub CI
before final delivery, not claimed as locally executed. The smoke harness starts
only the existing normal loopback app/Vite servers; new ownership fixtures use
ASGI calls and no extra listener. Existing NO_COLOR/FORCE_COLOR warnings are
nonblocking. No performance/bundle remediation was attempted.

The initial security-only run had 114 passes and one incorrect test expectation
for an uppercase noncanonical UUID (422 expected by the implemented contract,
while the test expected 404). The expectation was corrected; all 131 final
security cases pass in the full run. An initial 81-race-case run passed before
adding the consent-placeholder final-guard case; all 82 final cases pass above.
Final review also added regression cases for a non-boolean availability flag,
non-ASCII CSRF header (fixed 403), malformed cursors and framework root/method/
Unicode-path failures that must not reflect query identifiers. These development
runs are not separate security assurance evidence.

## Acceptance evidence

| ID | Executed evidence and limits |
| --- | --- |
| OA-01 | Actual inherited OIDC/session logins for same-email fictional subjects resolve separate UUIDs; mismatched issuer/subject/owner/epoch/session digest and malformed principal fields deny construction |
| OA-02 | Constructors require principal; cached handles validate every operation; no public unscoped helpers; corrupt owner/record/link/lifecycle/cursor state fails closed; wrong-owner sentinel attribution rejects |
| OA-03 | Symmetric A/B foreign/random detail/update/delete/filter/count/join/nested/batch and linked-create/update attempts return fixed 404; snapshots prove no state or other-owner mutation; valid CRUD/batch and relationship repair succeed |
| OA-04 | Foreign/nonexistent status, exact body and all returned headers compare equal; strict JSON/path/query/header/nested/batch negatives; DEBUG logs/retained URL and errors contain no B sentinel, foreign path ID or raw session handle |
| OA-05 | Own pagination succeeds; manipulated/foreign/random/other-session/wrong-limit/wrong-filter cursors deny; stale cursor is 409; B-only mutation leaves A bytes/count/order/generation/active cursor unchanged; independent per-owner capacity |
| OA-06 | 64 write-vs-invalidation cases: both subjects, four mutation operations, logout/logout-all/recovery/MFA-reset and both owner-lock acquisition orders; write-first may commit, revoke-first cannot; later stale writes deny |
| OA-07 | 13 final-guard failure cases cover waiting/locked/swallowed cancellation, publication/outage, expiry, epoch, missing session, inactive/quarantine and changed generation/consent/lifecycle; no draft publishes; cached-handle operations all deny after rotation/revocation |
| OA-08 | Test-only two-view ticket invalidation clears rows and rejects delayed A responses after logout/B switch; independent ASGI client reusing revoked shared cookie gets 401; no real browser login/invalidation integration claim |
| OA-09 | Default factory ignores environment activation and registers no routes/state/keys; normal GET/POST routes and OpenAPI exclude fixture; lifecycle teardown discards data/security state; guarded file-write/DNS/socket test and all prior suites pass |
| OA-10 | Immutable Python inventory plus endpoint-by-endpoint document separate current checks, trusted bootstrap/test exceptions and six unimplemented future families; no public operator bypass |
| OA-11 | Full local checks above; exact-head push/PR CI, GitGuardian and scaffold logs recorded in the GitHub evidence section and final PR body after observation |

Snapshot checks compare repository records, lifecycle and cursors after rejected
operations. CSRF bootstrap may legitimately touch session idle metadata; accepted
logout/recovery intentionally revokes/quarantines authority. The no-mutation claim
applies to rejected footprint writes, not to pretending invalidation never changes
security state. Each successful ownership mutation rotates its fixture CSRF base.

## Preservation and delivery verification

Before commit/push, the ignored delivery validator compares every historical
tracked file to the exact base, validates the ten-file allowlist, all prior ADRs,
local Markdown targets/anchors, acceptance IDs and corpus manifest digest.
Executed: PASS, **163 historical tracked files unchanged**, exact ten additions, all previous ADR text/statuses preserved and **16 local Markdown targets/anchors** valid. Approved corpus manifest SHA-256 remains `53b4ff49c5b31e4fa5b2670c757c02058d0ffab3f6b0472fe8d198a86bdd36b1`. `git diff --check` also passed. Exact final head belongs in the PR body and final
response to avoid a self-referential report commit hash. GitHub assigns the PR
number; expected #9 is not an authority to overwrite an existing PR.

## GitHub delivery evidence

[PR #9](https://github.com/ankit8github/FootPrint/pull/9) is open and unmerged
against main. Verified implementation head:
`1d18692620bcd4b5bcb9e517767130bdab9e31b7`.

| Observed check on implementation head | Result |
| --- | --- |
| [Push CI 45548405672](https://github.com/ankit8github/FootPrint/actions/runs/45548405672) | SUCCESS, every job/step |
| [PR CI 45548519481](https://github.com/ankit8github/FootPrint/actions/runs/45548519481) | SUCCESS, every job/step |
| [GitGuardian 138983840668](https://github.com/ankit8github/FootPrint/runs/138983840668) | SUCCESS; secret scanning, not independent security review |

Decoded logs from both fresh-checkout jobs were inspected through the GitHub
connector. Each confirms **564 backend tests**, **284 frontend tests**, **nine
Chromium scenarios**, clean audits/contracts/corpus checks and
`PASS: PostgreSQL upgrade, constraint enforcement, downgrade, re-upgrade; no personal tables.`
Backend timings were 29.80s/51.44s; browser timings were 6.1s/11.7s for push/PR.
The unchanged workflow runs Docker Compose and `scripts.check_database`, then
cleans its disposable volume. This proves only the old scaffold migration, not
tenant/FK/RLS database coverage.

The connector independently confirmed all ten changed filenames. Read-only API
verification confirmed unchanged remote main, exact PR head/base, all check runs
successful, no pending legacy status, zero submitted reviews and zero inline or
discussion comments. Absence of reviews is not approval. The connector could read
metadata/logs but PR creation returned `403: Resource not accessible by integration`;
the existing authenticated Git account created the explicitly requested PR.
Credentials stayed in memory and were neither printed nor saved.

This follow-up changes only this report to record observed implementation-head
evidence. Final exact head, its fresh push/PR CI and GitGuardian results are
recorded in the PR body and delivery response after verification, avoiding a
self-referential report commit hash. No implementation files changed after the
successful 564-test local run or implementation CI. Repeat preservation/link and
whitespace checks before the report commit. Leave PR open and unmerged.

## Security limitations, incomplete cases and stop gate

This is a bounded in-memory mock repository/interface harness, **not PostgreSQL
RLS, tenant database isolation or production authorization certification**. Even a
successful Docker scaffold roundtrip tests only the two old scaffold tables.
G-S3 remains missing until restricted-role SQL, FK/RLS, pool reuse and the full
real endpoint matrix pass under separate Phase 6C authorization.

Lifecycle/consent epoch fields are synthetic placeholders, not captured save
consent, deletion journals, retention or durable generation control. No actual
saved-footprint API, durable record, auth/tenant table, provider account, live
registration, public login, deployment, outbound footprint transfer or next-phase
work is added. Test-only private state inspection is trusted interpreter access,
not a supported unscoped repository/admin interface.

Single-process/event-loop fences do not establish distributed serialization,
crash-safe revocation or cross-worker cancellation. Tests exercise cancellation
signaled to the running task, including swallowed cancellation; they do not prove
that every client disconnect automatically cancels server work. Data already
committed/delivered before logout cannot be recalled. Clearing drops references,
not secure erasure. Uniform envelopes do not prove timing indistinguishability.

Two-tab helpers model invalidation and stale-response clearing. Real frontend
login, browser BroadcastChannel/cookie propagation, TLS/proxy behavior and actual
provider recovery/logout/MFA freshness remain unverified. The inherited mock
issuer/BFF share a cookie hostname across ports, so separate provider test jars
and Cookie rejection are required; never serve the fixture. Existing nine browser
tests cover the unchanged synthetic MVP, not authentication integration.

TM-15's production proxy/IdP/database/executor/audit access/retention/support cases
are incomplete because those systems do not exist here. No general XSS, penetration,
real-user, tenant-schema, production key custody, legal or vendor readiness claim
is made. 213 extra tests and GitGuardian are regression evidence, not independent
security assurance. ADRs remain PROPOSED; P5-F01 and P5-F02 stay unresolved.

**STOP: leave PR open and unmerged for product-owner and independent engineering
security review. No Phase 6B-04 or Phase 6C work, deployment or further phase is
authorized by this implementation.**

## Merge finalization — 2026-11-25

The subsequent user instruction explicitly authorized finalization of PR #9 only.
Immediately before merging, guarded verification reconfirmed exact PR head
`a717303bd71cea58edf088af65b52090a79213c9`, expected main base
`0dc69cc296a53d88353da573ed35a882c209bc3f`, a clean synchronized feature branch,
the exact ten added files listed above, and clean mergeability. GitHub connector
and direct API reads showed zero submitted reviews, zero review threads, zero
inline comments and zero discussion comments. There were no blocking comments;
this does not represent independent review approval.

The guarded merge repeated the checks immediately before an expected-head merge
request with method `merge`. The connector's merge action returned
`403: Resource not accessible by integration`; the existing authenticated Git
account completed the explicitly authorized operation. Credentials remained in
memory and were not printed or saved.

**Authoritative merge commit:**
[`c2bc3be8a18d9917bfb1e0a490497652f54b81ce`](https://github.com/ankit8github/FootPrint/commit/c2bc3be8a18d9917bfb1e0a490497652f54b81ce).
GitHub confirmed PR #9 merged at `2026-11-25T04:54:30Z` and is closed. The merge's
ordered parents are the expected main base and exact PR head above; this is a
merge commit, not squash or rebase. Its tree is identical to the reviewed head.
Local main was fast-forwarded to origin/main at this authoritative merge.

### Reverified CI and boundary evidence

| Check | Observed result |
| --- | --- |
| [Final PR-head push CI 45548987880](https://github.com/ankit8github/FootPrint/actions/runs/45548987880) | SUCCESS, every job/step on expected PR head |
| [Final PR CI 45548992368](https://github.com/ankit8github/FootPrint/actions/runs/45548992368) | SUCCESS, every job/step on expected PR head |
| [GitGuardian 138985364768](https://github.com/ankit8github/FootPrint/runs/138985364768) | SUCCESS on expected PR head; secret scanning only |
| [Post-merge main CI 45549937384](https://github.com/ankit8github/FootPrint/actions/runs/45549937384) | SUCCESS on authoritative merge, every job/step and check run |
| Local default-disabled/normal-route/lifespan regression | `uv run --frozen pytest -q tests/test_ownership_security.py::test_default_disabled_normal_routes_and_lifespan`: **1 passed in 1.41s** |
| Ownership collection check | **213 tests collected** in the two unchanged ownership test modules |
| Preservation/documentation checks | PASS: all 163 historical files, all 172 other reviewed files, proposed ADRs, corpus/gate and 16 local Markdown targets/anchors preserved |

Decoded logs from both final PR-head jobs and post-merge main CI were inspected.
Each confirms **564 backend tests** (all **351 previous** plus **213 ownership**
cases), **284 frontend tests**, **nine Chromium scenarios**, successful
lint/format/types/contracts/corpus/audits and the PostgreSQL scaffold roundtrip:
`PASS: PostgreSQL upgrade, constraint enforcement, downgrade, re-upgrade; no personal tables.`
Post-merge backend and browser timings were 46.83s and 12.4s. This is the unchanged
scaffold migration check, not tenant database, restricted-role or RLS coverage.
No full local suite was rerun merely for this report-only update; fresh main CI
executes the complete validation workflow after its commit/push.

### Preservation, limitations and completion scope

Only this report changes after the verified merge. All 172 other reviewed files
are preserved, including every ownership/session/OIDC implementation and test,
the normal FastAPI application and external-facing routes, existing frontend,
dependencies/locks, contracts, corpus/oracles, synthetic input gate, migrations
and workflow. All 163 historical tracked files remain unchanged from the expected
pre-6B-03 base. The approved corpus manifest SHA-256 remains
`53b4ff49c5b31e4fa5b2670c757c02058d0ffab3f6b0472fe8d198a86bdd36b1`.
ADR-015 through ADR-022 are byte-for-byte unchanged and **PROPOSED**.

The ownership experiment remains disabled by default, explicitly activated only
for fictional ASGI tests, unmounted from the normal app and absent from its
OpenAPI/frontend contracts. No serving CLI, public activation flag or production
authorization claim is introduced. All 213 ownership cases and previous 351
backend tests are preserved. Additional tests and successful GitGuardian checks
are regression evidence, not independent security assurance.

**G-S3 remains missing** until real PostgreSQL restricted-role/FK/RLS, pool reuse
and endpoint tests pass under separate authorization. There is no production
browser/auth integration, distributed lock, durable session/revocation, durable
consent or personal-data guarantee. The inherited shared-host mock cookie limit,
test-only tab clearing, memory-only teardown and incomplete operational logging/
provider/recovery coverage remain. Auth0/vendor capability and selection,
accountable ownership, legal/retention decisions, independent security assessment,
and previous findings P5-F01/P5-F02 remain unresolved.

Local main is checked against origin/main for clean synchronization after the
report commit. Its exact final HEAD and newest main CI result are reported in the
finalization response, avoiding a self-referential report commit hash. The merge
SHA above remains authoritative regardless of the report-only follow-up SHA.

**Stop after Phase 6B-03 finalization.** No Phase 6B-04 or 6C work, tenant database
schema, durable personal-data persistence, real-provider connection, deployment,
real-user processing or beta invitations are authorized. Finalization does not
resolve the limitations or approve a next phase.
