# Phase 6B-04 report: measured experiment rejected and rolled back

Date: 2026-11-25. Scope: isolated synthetic frontend performance measurement.
**No performance remediation is accepted.** The route-loading candidate failed
seven proposed checks and was rolled back. P5-F01 remains OPEN; original eager
imports and the original Vite advisory remain. The subsequent user instruction
authorized a benchmark-evidence-only merge, recorded below. Engineering outcome:
**measurement completed; candidate rejected; P5-F01 open**. This is not successful
performance remediation and does not authorize another phase.

## Authority, baseline and measured outcome

Fetched and verified clean synchronized main/origin/main
`4565d4c5665f941b486d569c35fe7aebc14654f2`, including Phase 6B-03 merge
`c2bc3be8a18d9917bfb1e0a490497652f54b81ce` ancestry. Created
`phase6b/frontend-performance` without resetting local changes. Read required
6A plan/design, Phase 5 findings and boundaries, corpus/oracles, Phase 6B-03
completion and relevant code/tests. Wrote the [plan](PHASE6B04-PLAN.md) before
application changes; built and archived unchanged main before remediation.

Executed **240 formal cold samples**: 30 per route/viewport in baseline and
candidate, four cells per stage. All samples retained; no failures, hidden
retries, outlier deletion or threshold adjustment. Matching Node/Vite/Chromium,
hardware, loopback gzip server, CPU/network emulation and instrumentation hashes
are documented in the [baseline](PHASE6B04-PERFORMANCE-BASELINE.md).
Full [results and rollback](PHASE6B04-PERFORMANCE-RESULTS.md) disclose costs,
distributions, failed targets and measurement limitations. Committed numeric
rows/waterfalls, exact asset hashes/module graphs and the rejected source patch
provide reviewable synthetic evidence. Full local traces/screenshots/JSONL remain
under `.local/phase6b04-validation/`; raw JSONL hashes identify those archives.

The candidate's root initial gzip JS decreased 191121 to 70973 bytes, but Phase 5
complete HTTP transfer increased 445757 to 452079 bytes. Phase 5 p75 LCP was
**2580 ms mobile / 2564 ms desktop**, exceeding 2500 ms. Selection/disclosure
regressed over 10% in both viewports; desktop filtering also regressed over 10%.
LCP tails worsened in every cell. The budget evaluator exits **1**, retaining
all **seven failed checks out of 25** in its JSON. No approved alternative budget
or performance success is claimed. Separate calibration/functional checks are
excluded from the 30-sample statistics.

Restored the original three source files and removed only two introduced modules
after verifying their candidate hashes against concurrent edits. The archived
five-file patch applies cleanly to restored main. Final production JS/CSS hashes
match the unchanged baseline exactly; HTML CSP nonce may vary. No active frontend
or backend application code changes remain. The only historical-file changes
are an npm command and a CI step for explicit rollback/privacy verification.

## Acceptance evidence

| ID | Outcome |
| --- | --- |
| PF-01 | PASS: unchanged-main ordinary archive, exact JS/CSS observational-build match, full asset/import graphs, 120 baseline samples before source edits |
| PF-02 | PASS with stated limitations: exact environment/protocol, raw rows/waterfalls, nearest-rank distributions and available CPU/trace evidence; unreliable measurements marked unverified |
| PF-03 | Experiment performed: selected-route imports, parallel renderer and verbatim shared-view extraction; React.lazy/Suspense pilot investigated; complete byte/request/worker costs disclosed; candidate rolled back |
| PF-04 | **FAIL; rollback executed:** seven proposed budget/regression failures; no target changes, warning suppression or accepted remedy; stop for review |
| PF-05 | PASS for restored application: all 564 backend, 284 frontend and nine existing browser scenarios unchanged; seven new focused production privacy/rollback scenarios |
| PF-06 | PASS: source gate, corpus/oracles, engines, bounds/deadline, API/contracts, migrations, disabled fixtures and ADR statuses preserved |
| PF-07 | Four documents, reproducible tooling, inventories/graphs/waterfalls/distributions and rejected patch delivered; exact head and fresh GitHub evidence recorded after push below |

## Executed local validation

Frozen dependencies; no installs or dependency/lock changes. Complete command
outputs and exit codes are in `.local/phase6b04-validation/backend.json` and
`frontend.json`. All completed with exit 0 except the deliberately failing
proposed-budget comparison described above.

| Check | Executed result |
| --- | --- |
| Backend Ruff lint / format check | PASS |
| Backend mypy | PASS, 35 source files |
| Backend pytest | **564 passed**, including all 213 ownership and 351 previous cases; pytest 120.43s |
| API and Phase 2 export checks | PASS, both unchanged contracts |
| Synthetic corpus validation | PASS, **29 scenarios / six deletion snapshots / 27 approved source files**, 32 coverage categories |
| Python dependency audit | PASS, no known vulnerabilities |
| Frontend ESLint / TypeScript | PASS |
| Frontend tests | **284 passed in 11 files**, existing test files unchanged |
| Frontend contracts | PASS |
| Production build | PASS, original main 527589 bytes and original advisory retained after rollback |
| npm dependency audit | PASS, zero vulnerabilities |
| Existing Playwright Chromium smoke | **9 passed**, 27.6s; all original scenarios unchanged |
| Focused production checks | **7 passed** in explicit `--baseline` mode: exact original JS/CSS, no early workers, original route inventory, expected selection worker, no unwanted traffic/storage/cookies/console/WebSocket |
| Candidate functional check, before rollback | **7 passed**; separate from statistical performance acceptance |
| Evidence integrity / independent numeric audit | PASS: 240 rows, SHA-256 checks, nearest-rank LCP/interaction calculations and exact five instrumentation hashes |
| Scoped rollback / patch check | PASS; no application-source diff and rejected patch applies cleanly |
| Scaffold migration roundtrip | Not run locally; verified in both fresh CI job logs below. No tenant/RLS claim |

The new strict production check still rejects the restored oversized/eager build.
CI explicitly calls `test:performance -- --baseline`, testing preservation and
privacy without asserting performance approval. The 30-run budget comparison
remains failed. Additional scenarios, test totals, passing CI or GitGuardian are
regression evidence, not independent security or performance assurance.

## Changed-file inventory

Two modified historical files; twenty-one additions, **23 files total**:

- `.github/workflows/phase0.yml` — retain all checks/Docker roundtrip; add explicit production privacy/rollback check.
- `frontend/package.json` — add `test:performance`; dependencies/locks unchanged.
- `docs/PHASE6B04-PLAN.md`
- `docs/PHASE6B04-PERFORMANCE-BASELINE.md`
- `docs/PHASE6B04-PERFORMANCE-RESULTS.md`
- `docs/PHASE6B04-REPORT.md`
- `docs/performance/.gitattributes` — LF for evidence hashes; permit required blank unified-diff context lines in the archived patch.
- `docs/performance/phase6b04-baseline.json`
- `docs/performance/phase6b04-baseline-samples.jsonl`
- `docs/performance/phase6b04-results.json`
- `docs/performance/phase6b04-results-samples.jsonl`
- `docs/performance/phase6b04-budgets.json`
- `docs/performance/phase6b04-rejected-candidate.patch`
- `frontend/scripts/performance/README.md`
- `frontend/scripts/performance/.gitattributes` — preserve exact measured instrumentation bytes across checkouts.
- `frontend/scripts/performance/build.mjs`
- `frontend/scripts/performance/server.mjs`
- `frontend/scripts/performance/probe.mjs`
- `frontend/scripts/performance/browser.mjs`
- `frontend/scripts/performance/run.mjs`
- `frontend/scripts/performance/summarize.mjs`
- `frontend/scripts/performance/compare.mjs`
- `frontend/scripts/performance/check.mjs`

All **171 other historical files out of 173** are unchanged, including every
application module, original test, immutable corpus/oracle, source gate, worker,
controller, rule/action directory, normal FastAPI router, ASGI fixture, migration,
contract and prior document. ADR-015 through ADR-022 remain byte-identical and
**PROPOSED**; no prior ADR status changed. Corpus manifest SHA-256 remains
`53b4ff49c5b31e4fa5b2670c757c02058d0ffab3f6b0472fe8d198a86bdd36b1`.

## Limits and strict stop

Unsupported measurements are explicitly unverified: dedicated-worker CPU throttle
inheritance, isolated syntax-parse CPU, complete browser worker waterfall phases,
OS disk cache/power/thermal/frequency control, physical-mobile equivalence and
production/field performance. Input-to-two-frame timings are automation proxies,
not INP; trace sums overlap. Server socket counters include browser HTTP headers
and bodies, excluding TCP/IP/TLS and backend proxy hop. Neither timing causes nor
production suitability are established by this sequential lab experiment.

Default-disabled Phase 6B OIDC/session/ownership fixtures remain untouched,
ASGI-only and unmounted from normal FastAPI. No production auth/browser,
distributed-lock, durable-session/revocation or consent guarantee is added.
**G-S3 remains missing** until real PostgreSQL restricted-role/RLS/FK/pool and
endpoint tests. Auth0/vendor capability/selection, accountable ownership,
legal/retention decisions, independent security review, P5-F02 and other inherited
findings remain unresolved. No personal-data persistence, tenant tables, real
provider/data processing, deployment or external user invitations occurred.

The original delivery stopped with PR #10 unmerged for product-owner/frontend-
security review. The later finalization instruction authorized only the rejected
experiment's benchmark-evidence merge described below.
No further optimization, Phase 6C/database work, production authentication,
real-user/provider integration, deployment or beta enrollment is authorized.

## Pre-merge GitHub delivery evidence

Opened [PR #10](https://github.com/ankit8github/FootPrint/pull/10), against main,
on `phase6b/frontend-performance`. Verified implementation head:
`81cf783e5da9e2548e81ed2a601a83aa24dd43bc`; verified base:
`4565d4c5665f941b486d569c35fe7aebc14654f2`. At delivery, GitHub confirmed open/unmerged,
clean mergeability and the exact 23-file inventory above. Zero reviews, inline
comments or discussion comments were present at verification; this is not
independent approval. The original instruction stopped before merging; later
explicit finalization authority is recorded below.

| Exact implementation-head remote evidence | Result |
| --- | --- |
| [Push CI 45557448778](https://github.com/ankit8github/FootPrint/actions/runs/45557448778) | SUCCESS, every job/step |
| [PR CI 45557675215](https://github.com/ankit8github/FootPrint/actions/runs/45557675215) | SUCCESS, every job/step |
| [GitGuardian 139013559489](https://github.com/ankit8github/FootPrint/runs/139013559489) | SUCCESS, secret scanning only |

Decoded logs from both jobs were inspected. Each confirms **564 backend tests,
284 frontend tests, nine existing Chromium scenarios, seven new production
privacy/rollback scenarios**, successful quality/contracts/corpus/audits and
`PASS: PostgreSQL upgrade, constraint enforcement, downgrade, re-upgrade; no personal tables.`
This is the preserved disposable scaffold migration check, not tenant-schema,
restricted-role or RLS coverage. Both logs explicitly retain the failed
performance-budget outcome; passing functional CI does not approve it.

The GitHub connector's creation action returned `403: Resource not accessible by
integration`; the existing authenticated Git account completed the explicitly
requested creation. Credentials remained in memory and were not printed/saved.
Connector reads independently confirmed PR metadata and decoded CI logs.

This evidence update is report-only after the tested implementation head. The
PR records its exact final head and fresh final push/PR/GitGuardian check results,
avoiding a self-referential report commit hash. All other 22 delivered files and
all 171 protected historical files remained unchanged. At that delivery point,
main had not been modified or merged. Delivery ended with the performance
proposal failed, remedy rolled back and P5-F01 open for review.

## Merge finalization - 2026-11-25

**Engineering outcome: measurement completed; candidate rejected; P5-F01 open.**
The subsequent user instruction authorized finalizing PR #10 exclusively as a
**REJECTED PERFORMANCE EXPERIMENT / benchmark-evidence-only merge**. It did not
approve the candidate, relax budgets or authorize additional optimization.

Immediately before merging, fetched refs and repeated guarded local/API checks:
clean synchronized feature branch at exact head
`634d624d0de3756fda903217e5bd853e8e9290c3`, base main/origin/main
`4565d4c5665f941b486d569c35fe7aebc14654f2`, exact 23-file inventory, clean
mergeability and zero submitted reviews, review threads, inline comments or
discussion comments. No new blocking review/comment was present. Absence of
reviews does not constitute independent security/performance approval.

**Authoritative merge commit:**
[`1e4662d9a4355232fabac10d3366297032547970`](https://github.com/ankit8github/FootPrint/commit/1e4662d9a4355232fabac10d3366297032547970).
GitHub confirmed PR #10 closed/merged at `2026-11-25T06:22:34Z`. Ordered parents
are the exact expected base and reviewed head above; this is a merge commit,
not squash or rebase. Its tree is identical to the reviewed head. Local main was
fast-forwarded to origin/main at the authoritative merge without a reset.

The connector merge action returned `403: Resource not accessible by integration`.
The existing authenticated Git account repeated all guards immediately before
the explicitly authorized expected-head `merge` request. Credentials stayed in
memory and were not printed or saved. Connector reads independently reconfirmed
the merged state and authoritative SHA.

### Exact pre-merge and post-merge CI evidence

| Reverified evidence | Result |
| --- | --- |
| [Final PR-head push CI 45558303162](https://github.com/ankit8github/FootPrint/actions/runs/45558303162) | SUCCESS on exact reviewed head; every job/step |
| [Final PR CI 45558309657](https://github.com/ankit8github/FootPrint/actions/runs/45558309657) | SUCCESS on exact reviewed head; every job/step |
| [GitGuardian 139015615613](https://github.com/ankit8github/FootPrint/runs/139015615613) | SUCCESS on exact reviewed head; secret scanning only |
| [Post-merge main CI 45560134922](https://github.com/ankit8github/FootPrint/actions/runs/45560134922) | SUCCESS on authoritative merge; every job/step |

Decoded logs from both final PR-head jobs and post-merge main CI were inspected.
All confirm **564 backend tests, 284 frontend tests, nine original Chromium
scenarios and seven new preservation scenarios** remain successful, along with
lint/format/types/contracts/corpus/audits and the scaffold migration roundtrip:
`PASS: PostgreSQL upgrade, constraint enforcement, downgrade, re-upgrade; no personal tables.`
Post-merge pytest completed in 35.17s; existing browser scenarios in 7.0s. These
are functional/regression results, not acceptance of the failed performance
proposal or tenant/RLS database coverage.

The mandatory `Production privacy and rollback preservation` CI step remains
unchanged, without a condition or `continue-on-error`, and executes
`npm run test:performance -- --baseline`. It verifies exact original active
JS/CSS asset hashes and original eager route-module inventory, along with worker
selection/lifecycle, network, storage and error checks. Its log explicitly says
the proposed performance budgets remain **FAILED**. The strict default check and
the archived statistical decision are not reclassified as passing.

### Failure decision, baseline and rollback retained

The unchanged-main baseline remains
`4565d4c5665f941b486d569c35fe7aebc14654f2`. All **240 formal samples** remain
exact: 120 baseline and 120 rejected-candidate samples, 30 per route/viewport in
each stage. Both published JSONL hashes, full local JSONL hashes, asset/module
graphs, scripts/instrumentation hashes, archived rejected patch and all other
reports are unchanged from the reviewed head. No new candidate or measurement
stage was introduced during finalization.

The decision remains **seven failed checks out of 25**, without budget changes:

| Failed proposed check | Rejected candidate | Required limit / baseline comparison |
| --- | ---: | --- |
| Phase 5 mobile p75 LCP | 2580 ms | <=2500 ms; baseline 2532 ms |
| Phase 5 desktop p75 LCP | 2564 ms | <=2500 ms; baseline 2568 ms |
| Mobile selection p75 | 1295.7 ms | +14.86%, exceeds 10% regression allowance |
| Desktop selection p75 | 1276.2 ms | +12.18%, exceeds 10% regression allowance |
| Mobile disclosure p75 | 188.6 ms | +22.95%, exceeds 10% regression allowance |
| Desktop disclosure p75 | 197.4 ms | +38.72%, exceeds 10% regression allowance |
| Desktop filter p75 | 62.2 ms | +20.31%, exceeds 10% regression allowance |

LCP tails worsened in all cells. Root's transfer reduction did not justify these
failures. Phase 5's complete HTTP transfer increased by 6322 bytes (445757 to
452079); worker costs and all deferred bytes remain disclosed in the results.
The original eager imports/build structure and oversized-chunk advisory remain
active. The rejected patch is **not applied**: all original application
JS/TS/TSX/CSS, backend/API routes, dependencies/locks, corpus/oracles, prior tests,
rules, source gate and exact **5000-ms worker deadline** match the baseline.
Only a dry-run `git apply --check` validated patch reproducibility.

Preservation checks reconfirm all 171 protected historical files and all 193
other reviewed files unchanged; this finalization changes only this report.
The 29 corpus scenarios, six deletion survivor snapshots and 27 approved source
files remain exact. ADR-015 through ADR-022 remain byte-identical and PROPOSED.
The fictional Phase 6B fixtures remain disabled by default, ASGI-only, untouched
and unmounted from normal FastAPI.

The original pinned lab environment remains recorded in the baseline: Node
22.15.0, Vite 8.3.8, Playwright 1.65.1, Chromium 159.0.8154.6, Windows 11 build
26200 on the documented i5-10210U host, page CPU 4x and 150-ms / 1.6-Mbps-down /
0.75-Mbps-up network emulation. Worker CPU-throttle inheritance, isolated parse
CPU, complete browser worker waterfall phases, OS cache/power/thermal control,
physical-mobile equivalence and production/field performance remain unverified.
Sequential host observations do not isolate timing-regression causes. No new
performance, durable-session/consent, provider, legal or security guarantee is
created by merging evidence. P5-F02 and G-S3 remain unresolved; the scaffold
roundtrip is not PostgreSQL restricted-role/RLS/tenant endpoint assurance.

The report-only follow-up triggers fresh main CI. Its final HEAD, clean
synchronization with origin/main and exact final CI result are reported in the
finalization response, avoiding a self-referential report commit hash. The merge
SHA above remains authoritative regardless of the report-only follow-up SHA.

**Stop after finalization: measurement completed; candidate rejected; P5-F01 open.**
No rejected-patch reapplication, budget relaxation, new performance candidate,
Phase 6C, real auth/data, tenant persistence, provider connection or deployment
is authorized.
