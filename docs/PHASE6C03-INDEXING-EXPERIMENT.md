# Phase 6C-03 / C03-R01: isolated indexing experiment

Status: measured experimental candidates only; **C03-R01 remains OPEN**.
No production rule, contract, executor, version, limit, schema or application
behavior was changed. PR #13 must remain draft/open/unmerged. No durable adapter
was implemented. This is AI-assisted engineering evidence, not qualified
independent human security approval or production G-S3 completion.

Reviewed head: `233620a10abbb6f53b773b853bd41900c62b8b61`; main/base:
`2038c65554501b7f0a099976ea07b75606cb7ff7`. Local HEAD, local main, origin/main,
live remote refs, clean worktree and PR metadata matched before work. All six
reviewed-head push/PR workflow runs and GitGuardian succeeded; fresh candidate
head receipts are separately bound to this report in the PR description and final
delivery. A file cannot record its own Git commit hash.

Read: the previous plan, security report, investigation and numeric archive;
6C-03 acceptance; S6A-04/06/12 and TM-07/09/10/13. The earlier reports and every
one of the 285 existing tracked blobs remain protected. Historical statements
that optimization was then unauthorized are preserved as historical evidence.
The current authorization permits these separate experimental copies only.

## Exact changes and unchanged boundaries

`backend/experiments/indexing_validation.py` subclasses the original strict
minimized model, inheriting the exact fields, bounds and field validators. Its
reference validator is an isolated copy. Only the final repeated per-commercial
group observation scan is replaced with an ordered alias-to-observation list.
Each observation occurs once per alias, in original observation order. All
original membership, order, completeness, domain, feature and type checks remain.
Foreign-domain members remain visible to the unchanged domain rejection; they
are never filtered away or treated as shared identity. The lookup exists only
for one validation call and is discarded. An AST regression checks that restoring
that single lookup and removing its index construction yields the original
reference validator exactly, ignoring formatting and comments.

The ordinary synthetic registry deliberately rejects this subclass (422); no
admission boundary is replaced. Only explicit experiment callers use it.
Original `MinimizedBatch`, `execute`, `benchmark_only` and all callers are intact.

`frontend/scripts/shared-rules/indexing-transforms.mjs` defines four exact,
single-occurrence build-time substitutions in copied pinned declarations:

1. Inside each transaction relationship/domain group, create alias-to-ordered
   support lists instead of filtering the entire support array per alias. Sorted
   alias traversal is unchanged. A per-observation Set prevents a repeated alias
   from multiplying that observation, matching the original `includes` predicate.
2. Build batch-local nested source-ID/adapter and relationship-ID/primary-member
   maps. These replace existence predicates only, not any emitted support list.
   Separate keys avoid ambiguous concatenation; duplicate evidence rows are not
   removed from the graph or assessment inputs.
3. Replace the two validation membership searches with those exact lookups. All
   surrounding support uniqueness, source, domain, type, duplicate, issue,
   identity and version conditions remain in place.
4. Inside each already validated transaction relationship, collect cancelled
   aliases and test paid aliases against that Set. The paid-side alias regex,
   same-row dual-claim conflict and all classifications remain unchanged. No
   cancelled alias crosses a relationship or domain boundary.

The new builder verifies the existing manifest and all eight normalized source
pins, selects the same TypeScript declarations and uses the same locked toolchain.
It reads the original artifact and emits separate baseline/indexed workers,
reviewable `copy.ts` files, pure test modules and transformation provenance under
ignored `.local/phase6c03-indexing-build`. It does not write the original build
directory. The baseline pure prefix is byte-identical to the pinned prefix.
No second classifier, raw-file parser, new dependency or retained sensitive field
is introduced. Both workers use the unchanged measurement wrapper.

| Artifact | SHA-256 |
| --- | --- |
| Original worker, unchanged | `69fcc47c8b0890c488900b4afe875aa7ce19faa6e257a691ad371fd53edff064` |
| Baseline measurement worker, same as previous investigation | `9fdc2ee12c7cff77dbad60231dcb7d25fb10f65dbffb5679af2219a2e5c9ed4f` |
| Indexed measurement worker | `03e7cb8cb9923a42b517feded409ff5bb2cff390aabde070fd874024f2df021f` |
| Immutable registry, unchanged | `333c513165273846a4645c74ba604900266d88e10fb6eda1848e0195949b0699` |

The new measurement supervisor is a separate copy with explicit artifact/model
selection. It reuses the original Windows Job Object helper, permission flags,
minimal environment, bounded pipe readers, kill/wait path and fixed limits:
**5-second child wall, 256-MiB process committed memory, 8-MiB input, 32-MiB output**.
Only metrics and canonical hashes leave this experiment; no findings are exposed
to an application, database or serving route. The original executor is untouched.

## Semantic and rejection evidence

All **70 immutable profiles** matched their complete existing discovery and
assessment hashes: 29 initial scenarios and six survivor selections, each in
forward/reverse order. These comparisons include all support, duplicate members,
conflicts, limitations, rationale/explanation text and seven unknown claims.
Expected oracles were neither regenerated nor modified. All 32 distinct catalog
batches additionally have paired baseline/indexed complete-result, discovery and
explicit support hashes. Support hashing includes relationships,
relationship_evidence, duplicate_groups, conflicts and unresolved findings;
whole-result hashing additionally covers every other result field.

The new bounded tests compare rejection error type/location/message/input against
the original model, not just whether an exception happened. Exception context
objects and documentation URLs are excluded from error comparison; neither
changes a rejection condition. Tests cover malformed versions/extra truth fields,
source/row identity, budgets and completeness, adapter mismatch, duplicate rows,
missing/repeated/foreign commercial members, alias traversal, feature/alias
duplicates, context eligibility/completeness and timestamps. Additional ordered
membership tests check multi-member acceptance and rejection of reversed members
and foreign-domain membership. The AST check protects every other validator rule.

The **44 pure-rule differential cases** compare full objects with strict deep
equality, including array multiplicity and order. They cover same/different-domain
commercial conflicts, reverse support order, different aliases, unpaid invoices,
both claims in one row, repeated aliases, invalid aliases, five-digit aliases,
duplicate copies in both orders, identical-looking distinct evidence, empty,
unresolved, invalid history time, context present/removed, 21 invalid-support
conditions, repeated source/primary edges, unrelated edges and three exact
`INVALID_EVIDENCE` duplicate failures. Accepted/rejected rule outcomes are asserted
explicitly. All seven assessment claims remain unknown/insufficient.

Two initial new test harness errors were corrected without altering assertions:
Node interpreted a comma-joined filesystem permission as one path, so the harness
now supplies three exact permitted files as separate flags; destructive graph
mutations initially shared fixture objects, so each mutation now starts from a
deep clone. The initial run had 103 successful pytest cases and one harness
failure; the corrected 44-case pure-rule invocation passed. These were fixture/
launch errors, not observed baseline/indexed semantic mismatches. The additional
AST test initially exposed a strict typing mismatch when inspecting a Pydantic
decorator proxy; inspecting its class source preserves the same AST assertion
and satisfies mypy. An ad hoc root-directory mypy invocation lacked the backend
import path; the documented configured backend invocation is used for receipts.

## Performance methodology and representativeness

Full numeric evidence is in `PHASE6C03-INDEXING-MEASUREMENTS.json`, copied from
`.local/phase6c03-indexing-0b574487f6d545229c5669bee134f116/measurements.json`.
The fixed matrix has **120 child runs: 119 PASS and one unchanged-baseline
DEADLINE**. It comprises 64 catalog runs (32 paired batches), 48 size-matrix runs
(four families, 20/1000/4000 rows, two repetitions, both variants), and eight
10,000-row runs. Pair order alternates in the repeated size matrix. All successful
paired complete-result/discovery/support hashes match. Indexed full-size cases
run before the known failing baseline. Its final failure terminates the script
nonzero; no further performance workload was run locally afterward. No new
indexed resource-bound failure was observed, and no limit was changed.

Catalog scope remains 32 exact whole-envelope batches, at most three sources,
ten rows, four observations and one alias. The 20/1000/4000/10000-row constructions
are existing model-level stress fixtures, **not new admitted catalog inputs**.
In particular 20 email sources with 500 rows per source cannot come from the
current one-row-per-email adapter; history cannot supply commercial claims.
Existing whole-envelope denial evidence is preserved. No fixture was enrolled,
and failed broad capacity evidence was not relabeled a catalog success.

Machine: Windows 11 Home Single Language build 26200, i5-10210U @ 1.60 GHz,
four cores/eight logical processors; CIM maximum clock 2112 MHz; 8,168,948 KiB
usable RAM, 900,824 KiB free at preflight. Python 3.11.9, Node 22.15.0,
TypeScript 5.9.3, tldts 7.5.5, frozen dependencies. No concurrent regression
workloads were started during this matrix. Power, thermals, paging, unrelated
host load and scheduling were not controlled. Small samples are not percentiles.

Timing definitions follow the previous investigation: parent validation/input
serialization precede the child budget; child wall includes launch and timeout
termination; supervisor wall includes result collection/decoding/hashing; total
case includes parent validation/serialization. Peak RSS is separate from the
enforced committed-memory cap, sampled through the final write marker. A killed
child has only the last-phase RSS lower bound and no full output/hash measurement.
Phase CPU, startup, parsing, preparation, output serialization/write, input/output
bytes and parent overhead are all retained in the JSON; missing values are null,
never substituted with zero. Observed zero stdout on the killed baseline is
distinct from its unknown full-output size.

### Paired 20/1000/4000-row means

Times are seconds; two samples per variant/family/size. Child speedup is baseline
mean divided by indexed mean; values below one mean slower indexed measurements.

| Rows | Family | Baseline validation | Indexed validation | Baseline child | Indexed child | Child speedup |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 20 | account | .00136 | .00134 | .1683 | .1858 | .91x |
| 20 | commercial | .00169 | .00195 | .1221 | .1397 | .87x |
| 20 | unresolved | .00148 | .00101 | .1724 | .1121 | 1.54x |
| 20 | duplicate | .00079 | .00076 | .0838 | .0900 | .93x |
| 1000 | account | .01934 | .01975 | .1174 | .1030 | 1.14x |
| 1000 | commercial | .18378 | .04170 | .1625 | .1346 | 1.21x |
| 1000 | unresolved | .02051 | .02363 | .1134 | .1507 | .75x |
| 1000 | duplicate | .02543 | .03018 | .1025 | .0995 | 1.03x |
| 4000 | account | .10146 | .11329 | .4179 | .1473 | 2.84x |
| 4000 | commercial | 2.82287 | .13345 | .9670 | .1822 | 5.31x |
| 4000 | unresolved | .10712 | .08232 | .2012 | .2055 | .98x |
| 4000 | duplicate | .22324 | .11791 | .1250 | .1589 | .79x |

At 4000 commercial rows, mean linking fell from **350.116 to 13.095 ms** and
assessment from **498.467 to 11.174 ms**; validation improved **21.15x**.
At 4000 account rows, assessment fell from **255.950 to 11.167 ms**. At 1000
commercial rows, linking was 28.316/7.181 ms and assessment 40.184/6.785 ms.
These phase measurements support the repeated-scan diagnosis while also showing
that startup/noise and unchanged serialization dominate smaller cases. The
candidate does not uniformly improve every workload.

Catalog mean child times were .3083/.2888 s (baseline/indexed), maxima
1.2061/.5537 s, peak RSS 34,420/34,460 KiB. Only one sample per catalog variant;
the maximum startup fluctuation is not a reliable throughput improvement claim.

### Full 10,000-row measurements

Each is a single local run. RSS is KiB; child CPU may include background threads.

| Family / variant | Validation s | Link ms | Assess ms | Child wall s | CPU s | Supervisor s | Peak RSS | Input bytes | Full output bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| account baseline | .8899 | 48.448 | 3780.051 | 4.3981 | 3.2344 | 5.1441 | 75972 | 3359465 | 4882083 |
| account indexed | .4972 | 36.465 | 34.256 | .3119 | .3125 | .6409 | 77128 | 3359465 | 4882083 |
| unresolved baseline | .8382 | 21.593 | 64.255 | .7637 | .7188 | 2.5184 | 124512 | 3429465 | 24059629 |
| unresolved indexed | .3658 | 27.712 | 116.037 | .9927 | .7188 | 3.2940 | 124248 | 3429465 | 24059629 |
| duplicate baseline | .6824 | 8.657 | 4.804 | .2785 | .2813 | .7874 | 71168 | 3609456 | 4702302 |
| duplicate indexed | .6768 | 13.569 | 9.029 | .2960 | .2188 | .7751 | 71568 | 3609456 | 4702302 |
| commercial baseline | 53.9056 | NOT COMPLETED | NOT REACHED | 5.0521, DEADLINE | 3.1094 | 5.1515 | >=64856, last marker only | 4289466 | NOT MEASURED |
| commercial indexed | .8310 | 54.505 | 69.203 | .4408 | .6094 | 1.1610 | 88696 | 4289466 | 5012285 |

Account child wall improved **14.10x**; commercial validation improved **64.87x**.
A completed 10,000-commercial child speedup cannot be calculated locally: baseline
was killed inside linking and published no result. Its local full-size semantic
comparison is therefore **NOT TESTED**; do not extrapolate smaller-size parity
into a measured full-size baseline result. The indexed case consumed 8.8% of the
unchanged child deadline on this run. Fresh CI may provide paired completion on
its different host; it cannot erase any local baseline failures.

Indexed total case times (including validation/serialization/verification) were
1.4361 s account, 3.9038 s unresolved, 1.7287 s duplicates and 2.5474 s commercial.
The five-second cutoff is a child limit, not an established end-to-end service
SLA. Unresolved output is about 24 MB; parent decode plus hashes took 2.3009 s,
showing an unchanged non-rule cost. Child serialization/output and memory remain
material even when lookup cost falls. Extra indexes also consume memory; the
commercial indexed peak RSS was 88,696 KiB, not a zero-cost optimization.

The previous two original local failures, third instrumented failure, earlier
Windows CI successes and their receipts remain unchanged. This fourth baseline
failure had lower child CPU (3.109 s) than the prior 4.953 s and .429 s to its
first marker; wall/CPU divergence is observable scheduling noise, not proof of
its cause. CPU model/power/load of earlier CI was not captured. No conclusion
depends solely on a faster CI runner.

## Validation receipts and preservation

Local receipts are preserved under `.local/phase6c03-indexing-validation`.
Two complete unchanged backend runs each had **1060 passed / one failed**:

- First run, 385.27 s: `test_ownership_security.py::test_cursors_counts_filters_and_b_only_metadata_changes`.
- One full retry, 556.89 s: `test_minimized_admission.py::test_every_complete_registered_envelope_is_validation_only[a-d30911944817063ed7d8749559a46bc403202cda320f1a4b0f603da6b5ca6bb1]`.

Both failed the existing `tests/session_test_support.py:69` assertion that the
fictional login callback redirects to `/_spike/complete`. The first case passed
unchanged in isolation (one passed, 2.17 s). The second case was not separately
rerun. The cause is **NOT ESTABLISHED**; neither a security vulnerability nor a
link to indexing is asserted. These are fail-closed setup failures in protected
code, not a demonstrated pure-rule/support mismatch. No protected code or
assertion was changed. No third full retry was attempted to obtain a green run.
**The full backend suite is not green locally**, regardless of later CI outcomes.
This is an additional adoption/review limitation, not evidence that the normal
regression gate is satisfied. Both complete outputs are retained in `backend.json`
and `backend-continuation.json`; the isolated result is in
`backend-isolated-retry.log`. The remaining independent gates have separate
receipts, preserving every failed run.

The existing native PostgreSQL 17.5 runner passed **434 in 90.85 s**, then
**434 in 100.01 s** after guarded downgrade/re-upgrade, confirming restricted-role
SQL and retained ledger receipts. It used a new recognized fictional disposable
cluster on loopback port 55447 and stopped that cluster; existing clusters/evidence
were not erased. Original migrations, role/RLS boundaries, ledger definitions and
all existing tests remain unchanged. This is synthetic roundtrip evidence, not
production deletion/restore validation.

| Final local check | Actual outcome |
| --- | --- |
| New indexing + original immutable suites | **179 passed in 29.40 s**: 108 new pytest cases (including 44 inner TS cases), plus original 71 |
| Existing backend, first full run / one full retry | **1060 passed / one failed**, twice; not green, as detailed above |
| Existing frontend | **284 passed**, Vitest 14.52 s; command 15.904 s |
| Chromium smoke | **nine passed in 25.8 s** |
| Privacy/rollback preservation | **seven scenarios PASS**; original proposed performance budgets remain **FAILED** |
| Tenant database | **434 passed**, then **434 passed** after re-upgrade; ledger retained |
| Frozen full Ruff lint/format | PASS; 66 files formatted; final repetition PASS |
| Strict configured Windows/Linux mypy | PASS, 58 configured source files each; explicit rule/indexing test typing PASS |
| Frozen ESLint, frontend TypeScript, build | PASS; generated experimental copy also passes strict `tsc` |
| OpenAPI/Phase 2/minimized exports and client contracts | PASS |
| Corpus, immutable admission generator and its `tsconfig` | PASS |
| pip-audit / npm audit at low threshold | no known vulnerabilities / zero vulnerabilities |
| Preservation | all **285** pre-experiment blobs unchanged; original **270 / 252 / 193** checks PASS |
| Local paired resource matrix | **119 PASS / one original-baseline DEADLINE**, no indexed resource failure |

Completed independent backend gates are in `backend-remaining.json`; frontend
receipts are in `frontend-remaining.json` and `frontend-final.json`. A Windows
CP1252 console-encoding error interrupted the new local receipt runner after its
successful build had already been saved; only unexecuted commands resumed with
UTF-8 stdout. No product/test assertion or successful receipt was changed.
`database.log`, `final-ruff.log` and the numeric archive preserve additional
evidence. No third complete backend rerun was hidden behind these continuations.
The original scaffold Docker roundtrip was **NOT TESTED locally** (Docker CLI
unavailable); its unchanged CI check is separate evidence. Fresh exact-head CI
and GitGuardian outcomes are recorded in the PR description/final delivery,
including any failures; historical green receipts cannot establish a later head.

## Recommendation and gates

Indexing is sufficient for **these four measured local synthetic full-size
candidates** under the existing child limits. It addresses the demonstrated
commercial validation/linking and account/commercial assessment scan bottlenecks.
The non-green local backend regression is an additional unresolved gate. It is
not sufficient evidence to close C03-R01, activate production code, start
the durable adapter or claim a portable capacity guarantee. Small/unresolved/
duplicate cases can be slower. Broad workload and end-to-end resource definitions
still require an explicit decision and further bounded evidence.

For separate product-owner authorization, the smallest protected-source proposal
is exactly the demonstrated lookup substitutions in:

- `backend/experiments/minimized_contract.py`, final commercial membership scan
  in `MinimizedBatch.references` (around lines 240-241).
- `frontend/src/features/discovery/discovery.ts`, transaction alias support scan
  (around lines 57-65).
- `frontend/src/features/assessments/assessments.ts`, source/primary-edge membership
  (around lines 46-47) and cancelled-alias search (around lines 71-72), plus local
  index construction inside `assessDiscovery`.

None of those protected edits is applied. Before any adoption, separately review
version/provenance strategy: current source hashes/version pins cannot silently
be changed, and this experiment does not authorize repinning. Preserve exact
result/support parity and rejection conditions, then repeat bounded tests on
specified reference hosts. Do not raise limits, truncate support or silently
narrow accepted model capacity. The durable projection remains a separate task.

NOT TESTED: completed local full-size commercial baseline output parity; exhaustive
malformed graph objects outside the validated typed JSON boundary; sustained-load
percentiles, cold-cache/thermal/paging attribution, maximum combinations of
alias/context/domain density beyond these existing fixtures, parent peak memory or parent
memory enforcement; Windows OS network-denial proof, memory exhaustion,
cancellation, hostile child/descendant behavior, malformed/oversized child output;
Linux executor isolation; new adapter-realizable maximum fixtures; durable-ID
mapping, new deletion-order adapter matrices, atomic persistence publication,
durable deletion/restore, endpoint authorization, real identity/provider behavior.
Original security-report NOT TESTED limitations remain applicable. No new claim
of absent capabilities is inferred merely from the successful functional tests.

TM-07: local candidate budget evidence plus preserved baseline timeout; isolation
and portability remain open. TM-09: pinned code and complete output/support hashes;
durable scoped provenance is unimplemented. TM-10: exact rule/unknown parity, no
new certainty or browser-derived authority. TM-13: existing immutable survivor
selections preserved; durable deletion/recomputation remains unimplemented.
Production G-S3, P5-F01/P5-F02, independent human review, legal/provider/security
and durable lifecycle gates remain **OPEN**. ADR-015 through ADR-022 stay PROPOSED.

Rollback is leaving these disabled new files unmerged, or removing only the new
experiment through a separately reviewed change. No database migration,
deletion-journal removal or user-data rollback is required or authorized. No
HTTP route, production auth, raw user data, save/delete workflow, integration,
deployment, beta or Phase 6C-04/05 capability was added.

## Reproduction and additive inventory

```powershell
# Fresh clone only: install frozen dependencies and build original pinned artifact.
uv sync --project backend --frozen
npm.cmd ci --prefix frontend
node frontend/scripts/shared-rules/build.mjs
# Existing working copy: preserve old artifact/evidence; build only new copies.
node frontend/scripts/shared-rules/build-indexing.mjs
cd backend
uv run --frozen pytest -q -x -s indexing_tests rule_tests
uv run --frozen python -m scripts.benchmark_indexing
# Stops nonzero at first failure, including the known local baseline deadline.
uv run --frozen python -m scripts.check_indexing_preservation
uv run --frozen python -m scripts.check_phase6c03_preservation
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy
uv run --frozen mypy --platform linux
uv run --frozen mypy rule_tests indexing_tests
# Frozen full backend run: local synthetic login setup failures are documented above.
uv run --frozen pytest -q
uv run --frozen python -m scripts.export_openapi --check
uv run --frozen python -m scripts.export_phase2 --check
uv run --frozen python -m scripts.export_minimized --check
uv run --frozen python -m scripts.validate_corpus
uv run --frozen pip-audit --progress-spinner off
# Fresh recognized disposable database only; choose an unused loopback port.
$env:FP6_TEST_PORT='55447'
uv run --frozen python -m scripts.run_tenant_database --postgres-bin 'C:/Program Files/PostgreSQL/17/bin'
cd ../frontend
npx.cmd eslint scripts/shared-rules/build-indexing.mjs scripts/shared-rules/indexing-transforms.mjs scripts/shared-rules/test-indexing.mjs
npx.cmd tsc --noEmit --strict --skipLibCheck --target es2022 --module esnext --moduleResolution bundler ../.local/phase6c03-indexing-build/indexed/copy.ts
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

Additions only: this report and `PHASE6C03-INDEXING-MEASUREMENTS.json`;
`backend/experiments/indexing_validation.py`;
`backend/scripts/measure_indexing.py`, `benchmark_indexing.py`,
`check_indexing_preservation.py`; `backend/indexing_tests/test_indexing.py`;
`frontend/scripts/shared-rules/build-indexing.mjs`, `indexing-transforms.mjs`,
`test-indexing.mjs`; `.github/workflows/phase6c03-indexing.yml`.
The additive workflow records bounded paired metrics on push/PR. All original
workflows, application/DB tests, production engines, corpus, registry, schema,
ledger, locks, original executor and reports remain unchanged. CI receipts and
GitGuardian must be checked against the final pushed head, not a prior commit.
