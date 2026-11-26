# Phase 6C-03 security report — STOPPED, incomplete experiment

This is AI-assisted engineering evidence, not independent human security approval.
Phase 6C-03 acceptance is **not achieved**. Implementation stopped at the first
measured resource-budget failure, as requested. No adapter, serving route,
persistence path, schema change or production capability was added. Do not merge.

Base: `2038c65554501b7f0a099976ea07b75606cb7ff7`.
Branch: `experiment/phase6c03-shared-rules`.
The final commit and exact-head push/PR CI receipts are bound to this report by
the draft PR description and final delivery; use `git rev-parse HEAD` to reproduce
the checked-out commit. The report cannot contain its own Git commit hash.

## Demonstrated stop result C03-R01

**Classification:** engineering acceptance failure of a proposed capacity limit;
not a demonstrated production vulnerability. The unchanged rules exceeded the
proposed five-second child wall deadline on a constructed 10,000-row commercial
fixture. The supervisor raised the fixed `DEADLINE` error and killed/waited for
the child. It returned no result. No application or database publication exists.

Exact reproduction, from the verified base plus these additive experiment files:

```powershell
cd I:\FootPrint\frontend
node scripts/shared-rules/build.mjs
cd ..\backend
uv run --frozen python -m scripts.benchmark_shared_rules
```

The script uses four fixed, bounded cases and stops at the first failure. It
does not contain an unbounded stress loop or relax any resource limit. Receipt:
`.local/phase6c03-validation/benchmark.json`. Initial measured results:

| Constructed fixture | Rows | Child wall time | Peak child RSS | Input bytes | Output bytes | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Primary account support | 10,000 | 4.094 s | 64,208 KiB | 3,359,465 | 4,882,083 | PASS on this run |
| Distinct commercial aliases | 10,000 | five-second deadline reached; exact elapsed not recorded | NOT MEASURED on killed child | 4,289,466 | NOT MEASURED on killed child | STOP / DEADLINE |
| Unresolved-only | 10,000 | NOT TESTED after stop | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED |
| Duplicate copies | 10,000 | NOT TESTED after stop | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED |

These constructed fixtures pass the existing minimized model, but are **not**
approved catalog batches, raw-parser outputs or newly admitted sources. They use
20 email sources with 500 modeled rows each, whereas the existing raw email
adapter yields one row per file. Ordinary `execute` rejects their whole-envelope
digest. This is a capacity hypothesis for contract-shaped unit data, not evidence
that an approved browser selection can trigger the failure. There is no claim of
real-world exploitability, accuracy or production workload representativeness.

The commercial fixture contains one distinct collection-local alias per row and
no raw order references. Its generator JSON SHA-256 is
`18ace3e956a25cf8ce76940d7a75a0a700781948835dd6d56b9066690bc50987`.
The initial benchmark artifact was
`8615b245400297c4e721505e84f01bbe49f844f2e4080805488ceff1d0076e56`.
The final wrapper uses ESM to satisfy frozen lint; the extracted rules are
unchanged. Final artifact hash:
`69fcc47c8b0890c488900b4afe875aa7ce19faa6e257a691ad371fd53edff064`.
The final ESM repetition again stopped on the commercial fixture; its account
fixture took **2.516 s**, **66,932 KiB** peak RSS and the same input/output byte
counts. Both failures are retained in `PHASE6C03-BENCHMARK.json`. Neither killed
child's peak memory/output size was captured, and neither is reported as zero.

Relevant existing work includes per-alias support scans in `linkEvidence` and
per-observation support searches/nested commercial searches in `assessDiscovery`.
These can grow quadratically; no profiler attribution was performed, so they are
a likely cost source, not a proven exclusive cause. Host scheduling was not
controlled. Repeated percentile/capacity calibration is NOT TESTED. A faster CI
measurement cannot erase this observed local failure or complete the stopped
adapter. Minimal next decision: review representable workloads and the proposed
budget in a separate authorized task; any change to frozen contracts/rules needs
explicit review. No larger limit, truncation, rule rewrite or oracle update was
applied here.

## Partial artifact and trust boundary

`build.mjs` verifies all eight normalized engine/source pins against the immutable
registry manifest, selects exact TypeScript AST declarations (not reimplemented
rules), transpiles them using TypeScript 5.9.3 and includes the pinned tldts 7.5.5
self-contained distribution. Parser/File/raw-reading declarations are omitted.
Fixed explanations and the existing PSL-aware domain helper are reused.
Generated worker/provenance files are ignored under `.local/phase6c03-build`.
Node is pinned to 22.15.0 at build. Package locks/dependencies remain unchanged.
No second classifier exists in Python.

The Python research supervisor revalidates retained model state and requires the
independently pinned whole-envelope catalog for ordinary execution. It provides
only minimized stdin, bounds collected stdout, suppresses child diagnostics,
checks successful exit and verifies the complete result against immutable
assessment hashes before returning it. Discovery hashes are independently checked
by the new tests. Browser classifications/relationships are not input fields.
Constructed benchmarks validate the model but return metrics only, never findings.

The local Windows child is attached to a Job Object before evidence is supplied,
with a 256-MiB process committed-memory cap and kill-on-job-close. This is **not**
an RSS cap; peak RSS is measured separately and checked on successful exit.
Microsoft documents the distinction in
[JOBOBJECT_EXTENDED_LIMIT_INFORMATION](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information).
Memory-exhaustion enforcement itself remains NOT TESTED.

Only SystemRoot/WINDIR/PATH are inherited; no test/database/provider credentials
are supplied. There is no HTTP/ORM/DB dependency or network call in the generated
rule artifact. Node filesystem permission is limited to its trusted artifact plus
stdin/stdout. **No OS network-denial boundary has been established on Windows**;
Node's permission model is not a malicious-code sandbox or a network firewall.
See [Node 22.15 permissions](https://nodejs.org/download/release/v22.15.0/docs/api/permissions.html).
Thus this prototype does not satisfy the complete isolated-executor acceptance.
Non-Windows execution fails closed with `ISOLATION_UNAVAILABLE`; no unverified
Docker/other-platform fallback is enabled. Trusted build/source/artifact integrity
is assumed; the adjacent local provenance file is not a signature or deployment
attestation. No production executor is authorized.

## Semantic evidence and preservation

The final ESM artifact passed **71 new cases in 30.45 s**, repeated after the
platform guard with **71 passed in 16.48 s**: all 70 immutable
profiles (29 initial + six survivor selections, each in forward/reverse order)
and rejection of input above 8 MiB before process launch. These compare the
entire discovery and assessment canonical SHA-256 values against existing
immutable expectations, including all observation/support/duplicate/conflict,
context, explanation, rationale, priority, confidence and seven unknown fields.
No expected results are regenerated. All seven unknown claims remain unknown /
insufficient. **No semantic hash mismatches were observed for these profiles.**
The initial CommonJS artifact also passed 71 cases in 24.69 s; frozen lint caught
its require-style import, which was corrected to ESM without weakening lint.
Initial push CI at `bd0fe4a73ddffd8ca198df387ee1b0716a79a9c5` exposed an
additional Linux mypy error on the Windows-only `ctypes.WinDLL` symbol before
regression execution. An explicit non-Windows fail-closed guard was added to the
Windows helper; no assertions, baseline workflow or resource limits were relaxed.
Local `mypy --platform linux` then passed all 53 configured source files.

Initial-head Windows push CI also executed all four constructed benchmarks
successfully on its faster runner (run
[45773354099](https://github.com/ankit8github/FootPrint/actions/runs/45773354099),
job 139751018311; 71 profile/input tests passed in 8.94 s):

| Fixture | Child seconds | Peak RSS KiB | Input bytes | Output bytes |
| --- | ---: | ---: | ---: | ---: |
| Primary account | 0.547 | 69,124 | 3,359,465 | 4,882,083 |
| Distinct commercial | 2.610 | 79,232 | 4,289,466 | 5,012,285 |
| Unresolved-only | 0.578 | 80,292 | 3,429,465 | 24,059,629 |
| Duplicates | 0.141 | 64,108 | 3,609,456 | 4,702,302 |

These measured platform differences are retained alongside the local failures.
They do not establish a portable five-second capacity guarantee or authorize
resuming the stopped implementation. Final-head CI receipts remain separate.

Local environment: Windows 10 build 26200 (platform-reported), Python 3.11,
Node 22.15.0, TypeScript 5.9.3, uv 0.9.29, pinned frontend packages and native
PostgreSQL 17.5 on loopback port 55443. Docker CLI was unavailable locally.

| Executed local check | Actual result |
| --- | --- |
| Existing backend | 1,061 passed in 373.54 s (runner 376.86 s) |
| Existing frontend | 284 passed; runner 23.14 s |
| Chromium smoke | nine passed in 37.4 s (runner 41.78 s) |
| Production privacy/rollback preservation | seven scenarios PASS; runner 41.03 s |
| Existing tenant DB | 434 before and 434 after re-upgrade; see below |
| New profile/input tests | 71 passed in 30.45 s; final guard repetition 71 in 16.48 s |
| Frozen Ruff lint/format, strict mypy | PASS; explicit `mypy rule_tests` PASS |
| Frozen ESLint, TypeScript, client build | PASS after new wrapper ESM correction |
| OpenAPI/Phase 2/minimized schema checks, client contracts | PASS |
| Corpus validation and immutable admission generator/tsconfig | PASS |
| pip-audit / npm audit at low threshold | no known vulnerabilities / zero vulnerabilities |
| All-base preservation | all 270 blobs unchanged, plus 193 historical / 252 prior baseline |
| Proposed executor budgets | FAIL / STOP, repeated on final artifact |

Seven preservation successes explicitly retain the old performance rollback;
they do **not** close the FAILED proposed frontend performance budgets. Local
machine-readable command/timing/output receipts are in `backend.json`,
`frontend.json`, `shared-profiles.log`, `database.log`, and the two benchmark
receipts under `.local/phase6c03-validation`. Existing Phase 6C-02 evidence is
untouched. The original scaffold database roundtrip was not rerun locally
(Docker unavailable); its unchanged CI step remains a separate check.

All **270** base blobs were verified unchanged, in addition to the original
193 historical and 252 Phase 6C-02 base files. This includes every migration,
role/RLS/context helper, ledger definition/test, Phase 6C-01 canonical batch,
registry/catalog/source gate, generator, corpus, oracle, application source,
lockfile, old CI workflow, engine version and 5000-ms frontend deadline.
ADR-015 through ADR-022 stay PROPOSED. No application module imports this
experiment. No existing test was weakened or removed.

Local tenant evidence: **434 passed in 45.94 s**, then **434 passed in 57.37 s**
after guarded downgrade/re-upgrade. The existing runner reported restricted-role
SQL, upgrade/downgrade/re-upgrade and retained ledger receipts. It created a new
fictional disposable cluster, used independent ephemeral credentials and stopped
that cluster. Existing evidence and other clusters were not deleted. This is
synthetic migration/receipt preservation, not durable production deletion/restore.

## Adapter/schema assessment and NOT TESTED matrix

The durable-ID-compatible adapter was **not implemented**, because the resource
stop occurred first. No owner/collection/generation mapping or durable output is
published. In the inspected schema, `finding_evidence` permits
primary/corroborating/context, while the engine also has a duplicate role.
The typed equivalence groups can retain duplicate membership; a future adapter
must prove a lossless reconstruction and must never relabel duplicate support as
independent corroboration. No schema incompatibility was silently repaired and
no complete projection compatibility is claimed.

**NOT TESTED in the new boundary after the stop:**

- Durable-ID bijection/completeness, malformed or foreign owner/collection/
  generation IDs, wrong-domain/type links and mismatched durable support.
- Both new removal-order matrices for email/history duplicates; durable canonical
  promotion and per-copy contexts; contextual-source-only removal; support and
  action eligibility recomputation through a durable adapter. Existing survivor
  profile hashes and existing browser tests do not substitute for these cases.
- New adapter comparisons for coincident nonequivalent rows, same/different order
  conflicts, unpaid invoice, invalid history timestamps, unresolved-only and empty
  durable projections. Their existing approved profile outputs were compared,
  but no new durable adapter exists.
- Constructed unresolved/duplicate 10,000-row benchmarks **locally** after the
  first stop (both were subsequently measured in the Windows CI table above).
  Complete representative worst-case calibration, memory pressure/kill,
  cancellation/interruption, abnormal child exit, malicious/malformed output,
  exactly-at-output-cap and over-output-cap termination, descendant cleanup under
  hostile code, and Linux isolation/enforcement. Only oversized input rejection
  and the observed deadline/kill path were exercised in this new boundary.
- OS-level network-denial proof, raw sentinel scans of new DB/WAL/artifacts, and
  platform-independent process isolation. No credential probes, external attack
  simulations or real provider connectivity were performed.
- Durable fences, atomic DB generation publication, save/delete races, durable
  deletion/restore, consent, endpoint authorization and serving behavior: no such
  pathway exists here. These remain outside 6C-03 and cannot be inferred from
  in-memory child result handling or the preserved tenant tests.

## Threat mapping, gates and rollback

| Threat | Evidence | Remaining gate |
| --- | --- | --- |
| TM-07 resource exhaustion | Bounded fixture, five-second termination, no returned result; explicit STOP | Proposed budget failed; full failure matrix/isolation incomplete |
| TM-09 metadata/version confusion | Frozen catalog/model admission, exact source/version/output hashes | Durable scoped references/projection and sentinel evidence NOT TESTED |
| TM-10 excessive certainty | All 70 exact profile hashes; seven unknowns preserved | Synthetic agreement is not real-world accuracy or sender verification |
| TM-13 deletion/recomputation | Six existing survivor selections compared with full provenance | New deletion-order adapter, durable fence/transactions are NOT TESTED |

Production G-S3, P5-F01/P5-F02, qualified independent human security approval,
legal/provider/security, endpoint authorization, performance and durable lifecycle
gates remain **OPEN**. Prior 6C-02 repository-only merge authorization is consumed
and grants no merge here. No product-owner exception is inferred.

Rollback: leave this experiment disabled and unmerged, or remove only these new
offline files in a separately reviewed change. No database downgrade, data
restoration or deletion-journal removal is needed or authorized. Do not start
6C-04/05, activate saves, add public endpoints, ingest real data, deploy or enable
beta access. Reopening implementation needs a separate decision addressing this
stop result, not a silent budget increase.

## Reproduction and changed-file inventory

```powershell
# From repository root, after frozen dependencies are installed:
git -c safe.directory=I:/FootPrint rev-parse HEAD
node frontend/scripts/shared-rules/build.mjs
cd backend
uv run --frozen pytest -q rule_tests
uv run --frozen mypy rule_tests
uv run --frozen python -m scripts.check_phase6c03_preservation
uv run --frozen python -m scripts.benchmark_shared_rules # first failed limit stops
$env:FP6_TEST_PORT='55443' # choose an unused loopback port
uv run --frozen python -m scripts.run_tenant_database --postgres-bin 'C:/Program Files/PostgreSQL/17/bin'

# Frozen backend gates (from backend):
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy
uv run --frozen pytest -q
uv run --frozen python -m scripts.export_openapi --check
uv run --frozen python -m scripts.export_phase2 --check
uv run --frozen python -m scripts.validate_corpus
uv run --frozen python -m scripts.export_minimized --check
uv run --frozen pip-audit

# Frozen client gates (from frontend):
cd ..\frontend
node scripts/admission/generate.mjs
npx.cmd tsc -p scripts/admission/tsconfig.json
npm.cmd run contracts:check
npm.cmd run lint
npm.cmd run typecheck
npm.cmd test
npm.cmd run build
npm.cmd audit --audit-level=low
$env:PLAYWRIGHT_BROWSERS_PATH='I:/FootPrint/.cache/ms-playwright'
npm.cmd run test:smoke
npm.cmd run test:performance -- --baseline
```

The separate additive Windows CI workflow repeats pinned build, all-base
preservation, new profile tests and the unwaived budget benchmark on push and PR.
The original regression and tenant workflows are unchanged. A resource failure
must remain visible as a failed CI step. Exact-head CI receipts are reported in
the draft PR; this static document does not assume future CI success.

Additions only: `frontend/scripts/shared-rules/build.mjs`, `worker.mjs`;
`backend/experiments/shared_executor.py`;
`backend/rule_tests/test_shared_profiles.py`;
`backend/scripts/benchmark_shared_rules.py`, `check_phase6c03_preservation.py`;
`.github/workflows/phase6c03.yml`; this report, `PHASE6C03-PLAN.md` and
`PHASE6C03-BENCHMARK.json`.
Local logs/JSON/build artifacts remain ignored under
`.local/phase6c03-validation` / `.local/phase6c03-build`.
