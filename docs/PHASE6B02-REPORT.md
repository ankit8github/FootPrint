# Phase 6B-02 report: opaque sessions, CSRF and revocation

Date: 2026-11-24. Status: implemented experimental fixture; **not production auth**.
Implementation branch: `phase6b/opaque-session-csrf`. Initial delivery was held
for review; subsequent explicitly authorized merge finalization is recorded below.
Base: `fb0db1300a117e07a7992a7b2675bd8a8ebe5faa`, containing Phase 6B-01 merge
`bfaa9585167771f6e49b849ec9ecb88fa0501579`. Preflight verified clean synchronized
main and ancestry before branching; origin/main was re-fetched and confirmed
unchanged after local validation. See the [pre-implementation checklist](PHASE6B02-PLAN.md)
and [security contract and limitations](PHASE6B02-SESSION-SECURITY.md).

## Result and inventory

Explicitly activated ASGI-only fictional OIDC login can now issue an ephemeral
opaque session, enforce exact cookie/expiry/CSRF rules, rotate handles, revoke
locally and serialize an artificial marker against invalidation. Recovery/MFA
events are signed **fictional test messages**, not an Auth0 integration. The
normal FastAPI application, frontend, dependencies, locks, migrations, contracts,
historical tests and immutable corpus have no changes.

Exactly ten review files: nine additions and one append-only ADR update.

| File | Purpose |
| --- | --- |
| [session_store.py](../backend/experiments/session_store.py) | Digest-only bounded records, clocks, validation, owner fences, rotation, marker and revocation |
| [session_fixture.py](../backend/experiments/session_fixture.py) | Default-disabled ASGI BFF adapter, strict HTTP/CSRF/cookie lifecycle and teardown |
| [session_events.py](../backend/experiments/session_events.py) | Authenticated short-lived fictional recovery/MFA-reset messages and ordered invalidation |
| [session_test_support.py](../backend/tests/session_test_support.py) | Deterministic clocks and isolated ASGI/provider cookie jars |
| [test_session_security.py](../backend/tests/test_session_security.py) | Positive/negative protocol, session, HTTP, failure, leak and lifecycle tests |
| [test_session_races.py](../backend/tests/test_session_races.py) | Barrier-controlled ordering, final checks, cancellation and epoch races |
| [PHASE6B02-PLAN.md](PHASE6B02-PLAN.md) | Scope and acceptance checklist written before implementation |
| [PHASE6B02-SESSION-SECURITY.md](PHASE6B02-SESSION-SECURITY.md) | Implemented boundaries, failure policy and unresolved assumptions |
| PHASE6B02-REPORT.md | Executed evidence and review gates |
| [DECISIONS.md](DECISIONS.md) | Proposed ADR-022 only; all previous text and proposed statuses preserved |

## Executed local checks

Commands below ran on Windows from `backend` unless noted. Frozen dependencies
were reused; no dependency or runtime configuration changes were needed. Ignored
local orchestration `python .local/phase6b02-validation/run_checks.py backend`
and `... frontend` captured exact command outputs/exit codes, using repository
`.cache/uv`, `.cache/npm`, `.cache/pip-audit` and `.cache/ms-playwright` caches.

| Exact command | Observed result |
| --- | --- |
| `uv run --frozen ruff check .` | PASS |
| `uv run --frozen ruff format --check .` | PASS, 28 files already formatted |
| `uv run --frozen mypy` | PASS, 28 source files |
| `uv run --frozen pytest -q` | **351 passed in 88.30s**: 117 new session cases + all 234 previous tests, including 84 original OIDC cases |
| `uv run --frozen python -m scripts.export_openapi --check` | PASS, original normal-app OpenAPI unchanged |
| `uv run --frozen python -m scripts.export_phase2 --check` | PASS, previous phase contract unchanged |
| `uv run --frozen python -m scripts.validate_corpus` | PASS: 29 scenarios, six deletion snapshots, 27 source files, 48 events |
| `uv run --frozen pip-audit --cache-dir I:\FootPrint\.cache\pip-audit --progress-spinner off` | PASS, no known vulnerabilities |
| `npm run contracts:check` (frontend) | PASS |
| `npm run lint` (frontend) | PASS |
| `npm run typecheck` (frontend) | PASS |
| `npm test` (frontend) | PASS, 284 tests / 11 files |
| `npm run build` (frontend) | PASS; existing Vite 527.58 kB / gzip 192.99 kB main advisory remains P5-F01 |
| `npm audit --audit-level=low --cache I:\FootPrint\.cache\npm` (frontend) | PASS, zero vulnerabilities |
| `npm run test:smoke` (frontend) | PASS, nine Chromium scenarios in 39.4s |
| `.local/phase0-validation/tools/actionlint.exe -shellcheck= -pyflakes= .github/workflows/phase0.yml` (root) | PASS; workflow unchanged |

`npm` commands were invoked as `npm.cmd` by the Windows helper. Existing
NO_COLOR/FORCE_COLOR warnings are nonblocking. No Docker executable is available
locally (`Get-Command docker -ErrorAction SilentlyContinue` returned none);
scaffold migration evidence must come from fresh GitHub CI, not a local claim.
New diagrams or frontend screens were not introduced. The nine existing browser
tests include source removal/recomputation, consent withdrawal, workers, no raw
egress/WebSocket/storage/console leakage and the approved input gate. They do not
exercise experimental authentication in a real browser.

## Security acceptance evidence

All rows refer to executed tests in the two new test modules above, included in
the 351-test run. Earlier incremental runs were used during implementation; the
full final local run is the authoritative local result.

| ID | Executed evidence |
| --- | --- |
| SS-01 | Validated fictional login; step-up rejects a different validated subject; equal-email subjects remain independent; all 84 unchanged OIDC tests pass |
| SS-02 | Handle decodes to 32 bytes, raw handle absent from records, digest lookup; exact host-cookie flags and matching secure deletion; only opaque payload |
| SS-03 | Idle/absolute immediately before, at and after boundary; login/step-up rotate, deny old cookie and preserve absolute deadline; chosen cookie/preauth cannot authenticate |
| SS-04 | Missing, inactive, quarantined, epoch-mismatched, expired, unavailable and corrupt records/digest/CSRF metadata fail closed |
| SS-05 | Per-owner live limit, pending/attempt limits, expiry reclamation, no live eviction, shutdown/explicit teardown and deterministic clocks |
| SS-06 | Missing/wrong/replayed/expired preauth; all four marker methods; cross-action/session tokens; all login/revocation POST paths require their own token; concurrent replay commits once |
| SS-07 | Origin/Fetch Metadata/media/body/duplicate header/Host/forwarding/method/path/query/cookie negatives leave session and identity state untouched; GET/OPTIONS cannot logout or commit; no credentialed CORS |
| SS-08 | Logout removes digest before success and secure deletion; logout-all advances only owner epoch, independent subject survives, provider key failure cannot prevent local logout |
| SS-09 | Both signed event kinds; invalid signature/key/algorithm/header/issuer/audience/owner/claims/time/size; duplicate/sequence gap rejection; retry after authenticated failure completes invalidation |
| SS-10 | Both lock orders against logout/all/event; final marker rechecks expiry/epoch/activity/existence/availability; cancellation/store/publication failures; recovery during OIDC cannot resurrect stale epoch |
| SS-11 | DEBUG log/error/handled URL sentinels; opaque cookie contents, no network/DNS fallback, Python file-write guards, memory-only teardown; no browser storage/UI added |
| SS-12 | Default factory ignores environment activation; normal app rejects every new route and OpenAPI unchanged; original corpus/contract/backend/frontend/browser checks pass |

Rejected unauthenticated or malformed inputs cannot update session/identity state.
An authenticated invalidation accepted under the fence intentionally quarantines
the owner if publication fails or the task is canceled; it returns no success.
Availability restoration alone cannot restore stale access. Cancellation before
lock acceptance does not claim revocation and may leave a valid old session.
Both policies are explicitly tested. Marker commit uses a final authorization
recheck after its last await and publishes under the same lock as revocation.
Mutation-first may commit before revocation; revocation-first prohibits a later
stale commit. This is not a tenant database transaction or distributed guarantee.

## Baseline and document verification

The ignored validator `python .local/phase6b02-validation/validate_delivery.py`
checks the exact ten-file inventory, all original files except the append-only
DECISIONS update unchanged against the base, complete previous ADR text preserved,
ADR-015–022 PROPOSED, local Markdown targets/fragments, balanced code fences,
normal-app separation and all twelve acceptance IDs. `git diff --check` is also
required. Results are recorded after execution below.

Executed validator: PASS, **153 original files unchanged**, exact ten-file scope,
all prior ADR text preserved, ADR-015–022 PROPOSED and **29 local links/fragments**
valid. `git diff --check`: PASS. No architecture diagrams were added or changed.

Approved corpus manifest SHA-256 remains
`53b4ff49c5b31e4fa5b2670c757c02058d0ffab3f6b0472fe8d198a86bdd36b1`.
No scenario labels, survivor oracles or synthetic gate bytes were edited.

## GitHub delivery evidence

At initial delivery, [PR #8](https://github.com/ankit8github/FootPrint/pull/8) was
open and unmerged against main, with the ten-file inventory above. Implementation head:
`f9ca10faa7a9425b23222e5c5fbebfc2ad70d66f`.

| Observed check on implementation head | Result |
| --- | --- |
| [Push CI 45354089221](https://github.com/ankit8github/FootPrint/actions/runs/45354089221) | SUCCESS, every job/step succeeded |
| [PR CI 45354200780](https://github.com/ankit8github/FootPrint/actions/runs/45354200780) | SUCCESS, every job/step succeeded |
| [GitGuardian 138307834795](https://github.com/ankit8github/FootPrint/runs/138307834795) | SUCCESS; secret scanning, not independent security assessment |

Decoded job logs were inspected for both fresh-checkout workflows. Each records
351 backend tests, 284 frontend tests, nine browser scenarios, successful
lint/types/contracts/corpus/audits and `PASS: PostgreSQL upgrade, constraint
enforcement, downgrade, re-upgrade; no personal tables.` The unchanged workflow
executes `docker compose config --quiet`, `docker compose up -d --wait db`,
`uv run --frozen python -m scripts.check_database` and disposable-volume cleanup.
This verifies only the existing scaffold, **not tenant database isolation**.
Push/PR backend timings were 23.41s/23.22s; browser timings 12.2s/11.5s.

The GitHub connector independently confirmed the exact ten filenames. At this
verification there were zero submitted reviews and zero inline review comments;
absence of comments is not approval. Main remains at the baseline. Git writes
used existing authorized Git credentials; an ignored delivery helper used the
credential helper in memory without printing/saving credentials to create/update
PR metadata and inspect check results.

Root commands for delivery verification:

```powershell
git -c safe.directory=I:/FootPrint fetch origin
git -c safe.directory=I:/FootPrint rev-parse main origin/main
git -c safe.directory=I:/FootPrint merge-base --is-ancestor bfaa9585167771f6e49b849ec9ecb88fa0501579 main
python .local/phase6b02-validation/validate_delivery.py
git -c safe.directory=I:/FootPrint diff --check
python .local/phase6b02-validation/github_delivery.py ci
python .local/phase6b02-validation/github_delivery.py review-state
```

This follow-up changes only the report. Baseline/document checks are repeated
before its commit. The exact final head and newest push/PR/GitGuardian results
are recorded in the PR body and delivery response after observation, avoiding a
self-referential report commit hash. The PR was left open and unmerged for
product-owner/security review at that delivery; later merge authorization and
verification are recorded in the finalization section below.

## Limitations and stop gate

This work establishes only a bounded single-process fictional ASGI experiment.
The inherited loopback issuer/BFF ports share a cookie hostname; separate test
provider jars plus rejection of issuer Cookie headers are required. **Never serve
this fixture** or treat these results as actual browser TLS/cookie/proxy behavior.
No login UI was built. Memory clearing drops references, not guaranteed physical
zeroization. Network/write guards and GitGuardian are useful regression checks,
not independent penetration testing or OS-level forensic guarantees.

No durable sessions/revocation, multi-worker locks, production secret/key custody,
real MFA/step-up freshness, live provider recovery hooks, verified upstream logout,
tenant isolation or backup guarantees are established. Strict-next fictional event
ordering is not an Auth0 delivery contract. An unavailable store cannot acknowledge
logout; accepted invalidation failure quarantines access, while outage restoration
alone provides no durable or cross-process security guarantee.

Auth0 selection, plan/region/cost, production TLS/cookies/CSRF integration,
MFA/recovery delivery, named owners, independent review, legal and retention
decisions remain unresolved. ADR-015–021 retain their original PROPOSED history;
ADR-022 is also PROPOSED. P5-F01 Vite chunk remediation and P5-F02 independently
verified real-world action links remain tracked future work. Fictional reviewed
`.test` actions and browser-local transient raw parsing remain unchanged.

Initial delivery stopped for review. Subsequent authorization permits Phase 6B-02
merge finalization only. No live provider/account, durable auth/personal-data
storage, saved-footprint APIs, tenant tables/RLS, Phase 6B-03/6C, real-data import,
public deployment or beta invitations are authorized. Further implementation
requires separate authorization and review; no production readiness or compliance
claim is made.

## Merge finalization — 2026-11-24

The product owner's subsequent instruction explicitly authorized finalization of
PR #8. Immediately before merging, the guarded verification reconfirmed exact head
`14bda0d64445a10c356330cd16544806d2995345`, main base
`fb0db1300a117e07a7992a7b2675bd8a8ebe5faa`, synchronized clean feature branch,
the exact ten files above, open/non-draft state and clean mergeability. GitHub
review APIs and the connector showed zero submitted reviews, zero inline review
threads/comments and zero discussion comments; there were no blocking comments.
The merge helper repeated the checks immediately before the expected-head merge.

**Authoritative merge commit:**
[`394130d0776eca2f27d52f806d172ba5ca626117`](https://github.com/ankit8github/FootPrint/commit/394130d0776eca2f27d52f806d172ba5ca626117).
GitHub confirmed PR #8 merged at `2026-11-24T10:26:33Z`, closed, using method
`merge`. Its ordered parents are the verified main base and exact PR head above;
this was neither squash nor rebase. The merge tree is identical to the reviewed
PR tree. Local main was fast-forwarded to origin/main at this merge.

### Reverified final PR checks

| Check on exact expected PR head | Observed result |
| --- | --- |
| [Final push CI 45363750003](https://github.com/ankit8github/FootPrint/actions/runs/45363750003) | SUCCESS, every job/step |
| [Final PR CI 45363758563](https://github.com/ankit8github/FootPrint/actions/runs/45363758563) | SUCCESS, every job/step |
| [Final GitGuardian 138340114510](https://github.com/ankit8github/FootPrint/runs/138340114510) | SUCCESS, secret scanning only |
| Other check runs / legacy statuses | All check runs successful; no pending/failing legacy contexts |
| Local boundary regression | `uv run --frozen pytest -q tests/test_session_security.py::test_default_fixture_normal_app_and_method_boundaries`: **1 passed in 3.33s** |
| Local baseline/docs | PASS: 153 original files unchanged from pre-6B-02 base, ten-file scope, preserved prior ADR text, 29 local links/fragments and unchanged corpus manifest |

These CI runs cover all **351 backend tests**, including all **117 session cases**
and **84 prior OIDC cases**, 284 frontend tests, nine browser scenarios,
lint/format/types/contracts/corpus/audits and the preserved Docker scaffold
migration roundtrip. Earlier full local execution remains recorded above; the
complete suites were not rerun locally just to change this report.

[Post-merge main CI 45374839500](https://github.com/ankit8github/FootPrint/actions/runs/45374839500)
completed **SUCCESS** on authoritative merge
`394130d0776eca2f27d52f806d172ba5ca626117`, with every job/step and its check
run successful. Decoded logs reconfirmed 351 backend tests, 284 frontend tests,
nine browser scenarios, clean audits and the PostgreSQL scaffold roundtrip with
no personal tables. This is not production authentication or tenant-isolation
verification.

### Preservation and completion scope

Only this report changes after the verified merge. All **162 other tracked files**
from the PR head are unchanged, including all six new Python files, the original
OIDC implementation/tests, application/frontend, dependencies/locks, contracts,
migrations and CI workflow. The exact approved corpus hash, 29 initial scenarios,
six survivor oracles, SHA-256 import gate and historical Phase 0–6B-01 behavior
remain intact. ADR-015 through ADR-022 are byte-for-byte unchanged from the
reviewed head and explicitly **PROPOSED**.

The fixture remains default-disabled, explicitly activated for fictional ASGI
tests only, absent from normal FastAPI routing/OpenAPI, with no serving CLI or
public activation flag. The boundary regression was rerun before merge. Existing
transient processing and reviewed fictional actions are preserved. This edit does
not implement any new session functionality or change the security assumptions.

Unresolved limitations remain: one-process ephemeral revocation/fences, no real
browser TLS/proxy assurance, shared-host loopback cookie limitations, no durable
session/tenant storage, no actual MFA/step-up freshness, no verified upstream logout
or real recovery event integration, no production credential/key custody, and no
independent security assessment. Auth0/vendor, named ownership, legal/retention and
independent review decisions remain conditional. P5-F01 bundle remediation and
P5-F02 genuine action verification remain future work.

Commands executed from root during finalization, in addition to the boundary
pytest command above executed from `backend` with the repository UV cache:

```powershell
git -c safe.directory=I:/FootPrint fetch origin
python .local/phase6b02-validation/validate_delivery.py
python .local/phase6b02-validation/finalize.py verify
python .local/phase6b02-validation/finalize.py merge
git -c safe.directory=I:/FootPrint switch main
git -c safe.directory=I:/FootPrint merge --ff-only origin/main
git -c safe.directory=I:/FootPrint show -s --format='%H%n%P%n%s' HEAD
git -c safe.directory=I:/FootPrint diff --exit-code 14bda0d64445a10c356330cd16544806d2995345 HEAD
python .local/phase6b02-validation/finalize.py ci-current
python .local/phase6b02-validation/validate_finalization.py
```

The ignored helper uses existing Git credentials in memory without printing or
saving secrets. Report-only completion verification passed: the merge has the
correct two parents and exact reviewed tree; all other 162 files and ADR statuses
are preserved, corpus hash unchanged, document/baseline checks and whitespace
checks pass. Local main was synchronized before this report edit and is checked
again after its commit/push for a clean working tree and equality with origin/main.
Final completion HEAD and its newest main CI are reported in the finalization
response to avoid a self-referential commit hash.

**Stop after Phase 6B-02 finalization.** No Phase 6B-03/6C, persistent sessions,
tenant databases, real provider connection, login UI, real-user processing,
deployment or beta users; the default-disabled experimental boundary is unchanged.
