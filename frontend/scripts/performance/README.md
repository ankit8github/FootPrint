# Isolated synthetic production benchmark

Run from the repository root with the locked frontend and backend dependencies
installed. Node 22.15.0, Python 3.11.9 and the Playwright-locked Chromium are
required. Install Chromium using the existing smoke-test instructions. Set
`PLAYWRIGHT_BROWSERS_PATH` if using a repository-local browser cache. Ports 8000
and 5185 must be free. No development server, HMR or external provider is used.

```text
npm run build --prefix frontend
node frontend/scripts/performance/build.mjs .local/performance/observed frontend/dist
node frontend/scripts/performance/run.mjs .local/performance/observed .local/performance/run 30
node frontend/scripts/performance/summarize.mjs .local/performance/run .local/performance/observed-inventory.json .local/performance/evidence.json
node frontend/scripts/performance/compare.mjs docs/performance/phase6b04-baseline.json .local/performance/evidence.json .local/performance/budgets.json
```

Use fresh build/output directories; the graph build does not delete old files.
Keep the ordinary-build verification argument shown above to reject stale JS/CSS.
The graph plugin is observational. The optional ordinary-build argument verifies
identical JS/CSS names, sizes and hashes. Production HTML has a fresh CSP nonce,
so its hash and compressed size can vary between builds. Each run refuses an
existing samples file; failed samples are recorded and abort the stage. No retry,
outlier trimming or parallel browser sampling is performed. Calibration uses a
separate output directory and count 1; it never substitutes for the 30-run data.

`run.mjs` owns a normal loopback FastAPI child and a loopback archived-asset
server, and closes both on completion/failure. It never mounts Phase 6B fixtures.
The only API proxy is the existing empty demo GET. The server cannot serve corpus
files. Three fixed approved corpus files are selected through the file chooser;
all processing stays in the original browser workers. No probe is imported by
the application or included in its assets.

Four cells run serially in round-robin order: `/` and `/phase5`, each at 390x844
and 1440x900, DPR 1. Every sample launches a fresh Chromium process/context,
clears/disables browser cache and applies page-target CPU 4x and network
150 ms / 200000 B/s down / 93750 B/s up. Runtime requests, workers, storage,
cookies, console errors and WebSockets are checked. The complete JSONL contains
all samples, navigation/resource timings, HTTP waterfall and served-byte ledger.
Environment JSON records software/hardware and instrumentation SHA-256 hashes.
One initial trace and screenshot per cell are retained. All samples collect the
same trace categories; only the first trace per cell is written to disk.

The total HTTP metric uses the server's public socket counters with one request
per `Connection: close` connection, including request/response headers and worker
scripts. Gzip bodies are independently inventoried. Chromium under-reports worker
response bodies in this runner; those zeroes are not treated as zero transfer.
TCP/IP overhead, TLS, and the server-to-backend proxy hop are outside this metric.
There is no production transport/hosting claim.

LCP is the last initial-view candidate before input after application readiness
and network quiet. Interaction proxies run from the DOM change/click event to
the expected UI and two animation frames: selection, priority filter, disclosure,
and deletion recomputation. Automation may dispatch untrusted change events;
these are not INP. CDP execution/layout/style/task counters are separate and
non-additive. Compile/parse trace event sums are inclusive, overlap, and are not
isolated syntax-parse CPU. Worker CPU-throttle inheritance, OS disk cache,
thermal/power state and physical mobile equivalence remain unverified.

Summaries use nearest-rank p50/p75/p95, min/max and all 30 values. Compare the
same cells and identical instrumentation hashes before/after. Changing core
instrumentation requires a new complete baseline, not adjustment of old values.
The published evidence includes raw numeric rows, every waterfall and complete
asset/module graphs; full local JSONL/trace/screenshot hashes identify archives.
For an independent baseline, build commit
`4565d4c5665f941b486d569c35fe7aebc14654f2` in a separate disposable checkout and
copy only this observation tooling there. Do not overwrite a working checkout.

`compare.mjs` records every proposed budget and exits nonzero on any failure;
it never raises a target. A failed proposed budget remains a product/security
review blocker even when functional CI is green. Static loading/privacy CI does
not replace this host-specific 30-run statistical evaluation.

After an ordinary build, `npm run test:performance --prefix frontend` runs seven
production loading/privacy scenarios and static proposed JS budgets. It checks
root/Phase 5 in both viewports and each of the three other labs, including worker
selection timing and route-module exclusion. Its single samples are regression
checks; CI hardware does not validate local timing budgets. Existing nine browser
scenarios and all existing unit/security tests run separately and remain intact.

The measured candidate was rejected and rolled back. The active source retains
the original eager loading and unresolved budgets. CI explicitly uses
`npm run test:performance --prefix frontend -- --baseline`: seven privacy/worker
scenarios plus exact original JS/CSS hash preservation, with the expected eager
route-module inventory. This flag does not claim lazy loading or budget success.
The strict default check fails on the restored main bundle, as it should.
The comparison tool likewise exits 1 for the recorded seven budget failures.
To reproduce the rejected experiment, apply
`docs/performance/phase6b04-rejected-candidate.patch` only in a separate disposable
checkout of the baseline, build it and run the strict checks/full measurement.
The patch is review evidence and is not applied by the app, tests or CI.
