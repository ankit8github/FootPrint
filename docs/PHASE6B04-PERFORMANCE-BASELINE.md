# Phase 6B-04 unchanged-main performance baseline

Measured 2026-11-25 before application edits, at main
`4565d4c5665f941b486d569c35fe7aebc14654f2`. The ordinary production build was
archived in `.local/phase6b04-validation/baseline-dist`; an observational graph
build produced identical JS/CSS filenames, bytes and SHA-256 values. HTML has a
fresh CSP nonce. Full [inventory, module/import graphs, environment and statistics](performance/phase6b04-baseline.json)
and [all 120 numeric rows and request waterfalls](performance/phase6b04-baseline-samples.jsonl)
are committed. Local complete JSONL, traces and screenshots are under
`.local/phase6b04-validation/baseline/`; its JSONL hash is in the inventory.

## Environment and reproducible method

Node 22.15.0; npm 10.9.2; Vite 8.3.8; Playwright 1.65.1;
Chromium **159.0.8154.6** (locked Playwright Chromium revision 1255), headless;
Windows 11 Home Single Language 10.0.26200 build 26200, x64;
Intel Core i5-10210U @1.60GHz, four physical/eight logical cores,
8,365,002,752 bytes visible RAM. Python 3.11.9 supplies the unchanged normal API.
Versions, CPU/RAM, protocol and five instrumentation hashes are also machine
readable. No username/hostname is published.

Executed **30 cold samples per route/viewport, 120 total**, serial round-robin,
zero failures/retries/discarded values. Mobile 390x844, desktop 1440x900, DPR 1;
fresh browser process/context, cleared/disabled HTTP cache, page CPU 4x,
150 ms RTT, 200000 B/s down and 93750 B/s up. Archived production assets are
served with gzip level 6, no-store and Connection:close on loopback only. The
only API is the existing empty demo GET. No HMR, corpus serving or external fetch.
Two separate four-sample calibration runs are excluded from these statistics.

See the [plan](PHASE6B04-PLAN.md) and
[tooling instructions](../frontend/scripts/performance/README.md). Actual command:

```text
node frontend/scripts/performance/run.mjs .local/phase6b04-validation/baseline-dist .local/phase6b04-validation/baseline 30
node frontend/scripts/performance/summarize.mjs .local/phase6b04-validation/baseline .local/phase6b04-validation/baseline-dist-inventory.json docs/performance/phase6b04-baseline.json
```

## Exact assets and loading behavior

| Ordinary build asset | Raw bytes | gzip-6 bytes |
| --- | ---: | ---: |
| index.html | 588 | 341 |
| index-Bdh-iEi8.js | 527589 | 191121 |
| index-Dd3fVTG5.css | 3223 | 1203 |
| import.worker-DkRfHpQD.js | 282739 | 118612 |
| discovery.worker-BKysb9TZ.js | 291190 | 121442 |
| assessment.worker-C8IXT5T1.js | 299007 | 123887 |

Asset paths except HTML have the `assets/` prefix. The main asset hash is
`6e10ded8811392c006f6eb0dac25fe70cb4646f0c2ff2f13d210a3f74487ce08`;
every asset hash is in the inventory. Vite's gzip advisory reports 192.99 kB;
the actual benchmark server's explicitly pinned gzip-6 body is 191121 bytes.
Do not interchange compression implementations or kB/KiB units.

Both routes initially fetch the **same complete main bundle**, containing all
four labs plus App, React DOM and the PSL-aware domain dependency. The page
graph has 40 rendered modules. Large contributors before final minification
include react-dom-client.production.js (529545 rendered units), tldts trie.js
(163942) and suffix-trie.js (140274). These plugin `renderedLength` values are
attribution evidence, not additive minified asset bytes. Phase 5 imports the
shared AssessmentDetails view through AssessmentLab, retaining the unused lab
component. No manual shared-chunk or dependency-version change is justified yet.

No worker is requested or constructed initially. Phase 5 selection creates and
terminates one assessment worker; removing Source 2 creates and terminates a
second. With cache disabled throughout, both fetch the same 123887-byte gzip
worker. There are three unique emitted worker assets; four worker graph build
contexts include the assessment entry used from two page modules, not four
distinct emitted workers. No provider/data prefetch is present.

Representative first mobile Phase 5 waterfall (all 120 exact waterfalls retained):

| Stage/request | Start relative to navigation (ms) | Request duration (ms) | Body bytes |
| --- | ---: | ---: | ---: |
| initial document | 0.0 | 184.3 | 341 |
| initial main JS | 247.2 | 1172.6 | 191121 |
| initial CSS | 247.2 | 221.0 | 1203 |
| selection assessment worker | 2954.9 | 800.6 | 123887 |
| recompute assessment worker | 4325.2 | 801.3 | 123887 |

Root has four requests including one empty demo response; Phase 5 has three
initial requests and two later worker requests. Every sample has the same asset
set and byte totals. No duplicate demo/provider fetch, unexpected request,
WebSocket, console error/canary leak, cookie or browser persistence was observed.

| Transfer per completed flow (both viewports) | `/` | `/phase5` |
| --- | ---: | ---: |
| Initial raw / gzip JS bytes | 527589 / 191121 | 527589 / 191121 |
| Deferred raw / gzip JS bytes, including repeated workers | 0 / 0 | 598014 / 247774 |
| Total raw / gzip JS bytes | 527589 / 191121 | 1125603 / 438895 |
| Initial encoded body bytes, all types | 192762 | 192665 |
| Complete encoded body bytes, all types | 192762 | 440439 |
| Complete HTTP request+response bytes including headers | 197222 | 445757 |

## Distributions and baseline budget failures

All timings below are milliseconds, nearest-rank percentiles. Full min/max,
FCP, task/style/long-task distributions, compile events and every value are in
the linked evidence. CPU counters overlap and must not be added together.

| Route/viewport | LCP p50 / p75 / p95 | Script p75 | Layout p75 |
| --- | ---: | ---: | ---: |
| `/` mobile | 2524 / 2640 / 2696 | 610.5 | 500.5 |
| `/` desktop | 2460 / 2564 / 2708 | 560.9 | 490.5 |
| `/phase5` mobile | 2420 / 2532 / 2708 | 575.8 | 410.5 |
| `/phase5` desktop | 2460 / 2568 / 2712 | 550.6 | 451.7 |

| Phase 5 interaction | Mobile p50 / p75 / p95 | Desktop p50 / p75 / p95 |
| --- | ---: | ---: |
| Initial selection to four findings | 1089.9 / 1128.1 / 1367.7 | 1100.0 / 1137.6 / 1345.8 |
| Sensitive priority filter | 40.6 / 58.1 / 75.9 | 36.4 / 51.7 / 68.4 |
| Open disclosure | 127.5 / 153.4 / 221.6 | 119.0 / 142.3 / 198.3 |
| Remove Source 2 and recompute three findings | 893.7 / 913.8 / 995.4 | 903.6 / 923.2 / 997.6 |

Root initial JS **fails** proposed 100 KiB (186.64 KiB gzip); Phase 5 passes
220 KiB. Main JS **fails** proposed 500 KiB raw (515.22 KiB), and Vite emits its
unchanged advisory. All four p75 LCP cells **fail** proposed 2500 ms. No initial
worker load occurs, but unused lab code is fetched inside the eager main bundle.
These observations justify testing route-level lazy imports and extracting the
shared details view; they do not approve budgets or close P5-F01.

## Measurement limits

LCP is an initial-view lab observation before input, not field performance.
Input-to-two-frame interaction proxies are not INP; filter automation dispatches
an untrusted DOM change event. Initial CDP counters and tracing include probe
overhead consistently in every sample. Compile/parse trace sums are inclusive,
overlapping events; isolated syntax-parse CPU is **unverified**. Worker CPU
throttle inheritance is **unverified**. Worker transfer spans are observable but
Chromium exposes incomplete worker waterfall phases and zero encoded body sizes.
Those zeroes are replaced by actual server body accounting, never called zero
transfer. Browser-reported headers also differ from actual server socket counts;
complete HTTP totals use the latter with one request per connection.

HTTP totals exclude TCP/IP overhead and the server-to-backend proxy hop; no TLS
is involved. OS disk cache, thermal/power/frequency state and physical mobile
equivalence are **unverified**; host-relative 4x emulation is not a real device.
The benchmark blocks outside traffic and cannot characterize production hosting,
public networks, durable sessions, real authentication or real user data.
