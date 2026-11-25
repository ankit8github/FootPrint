# Phase 6B-04 implementation and measurement plan

Date: 2026-11-25 (Asia/Calcutta). Written before implementation or baseline
measurement. Scope: isolated frontend production-build performance experiment.

Preflight: clean synchronized main/origin/main at
`4565d4c5665f941b486d569c35fe7aebc14654f2`; verified Phase 6B-03 merge
`c2bc3be8a18d9917bfb1e0a490497652f54b81ce` ancestry. No local changes reset.
Branch: `phase6b/frontend-performance`. No applicable AGENTS.md found. Read 6A
plan 6B-04 and security design section 8/S6A-10, Phase 5 P5-F01/F02 and privacy
boundaries, immutable corpus guide, 6B-03 completion, frontend/controller/worker
and browser tests. Current entry eagerly imports all screens; worker constructors
remain selection-driven. Inspect actual graph/waterfall before changing this.

## Protocol, instrumentation and proposed budgets

1. Build unchanged application using locked Node 22.15.0/npm 10.9.2/Vite 8.3.8.
   Archive exact production dist, file hashes, raw and gzip level-6 byte counts.
   Obtain per-chunk module/import graph with an observational build plugin and
   verify JS/CSS asset bytes match the ordinary build. No application edits first.
2. Serve the archived build on loopback only with deterministic gzip level 6,
   no-store, HTTP/1.1 Connection:close, no HMR, restrictive local headers and only
   existing demo API proxy. Public server socket byte counters capture complete
   browser HTTP request+response payloads, including workers; TCP/IP overhead and
   the backend proxy hop are outside that browser-transfer metric.
   Raw corpus is never served. The normal FastAPI API supplies the original empty
   demo response. Refuse occupied ports or fallback to a development build.
3. Run **30 cold iterations for each of four cells**: `/` and `/phase5`, each at
   390x844 and 1440x900, device scale 1. Repeat identical 120-run protocol after
   any remediation. Fresh Chromium process/context per iteration; clear browser
   HTTP cache; no application data, cookies, storage or service workers carried.
   Serial round-robin cells, no parallel benchmarks/builds/test suites. Record
   all samples/errors; no discarded outliers, hidden retries or warm-up samples
   counted as cold measurements. Calibration runs are explicitly separate.
4. CDP main-page CPU slowdown **4x** and network **1.6 Mbps download / 0.75 Mbps
   upload / 150 ms RTT** (200000/93750 bytes per second). Record exact browser,
   Playwright/Vite/Node/npm/OS/CPU/core/RAM versions; publish no username/hostname.
   Document worker-target throttle limitations rather than assuming inheritance.
5. Install LCP observer before navigation; capture final initial-view LCP before
   input, after application readiness/network quiet and settled animation frames.
   Record navigation/FCP, CDP script/task/layout/style CPU counters and available
   compile/parse evidence. CPU counters are distinct and not additive. Missing or
   unreliable parse/worker CPU/transport measurements are **unverified**, never 0.
6. Capture each HTTP request stage/waterfall, compressed/uncompressed JS/CSS,
   initial/deferred/dynamic/worker assets, and total encoded request/response bytes
   using installed Playwright/CDP instrumentation where supported. Retain server
   body-byte ledger as independent fallback; disclose missing headers/TCP overhead.
   No initial worker or lab selection side effects. No arbitrary synthetic input
   is added to the runtime allowlist.
7. On `/phase5`, consent and select the unchanged registration-shop, receipt-shop
   and core-history files (same existing smoke scenario). Measure browser DOM input
   event through settled UI for initial findings, priority filter, disclosure and
   Remove Source 2 full recomputation. Validate expected 4 then 3 findings and
   worker creation/termination. Exact **5000 ms worker deadline unchanged**.
   Small test-only readiness waits are not application timeout changes.
8. Use nearest-rank p50/p75/p95, min/max and all raw samples. Primary interaction
   comparison is p75 browser input-event-to-two-animation-frame completion for
   selection/filter/disclosure/recompute, per viewport. Record worker-inclusive
   total transfer and separate initial/deferred totals; no main-chunk-only claim.

| Proposed target (evaluation, not approved policy) | Criterion |
| --- | --- |
| Root initial gzip JS | <=100 KiB |
| Phase 5 initial total gzip JS | <=220 KiB |
| Every emitted application JS chunk, including workers | <=500 KiB raw |
| Both routes, both viewports | Lab p75 LCP <=2500 ms |
| Each measured interaction/recompute | p75 regression <=10% against same-cell baseline |
| Loading behavior | No unused lab request until navigation; no worker until selection |

These are proposed architecture budgets from 6A/user instructions, not permission
to change warning thresholds or make field/Core Web Vitals claims. Fresh browser
processes do not flush OS disk caches or establish mobile-device equivalence;
4x slowdown is host-relative. Benchmark serving, profiling and input automation
are lab instrumentation and must be identical before/after. Keep raw JSON,
waterfalls, asset graph and representative screenshots locally; publish minimized
synthetic result evidence or exact reproduction commands with artifact hashes.

## Acceptance IDs and implementation sequence

| ID | Required evidence |
| --- | --- |
| PF-01 | Unchanged-main archive, hashes, asset/import/module graph and four 30-run cold baseline cells before application edits |
| PF-02 | Exact emulation/version/hardware disclosure, raw samples, p75 LCP, initial waterfall and execution/render/interaction distributions; unsupported measurements labeled |
| PF-03 | Targeted lazy/Suspense and shared-boundary change justified by graph; all route/UI semantics retained; initial and aggregate worker-inclusive byte accounting |
| PF-04 | Proposed budgets evaluated without raising thresholds; all regressions/failures disclosed; rollback if behavior/security/performance targets regress |
| PF-05 | Focused production lazy-loading/privacy/worker checks plus all 564 backend, 284 frontend and nine existing browser tests unchanged |
| PF-06 | Exact preservation: corpus 29 scenarios/six survivors/27 raw files, source gate, parser/discovery/assessment/action rules, bounds, 5000-ms deadline, API/contracts/migrations, default-disabled ASGI fixtures and all prior ADRs |
| PF-07 | Four required documents, reproducible scripts, before/after assets/waterfalls/distributions, exact head/file inventory and fresh push/PR CI/GitGuardian evidence |

First implement observation-only build/serve/benchmark tools and calibrate them;
then complete unchanged baseline. Investigate route lazy loading and measured
shared-dependency splitting. Change only justified import/module boundaries; no
CSS redesign or rule/worker refactor. Complete after measurements, compare all
budgets and bytes, and add focused tests. Run frozen full checks and fresh CI.
Do not run expensive validation concurrently with timed benchmark samples.

## Preservation, rollback and stop

All existing test files, backend code/experiments, source corpus/oracles, source
allowlist, worker scripts/controller deadlines, parser/rule/action modules, API
contracts, migrations, dependencies/locks and ADRs are protected. Any necessary
module extraction preserves exact component markup/guards and old exported test
contracts. No provider/API/data processing expansion or runtime telemetry.

On behavior/security/target regression, restore original imports/build structure;
keep evidence and P5-F01 open, document failed budget and stop for review. No
cherry-picked sample replacement, timeout increase, reduced test matrix, loosened
validation, suppressed errors or chunkSizeWarningLimit increase. P5-F02 and G-S3
remain unresolved. All prior PROPOSED ADRs retain that status. This work does not
establish production performance, auth/browser security or independent assurance.

Deliver a separate unmerged PR against main (GitHub assigns the number; expected
#10) and stop for product-owner/frontend-security review. No merge, Phase 6C,
tenant schema/database work, production auth, real users/data/providers,
deployment or beta enrollment.
