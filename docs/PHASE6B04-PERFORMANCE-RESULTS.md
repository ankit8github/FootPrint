# Phase 6B-04 measured import-loading experiment

**Rejected and rolled back.** “After” below means the measured candidate, not
the final active application. Original imports/build structure are restored;
P5-F01 and the original advisory remain open. No performance remedy is accepted.

Compare with the [unchanged-main baseline](PHASE6B04-PERFORMANCE-BASELINE.md)
and [pre-implementation plan](PHASE6B04-PLAN.md). Proposed budgets remain review
proposals; no threshold, worker deadline, validation or source allowlist changes.

## Changes tested and measured costs

The entry starts only the selected screen's dynamic import and a shared renderer
in parallel. It waits for both before the original StrictMode mount. Pathname
selection, fallback to App, anchors and all screens remain the same. This avoids
waiting for React DOM before requesting the selected screen. Vite's existing
module-preload helper handles only that selected import's dependencies. No route,
data, provider or worker is preloaded for an unused screen.

AssessmentDetails was extracted verbatim into its own module; AssessmentLab
imports/re-exports it to preserve the previous export contract. IntegratedMvp
imports the smaller view directly. All guards, markup, prose and semantic rules
are identical. Vite config, CSS sources, dependencies and locks remain unchanged.
No manual chunk policy or warning-limit change was needed.

A separate four-cell production pilot tried React.lazy/Suspense around the
parallel import. It passed loading/privacy checks but introduced a fallback
render and another reveal. Pilot LCP values were 2688/2972 ms for root and
3276/3208 ms for Phase 5, mobile/desktop. These single observations do not
establish a distribution or isolate causality. The final variant instead mounts
the existing view once both imports resolve; it adds no transient screen. Pilot
data/build are retained at `.local/phase6b04-validation/check-1795585085315/`
and `candidate-dist`/`candidate-observed-inventory.json`. They are excluded from
the final 120-sample comparison and are not substituted for slower final values.

The renderer and JSX/React runtime are shared across page routes. The PSL-aware
dependency remains one page-realm copy; each isolated worker retains its existing
copy. All three emitted worker assets have **identical filenames, raw/gzip sizes
and SHA-256 hashes** to baseline. No worker/controller/parser/rule/action source
changed. Selection/recompute still creates and terminates separate workers under
the exact 5000-ms deadline. Worker duplication across isolated realms is disclosed
and retained; no worker code is pulled into the bootstrap.

| Metric, per complete measured flow | Before `/` | After `/` | Before `/phase5` | After `/phase5` |
| --- | ---: | ---: | ---: | ---: |
| Initial raw JS bytes | 527589 | 225392 | 527589 | 514541 |
| Initial gzip-6 JS bytes | 191121 | 70973 | 191121 | 190610 |
| Deferred raw JS bytes | 0 | 0 | 598014 | 598014 |
| Deferred gzip-6 JS bytes | 0 | 0 | 247774 | 247774 |
| Complete encoded bodies, all types | 192762 | 72364 | 440439 | 440189 |
| Complete HTTP request+response bytes with headers | 197222 | 80091 | 445757 | 452079 |
| Requests (including two workers in Phase 5) | 4 | 7 | 5 | 11 |

Root initial gzip JS falls **62.86%** and complete HTTP bytes **59.39%**. Phase 5
initial gzip JS falls only **0.27%**; its complete HTTP bytes **increase 1.42%**
(6322 bytes) because six extra requests outweigh the 250-byte encoded-body
saving. This is a material disclosed cost of splitting, not a Phase 5 transfer
improvement. Both worker fetches total 247774 gzip bytes in each version because
cache remains disabled through recomputation. Warm-cache reuse is unverified.

All emitted page JS, including unused routes, increases from 527589 to 530863
raw bytes and 191121 to 197470 gzip bytes (+3.32% gzip). All emitted JS including
the three workers increases from 1400525 to 1403799 raw and 555062 to 561411 gzip
bytes. CSS sources are unchanged; two compressed CSS assets total 1470 bytes
versus 1203 combined before. No feature or cost is removed from this accounting.
The largest page chunk is 271184 bytes; the largest emitted JS including workers
is 299007 bytes. The default Vite advisory disappears because chunks are smaller;
that alone does not resolve P5-F01.

The four representative initial screenshots (both routes and viewports) are
**byte-identical PNGs** before/after: mobile root 75748 bytes, mobile Phase 5
93220, desktop root 78918, desktop Phase 5 104897. This supports initial-view
visual preservation only; existing tests cover interactions and other screens.

## Matched distributions and acceptance decision

Executed **120 baseline + 120 candidate cold samples**, 30 per cell in each
stage, zero failures/retries/discarded values. Exact before/after environment,
protocol and five instrumentation hashes match. Full [candidate assets/graphs and
statistics](performance/phase6b04-results.json), [120 candidate numeric rows and
waterfalls](performance/phase6b04-results-samples.jsonl), [all 25 budget checks](performance/phase6b04-budgets.json)
and the [rejected source patch](performance/phase6b04-rejected-candidate.patch)
are committed. Local complete JSONL/traces/screenshots are under
`.local/phase6b04-validation/after`; JSONL hashes are in the evidence files.

| Route/viewport | Before LCP p75 | Candidate LCP p50 / p75 / p95 | Candidate max | Script / layout p75 |
| --- | ---: | ---: | ---: | ---: |
| `/` mobile | 2640 | 2044 / 2208 / 3332 | 3376 | 547.8 / 523.9 |
| `/` desktop | 2564 | 2076 / 2180 / 2868 | 3420 | 536.7 / 539.9 |
| `/phase5` mobile | 2532 | 2460 / 2580 / 3200 | 3392 | 543.1 / 489.7 |
| `/phase5` desktop | 2568 | 2416 / 2564 / 3348 | 3416 | 541.3 / 488.5 |

Every cell's LCP p95 and maximum are worse than baseline. Phase 5 mobile p75
also regresses (2532 to 2580 ms); desktop's 4-ms improvement is insufficient for
2500 ms. Root's lower p75 does not excuse Phase 5 failures or the worse tails.

| Phase 5 operation | Mobile candidate p50 / p75 / p95 | p75 change | Desktop candidate p50 / p75 / p95 | p75 change |
| --- | ---: | ---: | ---: | ---: |
| Selection | 1124.9 / 1295.7 / 1366.3 | **+14.86% FAIL** | 1092.4 / 1276.2 / 1346.1 | **+12.18% FAIL** |
| Priority filter | 43.6 / 54.0 / 74.3 | -7.06% | 40.4 / 62.2 / 68.7 | **+20.31% FAIL** |
| Disclosure | 117.8 / 188.6 / 234.8 | **+22.95% FAIL** | 112.9 / 197.4 / 247.8 | **+38.72% FAIL** |
| Recompute | 906.3 / 966.3 / 988.1 | +5.75% | 912.4 / 972.1 / 1014.0 | +5.30% |

Nearest-rank p50/p75/p95; timings in ms, rounded here only. All unrounded values,
min/max, FCP, long-task/style/task distributions and inclusive compile-event
evidence are retained. These counters overlap and are not additive.

**Seven of 25 proposed checks fail:** both Phase 5 LCP cells; selection and
disclosure in both viewports; desktop filter. Root/Phase 5 initial gzip budgets,
maximum raw chunk size, unused-route exclusion and selection-only worker loading
pass in the candidate. The comparison command exits **1** and writes every
failure; no target was raised, waived or silently rounded into a pass.

Representative first mobile candidate Phase 5 waterfall:

| Request | Start from navigation (ms) | Duration (ms) | Body bytes |
| --- | ---: | ---: | ---: |
| document | 0.0 | 193.1 | 335 |
| index-CXmjuSuf.js | 294.6 | 224.5 | 1483 |
| index-lVi0YC3-.css | 294.7 | 204.9 | 959 |
| IntegratedMvp-D9IeWGNM.js | 550.5 | 312.2 | 5431 |
| jsx-runtime-Am8b9ysO.js | 550.8 | 292.5 | 3116 |
| AssessmentDetails-CRdTylCr.js | 551.0 | 276.2 | 2123 |
| parsers-NWfqFHAR.js | 551.2 | 1181.1 | 113411 |
| IntegratedMvp-oQGNQ3KE.css | 551.5 | 226.5 | 511 |
| render-CadkVlM9.js | 551.6 | 946.8 | 65046 |
| selection assessment worker | 4374.9 | 844.9 | 123887 |
| recompute assessment worker | 6557.4 | 820.7 | 123887 |

The extra dependency-fetch stage and requests are observable. Host thermal/power
state and background scheduling are unverified, so the sequential runs do not
isolate the cause of each timing regression. No outlier replacement or extra
favorable run was used to rehabilitate the failed candidate. The separate final
candidate seven-scenario functional check passed; it is not 30-run budget evidence.

## Rollback and review stop

The exact five-file candidate is preserved in the patch. After checking for
concurrent edits, restored main.tsx, AssessmentLab.tsx and IntegratedMvp.tsx from
the verified baseline and removed only the two introduced source modules. The
patch passes `git apply --check` on the restored tree. Final ordinary JS/CSS
assets must match the baseline byte-for-byte; HTML nonce may differ. All active
application source is unchanged from main. No new runtime code, source-validation
exception, timeout, CSS redesign or dependency change remains.

Focused CI explicitly runs `test:performance -- --baseline`: all seven
production privacy/worker scenarios and exact baseline JS/CSS hashes. It expects
the original eager route-module inventory. It does **not** assert performance
success. The strict default candidate check fails on restored main, and the
recorded statistical comparison fails seven targets. These are visible outcomes,
not skipped negative cases disguised as passing tests.

**P5-F01 remains OPEN. Stop for product-owner/frontend-security review.** This
PR delivers reproducible measurement and rollback evidence, not an approved
remediation. No alternative budget is proposed here. Further optimization needs
review of the failed distributions, host-control limitations and request costs.
P5-F02, G-S3, all prior proposed ADRs and inherited security/legal/provider gaps
remain unresolved. No Phase 6C, database, real auth/data/provider, deployment or
beta work follows from this experiment.

All baseline measurement limitations remain: page-target CPU throttling only;
worker inheritance unverified; no reliable isolated syntax-parse CPU; inclusive
trace sums; input-to-two-frame proxies rather than INP; incomplete browser worker
waterfall phases; exact server HTTP accounting excludes TCP/IP/TLS/backend hop;
OS disk cache, power/frequency and physical mobile equivalence unverified. Green
functional CI cannot establish production performance or independent assurance.
