# Phase 6C-03 completion attempt — STOPPED at durable package provenance

Prepared 2026-11-26 for [PR #13](https://github.com/ankit8github/FootPrint/pull/13).

**Phase 6C-03 is INCOMPLETE. C03-R01 remains OPEN. New design blocker
C03-COMP-01 is OPEN. Do not merge. Keep the PR draft/open/unmerged.**

Implementation was authorized for this milestone, including an additive,
backwards-compatible indexing revision. The implementation stopped under the
user's explicit condition for unrepresentable durable provenance. No schema
change, historical repin, oracle change, production activation or exception was
applied. This is AI-assisted evidence, not independent human security review.

## Exact state and stage disposition

Preflight branch: `experiment/phase6c03-shared-rules`. Local and live remote head:
`580fddd8f081182a21bde60eb24d26005115e47f`. Base, local main, origin/main and
live remote main: `2038c65554501b7f0a099976ea07b75606cb7ff7`.
PR metadata matched and was draft/open/unmerged. The sole pre-existing untracked
file was [the adoption review](PHASE6C03-ADOPTION-REVIEW.md), read and preserved
before edits, SHA-256
`7fc170d40d178c9e0b13f553b3a3e4838ad48fc57f3410f372018c7e32c4ff30`.
It is now retained in Git without rewriting its historical proposal wording.

Implementation/evidence commit: `2b0f791bca87cddf7bb93b3a87403ffbaf1d7304`.
The subsequent report commit corrects only this report's numeric archive and
adds this document. The final report-bearing SHA and exact-head CI receipts are
bound in PR metadata, the final delivery and local `final-state.json`; a committed
file cannot contain its own Git commit hash. No merge is authorized or performed.

| Stage | Actual disposition |
| --- | --- |
| Preflight | Completed: expected local/live remote refs; prior untracked evidence preserved; actual combined parity rerun passed. Historical failure receipts retained. |
| A — indexing adoption | **Candidate implemented and functionally verified**, using explicit implementation revisions. Historical worker reproduces exactly; 70 old/new profile comparisons, negative/version checks and four indexed model stress fixtures pass. This is not final adoption acceptance. |
| B — durable provenance | **STOPPED / incomplete** at C03-COMP-01. A partial catalog-seed UUID codec exists and has 44 tests. There is no complete result-to-typed-storage adapter or lossless durable implementation binding. |
| C — survivor recomputation | **NOT COMPLETED / NOT TESTED through a durable adapter.** An unaccepted local draft was preserved outside runtime source; its survivor/publication code was removed from the repository candidate after the stop. Historical survivor oracle comparisons remain valid separate evidence. |
| D — executor failure safety | **PARTIAL.** New trusted-child boundary and successful bounded executions exist; the required deadline/memory/cancellation/exit/malformed/truncated/output-cap/hostile-descendant matrix was not executed for this new boundary. No completion claim. |
| E — complete validation | **INCOMPLETE.** Scoped local checks and a new stopped-evidence CI workflow exist. Full local baseline/browser/DB/audit validation was not resumed after the stop. Final-head CI outcomes are reported separately, not presumed here. |

## C03-COMP-01: lossless generation-to-implementation binding is missing

The selected strategy intentionally preserves existing semantic versions and adds
an exact implementation revision (`historical-v1` versus `indexed-r1`) with source,
transform, toolchain and worker hashes. For durable execution provenance, that
selection must remain attributable to owner/collection/generation, including an
empty generation. Semantic output equality cannot identify which bytes ran.

Inspection of the existing immutable
`backend/tenant_migrations/versions/6c02_0001.sql` shows:

- `collections` lines 119-125 fixes the semantic/explanation versions to their
  original v1 values. It has no implementation/package/artifact identity field.
- `generations` lines 129-135 has only `owner_id`, `collection_id`, `generation`
  and their keys. There is no versioned implementation binding on that root.
- Finding, assessment, directory, action, outbox, idempotency and deletion-journal
  structures provide no appropriately scoped execution-artifact metadata target.
  The idempotency HMAC, directory version, deletion journal and UUID identifiers
  must not be repurposed to conceal unrelated provenance.

The test `completion_tests/test_storage_compatibility.py` verifies the actual SQL
definitions and constructs the counterexample: two different worker hashes with
the same semantic versions project to the same available collection/generation
rows. Empty generations have no finding UUID to join for missing metadata.
This is **logical information loss for this implementation-lineage requirement**,
not a runtime PostgreSQL test, ownership breach or proof that every possible
semantic projection is unrepresentable. No database writes were attempted.

An in-memory `implementation` property or adjacent build JSON does not by itself
make that binding durable and scoped. The stopped decision is recorded in
`backend/experiments/rule_packages/storage-compatibility.json`; durable projection
is explicitly disabled. The current milestone does not authorize the needed
schema change, nor silently replacing v1 semantic fields with new meanings.

Owner review must choose a separately authorized typed generation-to-package
binding migration, or review an alternative explicit version/provenance design
and prove its lossless mapping without overwriting historical pins or widening
the protected contract. If build/release-level attestation rather than a
generation-level binding is proposed as sufficient, that is a decision requiring
review and an explicit proof for empty and historical generations. It was not
silently assumed here. No migration or alternative was applied.

## Version inventory and compatibility

All existing rule sources, validators, registry/schema, oracles, limits and
experimental copies remain unchanged. The original eight normalized source pins
are reproduced verbatim in the new additive implementation manifest. Existing
`MinimizedBatch`, exact-class/retained-state admission and `SyntheticRegistry`
remain authoritative for ordinary catalog admission.

`frontend/scripts/shared-rules/build-packages.mjs` independently extracts the
original pinned TypeScript declarations and uses the four existing exact
indexing substitutions, creating new ignored package paths. It never rewrites
the historical builds or original registry. Its historical output is the original
worker byte for byte. The indexed package retains original discovery/assessment
result objects and separately emits eligible synthetic action IDs using the
exact pinned `ACTION_DIRECTORY` / `actionsFor` declarations. No Python business
classifier is introduced.

| Identity | SHA-256 / mapping |
| --- | --- |
| Original semantic registry, unchanged | `333c513165273846a4645c74ba604900266d88e10fb6eda1848e0195949b0699` |
| New additive implementation manifest | `7485ac86c2cd9502e1414d68df7a930ae531b209706d44b8161a736ec7e24055` |
| `historical-v1` worker | `69fcc47c8b0890c488900b4afe875aa7ce19faa6e257a691ad371fd53edff064` |
| Historical pure prefix | `73dbb73013b2a8ff0c364312adb6820b02a6de9ccb0d60ffd7adc9bc8cd58bb5` |
| `indexed-r1` worker, new wrapper/action-ID envelope | `f4170b61857e2ae673332e4d57cd01cab5214ede7f4c3b3abef390221258670a` |
| Indexed pure prefix, identical to measured experimental candidate | `5e980c1c1856226ef6b2ce35b9b4eb651d5860139ba6041a4ffe76ffb262d1e7` |
| Previous indexed measurement worker, unchanged and distinct | `03e7cb8cb9923a42b517feded409ff5bb2cff390aabde070fd874024f2df021f` |

Semantic versions remain `minimized-evidence-v1`, `phase2-normalized-v1`,
`email_features_v1`, `relationship_fusion_v1`, `email_context_v1` and
`sensitivity_rules_v1`. `historical-v1` uses `MinimizedBatch`; `indexed-r1` uses
the unchanged, source-pinned `IndexedBatch`. Its AST and rejection parity remain
covered. The new manifest names both implementations explicitly, records the
original source head and equivalence mapping, and pins Node 22.15.0, TypeScript
5.9.3, tldts 7.5.5, PSL, normalized lock and builder/wrapper/source identities.
LF attributes apply only inside the new package directory. The builder writes
a candidate manifest under `.local`; it does not automatically repin a tracked
manifest. Unsupported revisions/hash mismatches reject without fallback.

The four optimized paths remain ordered commercial alias membership in Python;
domain/relationship-local transaction alias support in discovery; exact nested
source/adapter and relationship/primary-member existence maps in assessment;
and relationship-local cancelled-alias membership with the original paid-side
regex. Every prior check/rejection and ordered emitted evidence remains intact.
Sets replace existence predicates, not support arrays or duplicate membership.
All seven unknown claims remain unknown/insufficient.

## Partial provenance inventory and deferred survivor semantics

`provenance_adapter.py` now contains only frozen scoped seed/binding structures,
catalog seeding and complete seed-bijection validation. UUIDs are generated
independently of minimized values/hashes. Exact original whole-envelope catalog
admission is required; source, observation/excluded-row, duplicate-group and
commercial-group bindings must be complete, unique, ordered, correctly typed
and match the independently supplied owner/collection/generation. The full
minimized input retains every duplicate member and its own context. No value
equality is used as authority for identity or deduplication.

The 44 seed tests are not full adapter acceptance. Result/root/evidence/assessment
mapping, domain/type/support mismatch negatives, generation publication, lossless
typed SQL projection, removal-order matrices, primary promotion, context-only
removal, action reset/eligibility and stale/partial generation fencing through a
durable adapter remain NOT IMPLEMENTED or NOT TESTED. The removed draft remains
ignored as `unaccepted-adapter-draft.py` in this task's receipt directory, not
imported by application/tests/CI. It grants no survivor or durability claim.

Duplicate support must later be recoverable through typed equivalence groups;
the SQL finding-evidence roles remain primary/corroborating/context. Duplicates
were not relabeled corroboration and no schema role was widened. Existing 29
initial/six survivor immutable oracles, both source orders, remain unchanged;
successful historical-profile comparisons do not establish the deferred adapter
or transactional deletion behavior.

## Actual local results

The previously reported native page error was checked by executing the actual
combined path, not by accepting the reported local fix:
`uv run --frozen pytest -q -x -s indexing_tests rule_tests` — **179 passed in
32.42 s**. It includes the original 71 and experimental 108 cases, with 44 inner
TypeScript comparisons. The page error did not recur on this run. Its historical
cause and the mechanism of any local fix remain unestablished; no protected
test/interpreter/security source was modified to obtain this result.

| New check | Actual local result |
| --- | --- |
| Both implementation packages / all 70 profiles / complete discovery, assessment and support-order parity; 32 validation mutations; four unknown-version negatives; historical identity/admission | **107 passed in 41.03 s** before final formatting |
| SQL representation counterexample | **1 passed in 0.03 s**, establishing the documented STOP rather than schema compatibility |
| Final new suite (same 107 + schema proof + 44 seed checks) | **152 passed in 61.56 s**. Counted separately from the original 1061 backend baseline; not an additional 152 on top of the earlier 107/1 executions. |
| Frozen full Ruff / format | PASS, 72 files formatted |
| Configured Windows mypy / Linux mypy | PASS, 61 source files each; new tests separately PASS, three files |
| New JS builder/wrapper ESLint / existing frontend types | PASS |
| Original preservation scripts | PASS, all 285 pre-experiment blobs; 270/252/193 baseline/historical inventories |
| Additional preservation | PASS, all 296 expected-head blobs and all 370 snapshotted prior source/evidence files unchanged, including the adoption review |

Initial style/type checks of the new files failed on formatting and broad
exception typing; only the new files were corrected. Failed receipts remain,
separate from final verified checks. No assertion was weakened. No full local
backend baseline was rerun in this stopped milestone. The two historical runs
remain **1060 passed / one failed**, in different fictional login callback setups,
with cause **NOT ESTABLISHED**. Their complete `backend.json` and
`backend-continuation.json` and the prior isolated/triage receipts are unchanged.
The successful parity path and future CI success do not diagnose those logins.

### Measured indexed candidate capacity

Four fixed 10,000-row **constructed model-level** fixtures passed the proposed
indexed path under unchanged **5 s child wall / 256 MiB committed memory / 8 MiB
input / 32 MiB output**. These do not enroll new catalog workloads. Ordinary
catalog scope remains 32 whole envelopes / 70 profiles, at most three sources,
ten rows, four observations, one alias and 1,977 input bytes. The new profile
tests executed representative catalog inputs under both guarded packages.

| Model fixture | Child s | Parent pin/model validation s | Supervisor s | `_execute` total s | Full-interval child RSS KiB | Input / complete envelope output bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Account | .2275 | .3126 | .3280 | .7455 | 79,500 | 3,359,465 / 4,882,129 |
| Commercial | .3034 | .3208 | .4622 | 1.2171 | 90,620 | 4,289,466 / 5,012,331 |
| Unresolved | .5179 | .5508 | 1.4872 | 2.3795 | 129,452 | 3,429,465 / 24,089,650 |
| Duplicates | .1761 | .5830 | .3108 | 1.1970 | 74,340 | 3,609,456 / 4,702,348 |

Numeric evidence: [completion measurements](PHASE6C03-COMPLETION-MEASUREMENTS.json).
The command wrapper reused the probe's JSON filename for its command receipt;
all four numeric rows were recovered exactly from the retained complete stdout,
verified by log SHA-256
`7d273a49ae654db6e3021a97d0dccc5fe39dc6dc63caded4ba50014a89259e5a`.
No workload was rerun for this recovery. The original command receipt and log
remain intact; the archive documents the naming error rather than hiding it.

Local host: Windows 11 Home build 26200, i5-10210U, four cores/eight logical
processors, 8,168,948 KiB usable RAM. Free memory was 1,197,052 KiB at a later
inventory check, not a controlled stress-run baseline. These are single samples,
not percentiles; host power/load/paging/thermals were not controlled.

The new envelope separately includes action IDs, so its full byte counts differ
from the old measurement wrapper. Canonical rule result/discovery hashes retain
the old meanings. Validation includes package pin checking; supervisor time
includes child collection/JSON decode, and total includes input serialization
and echo-consistency verification. Benchmark canonical result hashing occurs
after that total timer. Parent memory enforcement and a complete service SLA are
not established. The five-second deadline is a child limit. RSS is measured
after serialization/write for the indexed wrapper and is distinct from the
kernel committed-memory cap; historical early-RSS measurements are not rewritten.

All previous local baseline deadlines remain failures in the original benchmark,
investigation and indexing archives. No new completed local 10,000-commercial
historical baseline output was measured here, so its local full-size parity is
still NOT TESTED. The new candidate's successes do not relabel old failures.

## Append-only final evidence supplement to the plan and security report

This section supplements [the original plan](PHASE6C03-PLAN.md) and
[security report](PHASE6C03-SECURITY-REPORT.md) without altering their protected
bytes or historical measurements. Their original 285-blob checks remain intact.

The new boundary selects only the two pinned packages, validates original input,
uses the existing Windows Job Object process-commit cap, bounds input/output and
diagnostics, inherits only SystemRoot/WINDIR/PATH, and closes the job before pipe
collection completes. It has no raw parser, database, provider credential, HTTP
route or application import. All activity is explicitly offline and synthetic.

These code paths and successful runs are **not** the required failure/isolation
proof. NOT TESTED at the new boundary: deadline/kill cleanup, memory-pressure
termination, cancellation, unexpected exit, malformed/truncated/duplicate-key
result, output-cap edges, hostile descendant cleanup and missing/foreign durable
result references. Node permissions are insufficient for malicious-code or
OS-level network isolation; Windows OS network denial is not demonstrated.
Non-Windows execution fails closed; Linux typing is not Linux isolation proof.

NOT RERUN LOCALLY after the stop: full original 1061 backend, 284 frontend,
nine Chromium, seven performance-preservation scenarios, 434 + 434 tenant DB
cases/guarded roundtrip, Docker scaffold roundtrip, full client build,
OpenAPI/contracts/corpus/registry generator and dependency audits. Existing
proposed frontend performance failures remain explicit historical evidence.
New exact-head CI is reported with its actual counts/platforms; it cannot close
the stopped adapter or diagnose the two historical local login failures.

Production G-S3, P5-F01/P5-F02, legal/provider/security, qualified independent
human review, durable deletion/restore and lifecycle gates remain OPEN.
ADR-015 through ADR-022 remain PROPOSED. No persistent user data, production
authentication, schema migration, save/delete worker, endpoint, integration,
deployment, beta, Phase 6C-04/05 or consumed 6C-02 exception was used.

## Reproduction, CI and changed-file inventory

The new workflow is explicitly named **stopped implementation revision evidence**.
It builds separate packages, runs the 152-case new suite, bounded measurements,
quality/preservation and verifies the STOP decision. Its green status means its
checks passed; it does not mean Phase 6C-03 completed. Existing workflows remain
unchanged. Push/PR outcomes, GitGuardian, runner counts and local-versus-CI
measurements are bound to the final pushed SHA in PR metadata/final delivery and
retained under `.local/phase6c03-completion-20261126`. No pending job is called PASS.

Reproducible commands, frozen dependencies already installed:

```powershell
node frontend/scripts/shared-rules/build-packages.mjs
cd backend
uv run --frozen pytest -q -x completion_tests
uv run --frozen python -m scripts.benchmark_rule_packages
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy
uv run --frozen mypy --platform linux
uv run --frozen mypy completion_tests
uv run --frozen python -m scripts.check_indexing_preservation
uv run --frozen python -m scripts.check_phase6c03_preservation
```

On a fresh clone, the original combined path additionally requires the original
and experiment builds (`build.mjs`, then `build-indexing.mjs`) before
`uv run --frozen pytest -q -x -s indexing_tests rule_tests`. Those historical
builders are unchanged. Do not overwrite an existing receipt/build merely to
reproduce history; use a fresh checkout or the new package output directory.

Additions only relative to the expected head:

- `.github/workflows/phase6c03-completion.yml`.
- `backend/experiments/versioned_executor.py`, `provenance_adapter.py`;
  `rule_packages/{.gitattributes,README.md,manifest.json,storage-compatibility.json}`.
- `backend/completion_tests/{test_packages.py,test_seed_refs.py,test_storage_compatibility.py}`.
- `backend/scripts/benchmark_rule_packages.py`.
- `frontend/scripts/shared-rules/{build-packages.mjs,package-worker.mjs}`.
- The preserved `docs/PHASE6C03-ADOPTION-REVIEW.md`, this report and
  `docs/PHASE6C03-COMPLETION-MEASUREMENTS.json`.

Every previous tracked file, original rule package/version/source pin, oracle,
schema/RLS/ledger, lock and workflow is unchanged. Rollback is leaving the new
disabled candidate unmerged; no stored user data or journal is rolled back.

**Recommendation:** review the Stage A candidate and C03-COMP-01 design decision.
Do not call this milestone complete, approve adoption, merge PR #13 or begin the
next phase. Resume only under a reviewed solution to the lossless durable
implementation binding and then finish Stages B-E with their actual acceptance
evidence. Automated tests and CI are not independent human approval.
