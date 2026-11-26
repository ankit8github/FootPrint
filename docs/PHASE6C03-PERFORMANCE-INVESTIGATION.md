# Phase 6C-03: C03-R01 resource-budget investigation

Status: evidence complete for this bounded investigation; **C03-R01 OPEN**.
No remediation, durable adapter, merge or production capability is authorized.
Reviewed head: `5e1cd681d4d19193f4a2c4161b9e1b78b77de139` on
`experiment/phase6c03-shared-rules`; base/main:
`2038c65554501b7f0a099976ea07b75606cb7ff7`.
PR: [#13](https://github.com/ankit8github/FootPrint/pull/13), draft/open/unmerged.

## Finding and recommendation

The commercial failure is reproducible under the unchanged five-second child
deadline. The instrumented child used **4.953 CPU seconds**, was terminated after
**5.029 wall seconds including launch/kill**, and had not returned from
`linkEvidence`. No result was returned or published. Its Python model validation
also took **43.293 seconds before child launch**. This stage is outside the old
child deadline. Both paths contain full-observation scans repeated per alias.
Account assessment and the 4,000-row commercial assessment show additional CPU
cost. Startup, serialization and supervisory overhead are measured separately;
they are not a sufficient explanation for the failed commercial child.

Recommend a separate, explicitly authorized indexing-only remediation proposal
for the four locations below, preserving order and every validation/claim. Do
not raise limits, drop support, truncate output, remove the failed fixture or
claim the faster CI runs close C03-R01. No proposed source edit was applied.

## Preflight and preserved boundaries

Local HEAD, branch and live remote branch matched the reviewed head; local main,
origin/main and live remote main matched the expected base. The worktree was
clean. All **280 reviewed-head blobs** remain unchanged: the original 270 plus
all ten initial 6C-03 experiment/report/workflow files. The original 193 historical
and 252 prior-baseline checks also passed. In particular the old plan, security
report, benchmark receipts, runner, wrapper and TypeScript rules are preserved.

Read acceptance: implementation plan 6C-03; security S6A-04/06/12; threats
TM-07/09/10/13. The five-second deadline, 256-MiB committed-memory cap, 8-MiB
input and 32-MiB output limits, versions, corpus, 29 initial/six survivor oracles,
registry, schema/RLS/ledger and 5000-ms frontend deadline remain unchanged.
No new dependency, service permission, endpoint, network integration or durable
ID/save/delete implementation was introduced. All prior production and human
review gates remain OPEN; ADR statuses remain unchanged.

## Workload representativeness

The existing `fixture(kind, count)` generator was reused without modification;
no new observation families or catalog entries were created. Its 10,000-row
construction has 20 email sources, each with 500 rows. The discovery email branch
initializes `recordCount = 1` and produces row zero; only the history branch sets
record count from a multirow parser (`discovery.ts:109-135`). Even a 20-file raw
email selection cannot yield 10,000 email observations. History cannot provide
the email commercial features. A model-valid observation is not proof an adapter
produced it.

The actual offline entry additionally requires the pinned **whole-envelope**
catalog, not merely approved individual files or model validity. Its 70 profiles
share 32 distinct canonical batches. Inspection and actual admission checks show:

| Current catalog maximum | Value |
| --- | ---: |
| Selected sources | 3 |
| Total rows, including exclusions | 10 |
| Observations | 4 |
| Commercial aliases | 1 |
| Canonical input bytes | 1,977 |
| Measured full output bytes | 11,833 |

The ten-row batch has zero observations. The largest observation batches have
four observations from three sources. Every canonical batch was admitted and
profiled with both complete discovery/assessment hashes checked against immutable
expectations. All four 10,000-row stress families passed the model and were
**denied by the actual catalog with 422**. Commercial admission testing took
95.681 seconds including two model validations; this is separate from the
43.293-second validation in the measured execution case.

Thus the failed commercial input is an isolated **model-level capacity test**,
reachable through the metrics-only benchmark entry, not ordinary catalog
execution. It is not evidence of production exploitability. This distinction
does not turn its failure into a pass or relax the broad proposed capacity gate.
Admissible catalog performance and contract-shaped stress capacity are separate
claims. Arbitrary combinations of individually approved files are not thereby
enrolled in the whole-envelope catalog.

## Method and measurement coverage

New files only: a separate measurement builder/wrapper and Python harness.
The builder checks the existing artifact SHA-256 and copies its pure prefix
**byte for byte**; no business-rule body is edited or translated. The replacement
wrapper adds ten bounded numeric stderr markers around load, read, parse,
prepare, link, assess, assemble, serialize and write. It adds no inspector,
CPU-profile file reader/writer, DB or network interface. Child filesystem access
is limited to its trusted artifact and standard descriptors, as before.

Original artifact: `69fcc47c8b0890c488900b4afe875aa7ce19faa6e257a691ad371fd53edff064`.
Copied pure prefix: `73dbb73013b2a8ff0c364312adb6820b02a6de9ccb0d60ffd7adc9bc8cd58bb5`.
Instrumented artifact: `9fdc2ee12c7cff77dbad60231dcb7d25fb10f65dbffb5679af2219a2e5c9ed4f`.

Each fresh child receives the original Job Object committed-memory cap before
input, the same five-second process-wait deadline and input/output caps, and no
credentials. Diagnostic output is separately bounded to 16 KiB. Children run
sequentially, without warmup, retries, concurrency stress or unbounded loops.
The four existing families run twice at 20/1,000/4,000 rows; four 1,000-row
uninstrumented controls verify exact result parity. At 10,000 rows each family
runs once, with commercial last. Its failure stops further profiling.

All **64** planned child invocations were reached: 32 catalog, 24 matrix, four
controls and four full-size. There were 63 successful invocations and one
deadline termination. These are measurement samples, not 64 new pytest cases.
No semantic mismatch occurred in the 32 immutable comparisons, 12 repeated-input
pairs or four paired controls. Full-size constructed successes have no newly
invented oracle; only metrics and hashes are archived.

Wall clocks use `perf_counter`/`performance.now`; CPU uses Node `cpuUsage` and
Windows `GetProcessTimes` after exit, including a killed child's accumulated CPU.
CPU is summed across threads and may exceed wall time; fine-grained phase values
are coarse/quantized on this Windows host. See
[GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes)
and [Node 22.15 CPU usage](https://nodejs.org/download/release/v22.15.0/docs/api/process.html#processcpuusagepreviousvalue).
Startup-to-first-marker includes module parsing, process setup, pipe/reader
scheduling and OS startup; it does not isolate Node bootstrap alone. Phase wall
intervals include the preceding marker's small synchronous-write overhead.

Supervisor wall includes child launch/exit, collection, JSON decode and diagnostic
canonical hashing. Validation and input canonicalization are reported separately.
The profiler hashes discovery as well as the full result; this adds parent work
relative to ordinary execution. Its total wall is not an exact production-path
latency or an end-to-end five-second guarantee. The old timer's coverage excludes
parent validation and later result verification by inspection as well as timing.

## Measurements

Machine: Windows 11 Home Single Language, build 26200 (Python platform reports
`Windows-10-10.0.26200-SP0`); Intel Core i5-10210U @ 1.60 GHz, four physical/eight
logical cores, CIM maximum clock 2112 MHz; usable RAM 8,365,002,752 bytes,
preflight available RAM 953,772 KiB. Node 22.15.0; Python 3.11; unchanged locked
TypeScript 5.9.3 / tldts 7.5.5. CPU power/thermal/frequency behavior and paging
were not controlled or measured. No parallel test suites ran during profiling.

Catalog: all 32 passed; maximum child wall **0.3209 s**, supervisor wall
**0.3220 s**, peak RSS **34,476 KiB**. These maxima need not belong to one case.
Two-sample child wall ranges, seconds:

| Existing family | 20 rows | 1,000 rows | 4,000 rows |
| --- | --- | --- | --- |
| Account | 0.2248–0.3817 | 0.2350–0.2520 | 0.7812–0.8830 |
| Commercial | 0.1896–0.2194 | 0.3431–0.3941 | 2.1343–2.1884 |
| Unresolved | 0.2082–0.2923 | 0.2531–0.2615 | 0.4294–0.4407 |
| Duplicates | 0.2089–0.2116 | 0.2152–0.2206 | 0.2368–0.2715 |

Full-size measurements (seconds; RSS in KiB):

| Family | Child wall incl. launch/kill | Process CPU | Supervisor wall | Validation outside child budget | Total incl. validation/canonicalization | Peak RSS | Input / full output bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Account | 3.6821 | 3.4531 | 4.2788 | 0.6967 | 5.2571 | 76,484 | 3,359,465 / 4,882,083 |
| Unresolved | 0.9747 | 0.9063 | 3.1836 | 0.7853 | 4.3504 | 124,248 | 3,429,465 / 24,059,629 |
| Duplicates | 0.3745 | 0.4063 | 0.8687 | 0.6309 | 1.7417 | 71,100 | 3,609,456 / 4,702,302 |
| Commercial STOP | 5.0286 | 4.9531 | 5.0291 | 43.2930 | 48.6595 | ≥61,804, lower bound only | 4,289,466 / NOT MEASURED |

The timeout is still scheduled at five seconds; the extra 0.0286 seconds include
termination/wait overhead, not an increased deadline. The killed child's final
peak RSS and full output size are **NOT MEASURED**. Observed stdout bytes were
zero; this is an observed byte count, not a substituted missing output size.
No partial result/hash was returned. Markers ended after input preparation;
link completion, assessment and serialization were not reached/observed.

## Root-cause evidence and proposed minimal edits — NOT APPLIED

| Location in protected source | Evidence | Separate proposal |
| --- | --- | --- |
| `backend/experiments/minimized_contract.py:240-241` | For each commercial group, scan all observations. 1,000-row validation 0.349–0.404 s; 4,000-row 5.500–6.315 s; 10,000-row 43.293 s. Parent CPU for that measured case 42.563 s. | Build ordered alias→member lists once, then perform the same complete member/domain/feature checks. Preserve alias-first-seen order, exact member order, omissions/extra rejection and all error conditions. |
| `frontend/src/features/discovery/discovery.ts:59-64` | One full support filter per alias: 100 million visits at 10,000 distinct aliases/support rows. Link 58–78 ms at 1,000, 784–792 ms at 4,000; full-size killed while linking after startup/read/parse/prepare used only about 0.29 s. | Build ordered, relationship/domain-local alias membership once; retain sorted alias traversal, original member order and complete conflict support. No cross-domain alias index or changed conflict semantics. |
| `frontend/src/features/assessments/assessments.ts:42-45` | Primary support validation searches `relationship_evidence` per observation: N(N+1)/2 comparisons for one all-primary relationship. Account assess 42 ms at 1,000, 500–587 ms at 4,000, 3,103 ms at 10,000. | Precompute exact relationship/observation/role membership and source/adapter membership sets; keep every existing validity predicate and `invalid_support` outcome. Do not infer missing evidence. |
| `frontend/src/features/assessments/assessments.ts:67-68` | Nested paid/cancelled search is N² on the all-paid fixture, even with no cancelled rows. Commercial assess 97–100 ms at 1,000 and 1,084–1,117 ms at 4,000. Full-size assess is NOT TESTED because linking did not complete. | Preindex cancelled aliases, apply the identical valid-alias regex and paid predicate, then preserve the same boolean conflict result. Keep all relationship conflict/support construction unchanged. |

These are phase timing plus static operation-count evidence, not sampled
per-line CPU percentages. The measured shape supports the quadratic explanations;
JIT/GC and scheduling remain included. No exclusive instruction-level attribution
is claimed. Commercial full-size output generation is not a cause of the observed
failure because execution never reached that phase.

Output/serialization is nevertheless material in another family: unresolved
serialize **316.6 ms**, write **239.8 ms**, parent decode plus two diagnostic hashes
**2.208 s**. Its RSS rose from **77,564 KiB** at assembly to **124,248 KiB** after
write. The old worker evaluates its `maxRSS` field before stringify/buffering;
old successful receipts therefore do not measure the entire serialization peak.
The committed-memory Job Object cap still applies. Fixing measurement placement
in the old wrapper is a separate minimal proposal; it was not changed here.

A coherent remediation should address parent validation and both TS stages,
not promise that changing only discovery will meet the full capacity hypothesis.
Use indexes over existing evidence, not new rules or fewer checks. Any future
optimized core must be separately reviewed/versioned while retaining the old
engines, immutable expectations and registry bytes; no silent repin is authorized.
Require exact full-output and support parity on all 70 profiles, negative support
cases and these fixtures before considering activation. Expected speedup and
success at 10,000 rows after optimization are **NOT TESTED**.

## Portability, proposed capacity definition and residual limits

Both original local deadline failures remain in `PHASE6C03-BENCHMARK.json`; this
third local failure adds CPU/phase evidence. At the reviewed head, Windows GitHub
CI commercial runs passed in **1.688 s** (push) and **2.656 s** (PR); their 71
profile cases passed in 7.86/8.93 s. Existing numeric receipts also show all four
families passing there. CI Node/artifact pins match; runner CPU model, power and
load were not captured. These are different-machine measurements. It is plausible
that per-core throughput/JIT, load, power or memory conditions contribute, but
their individual contributions cannot be established retrospectively. This
investigation does not dismiss either environment or reinterpret earlier failures.

Keep the current five-second cutoff and **OPEN** broad capacity gate. If owners
find the intended workload specification inappropriate, a proposed alternative
for separate review is: explicitly distinguish the existing 32-batch catalog
functional performance claim from a future adapter-realizable envelope capacity
claim; define reference host/load and whether validation/output verification share
an end-to-end deadline. Develop adapter-realizable worst cases (including large
history and at most one row per email) in a separately authorized fixture task.
Keep this model-level stress regression and its failed status visible. Do not
silently narrow the model, enroll data, raise limits or declare the broad gate
passed by measuring only today's tiny catalog. No alternative was adopted here.

NOT TESTED: sustained-load percentiles, cold OS/cache isolation, thermal/power/
page-fault attribution, precise main-thread versus background JIT/GC accounting,
per-line sampling, new instrumented CI runs, post-optimization throughput, Linux
execution/isolation, memory exhaustion/cancellation/hostile child/output limits,
new adapter-realizable fixtures, durable provenance or lifecycle behavior. The
original missing independent human review, OS network denial, production G-S3,
P5-F01/P5-F02, legal/provider/security and durable lifecycle gates stay OPEN.
No privilege leak, unexpected child file/network access or semantic mismatch was
observed; this is not a comprehensive negative capability/security test.

## Checks, receipts and reproduction

Executed scoped frozen Ruff lint/format, strict Python typing on Windows and
with `--platform linux`, new JS ESLint and existing frontend TypeScript check:
PASS. Existing immutable-profile suite: **71 passed in 32.09 s**. Preservation:
all original 270 and all 280 reviewed-head blobs PASS. Existing reports unchanged:

- Plan SHA-256: `e7bf85d723c8fdcca267d50c6e51d4dc797ce171578d16f313d2e7e82443b422`.
- Security report: `b99edb26ed68960d4a0720bd7ddb760ec6c734bf61aee0dd3aae94731b120942`.
- Benchmark receipts: `fcdb2ecadf1e7ea90d3822306e22b115fd84707a72da39fd2409324924d534ef`.

Historical reviewed-head CI was rechecked: push/PR regression
45773821929/45773828036, tenant 45773821944/45773827949, shared-rule evidence
45773821983/45773827951 all SUCCESS; GitGuardian 139752581143 SUCCESS. This is
evidence for `5e1cd681...`, not an invented CI outcome for later investigation
commits. Full backend/frontend/browser/DB suites were not rerun locally in this
scoped task; their prior evidence is preserved. New push CI, if triggered, is
reported separately on PR #13 against its actual commit.

Complete numeric phase records: `PHASE6C03-PERFORMANCE-MEASUREMENTS.json`.
Catalog/matrix preceded the addition of full-mode admission timing and a
redundant post-exit RSS stop check; every child already had the kernel cap and
all recorded peaks were below that threshold. The full run used the final
harness. No profiling was repeated after the deadline stop. Parent peak memory
was NOT MEASURED.
Original cumulative per-run receipts remain in `.local/phase6c03-investigation-`
directories ending `c81dc07cfa8d4e18b6e017874fb8befa` (catalog),
`5e8a8d4184e44229ba51355b46a4bfeb` (matrix) and
`f756f7c1e04d4d25883200e4d2fec1a1` (full). No earlier evidence was erased.

```powershell
# Repo root, locked dependencies already installed. On a fresh clone only,
# first build the old pinned artifact with frontend/scripts/shared-rules/build.mjs.
node frontend/scripts/shared-rules/build-investigation.mjs
cd backend
uv run --frozen python -m scripts.investigate_shared_rules --mode catalog
uv run --frozen python -m scripts.investigate_shared_rules --mode matrix
uv run --frozen python -m scripts.investigate_shared_rules --mode full
# Full mode returns nonzero at the first failure; never retry by raising limits.
uv run --frozen pytest -q rule_tests
uv run --frozen ruff check scripts/investigate_shared_rules.py
uv run --frozen ruff format --check scripts/investigate_shared_rules.py
uv run --frozen mypy scripts/investigate_shared_rules.py
uv run --frozen mypy --platform linux scripts/investigate_shared_rules.py
uv run --frozen python -m scripts.check_phase6c03_preservation
cd ..\frontend
npx.cmd eslint scripts/shared-rules/build-investigation.mjs scripts/shared-rules/investigation-worker.mjs
npm.cmd run typecheck
```

Additions only: this report and its numeric JSON archive;
`backend/scripts/investigate_shared_rules.py`;
`frontend/scripts/shared-rules/build-investigation.mjs` and
`investigation-worker.mjs`. No existing tracked file, workflow, rule, contract,
schema, test or resource limit was changed. Final Git commit/state is recorded
with the PR delivery, binding this report without a self-referential commit hash.
No remediation or adapter implementation should begin without a separate owner
decision. AI-assisted analysis is not independent human security approval.
