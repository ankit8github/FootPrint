# Phase 6B-04 report: measured experiment rejected and rolled back

Date: 2026-11-25. Scope: isolated synthetic frontend performance measurement.
**No performance remediation is accepted.** The route-loading candidate failed
seven proposed checks and was rolled back. P5-F01 remains OPEN; original eager
imports and the original Vite advisory remain. Deliver the evidence for
product-owner/frontend-security review; do not merge or start another phase.

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
| Scaffold migration roundtrip | Not run locally; preserved Docker CI step must be verified from fresh job logs below. No tenant/RLS claim |

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

**Leave PR #10 unmerged. Stop for product-owner/frontend-security review.**
No further optimization, Phase 6C/database work, production authentication,
real-user/provider integration, deployment or beta enrollment is authorized.

## GitHub delivery evidence

Exact pushed head, PR URL, push/PR CI and GitGuardian results are populated after
remote verification. A later report-only commit may follow the tested code head;
the PR records its exact current head and fresh final check results, avoiding a
self-referential report commit hash. Main is not modified or merged by this work.
