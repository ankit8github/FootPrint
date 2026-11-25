# Phase 6B-03 implementation report

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

GitHub evidence is pending observation at this document's initial writing. The
branch will be pushed and a separate PR opened against main, then push and PR
workflow jobs/logs and GitGuardian will be inspected. No merge is authorized.

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
