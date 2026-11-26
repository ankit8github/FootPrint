# Phase 6C-03 / C03-R01: login triage and indexing adoption proposal

Prepared 2026-11-26 for product-owner review of [PR #13](https://github.com/ankit8github/FootPrint/pull/13).

**PROPOSAL ONLY. Owner adoption decision: PENDING. C03-R01: OPEN. Local full
backend regression: UNRESOLVED. Keep PR draft, open and unmerged.**

Recommend retaining the disabled indexing experiment and considering a separately
authorized, immutable implementation-revision package containing only the lookup
substitutions below. Do not adopt protected source, repin the old registry, activate
execution, implement a durable adapter or merge under this task. Successful
targeted tests do not resolve the two historical full-suite login failures.

## Verified scope and Git state

Preflight local branch was `experiment/phase6c03-shared-rules`, HEAD
`580fddd8f081182a21bde60eb24d26005115e47f`. Local `main`, `origin/main` and
`git merge-base HEAD main` were all
`2038c65554501b7f0a099976ea07b75606cb7ff7`. The worktree was clean. GitHub PR
metadata independently matched that head/base and reported draft/open/unmerged.
No fetch, checkout, commit, push or PR mutation was performed.

The ordinary shell helper failed before launch (`setup refresh had errors`),
and the Node REPL also failed to start. Authorized local commands then ran through
the escalated execution helper as `debru`. Git required a command-local
`-c safe.directory=I:/FootPrint` because the repository owner is
`ANKIT/CodexSandboxOffline`; no global Git configuration was changed. This is a
local invocation difference, not an explanation for either old failure.

Read the original [plan](PHASE6C03-PLAN.md), [security report](PHASE6C03-SECURITY-REPORT.md),
[C03-R01 investigation](PHASE6C03-PERFORMANCE-INVESTIGATION.md),
[indexing experiment](PHASE6C03-INDEXING-EXPERIMENT.md), both numeric archives,
the existing login helpers and both complete failure receipts. Historical
approvals, reports and failures retain their original meaning. The prior
6C-01/02 repository exceptions do not authorize this adoption or merge.

Only this document is intended as a new tracked deliverable. New diagnostic
scripts/receipts live under ignored `.local/phase6c03-adoption-review/`.
No original source, assertion, registry, version, oracle, lock, CI workflow,
schema/RLS/ledger or resource limit was edited.

## Track A: local login failure findings

### What the two original logs establish

Both logs are in `.local/phase6c03-indexing-validation/` and both commands were
unchanged `uv run --frozen pytest -q`:

| Receipt | Exact failed case | Evidence |
| --- | --- | --- |
| `backend.json` | `tests/test_ownership_security.py::test_cursors_counts_filters_and_b_only_metadata_changes` | 1 failed / 1060 passed in 385.27 s. Setup for owners A/B succeeded; failure was the later third login through a new `tab` cookie jar on that same ownership fixture, before testing foreign-session cursor rejection. |
| `backend-continuation.json` | `tests/test_minimized_admission.py::test_every_complete_registered_envelope_is_validation_only[a-d30911944817063ed7d8749559a46bc403202cda320f1a4b0f603da6b5ca6bb1]` | 1 failed / 1060 passed in 556.89 s. Failed entering the admission harness, on its first `fictional-a` login, before any minimized-envelope submission. |

Both reach `tests/session_test_support.py:69` after `pending` and `authorize`
have passed the preauth (200), start (303) and fictional issuer (303) assertions.
They fail the exact callback `Location == '/_spike/complete'` assertion. The
original logs do **not** contain actual callback status, target, elapsed exchange
time or the swallowed exception. They therefore cannot identify a timeout,
cookie fault, identity rejection or session-store rejection retrospectively.
The old isolated ownership case passed unchanged (1 passed in 2.17 s); the
second case had not previously been rerun individually.

The callback catches exceptions and normally redirects to `/_spike/rejected`;
middleware can also reject requests. A generic failed redirect assertion alone
does not establish which path occurred. No indexing code is invoked by these
login helpers or the failing setup. No security vulnerability or causal link
to indexing is demonstrated.

### State, order, initialization and environment analysis

- Every harness constructs fresh clocks, issuer key/code dictionary, protocol
  transaction dictionary, preauth/attempt dictionaries, session store, controls
  and locks. `finally: fixture.clear()` cancels transaction/code timers, clears
  state and drops the issuer key. Test clock 1000 and wall clock 2,000,000,000
  are explicitly supplied to both protocol and issuer, so suite elapsed time
  does not itself age their synthetic tokens. RSA key creation happens before
  callback exchange; its time is not the callback's two-second exchange budget.
- The issuer's `subject` is mutable within a fixture and set immediately before
  each sequential login. The ownership case intentionally shares the fixture
  across A/B/the later tab. This warrants checking reuse, but the two failures
  do not share a required third-login condition: admission failed on login one.
  No module-level shared mutable login store was found. Existing fault-injection
  tests use pytest `monkeypatch`, which restores their changes after each case.
- `SessionTransport` / `LoopbackTransport` dispatch only to explicit ASGI apps;
  they contain no socket fallback. BFF/issuer origins and callback are constants,
  including ports 9444/9443. A competing local listener on those ports cannot
  receive these requests. No listener scan or external probe was necessary.
  Clients use `trust_env=False`, separate provider cookie jars and disabled
  automatic redirects. Environment activation flags cannot enable these fixtures.
- `Protocol.finish` uses a real `asyncio.timeout(EXCHANGE_TIMEOUT)` of two
  seconds, despite injected logical clocks. Host scheduling or a slow exchange
  can therefore cause rejection while synthetic time stays fixed. This is a
  plausible hypothesis, not a measured explanation of the old failures. Their
  logs lack phase timing/exception evidence; thermal, paging and host-load causes
  were not measured. Other failure causes remain possible.

### Bounded attempts executed for this review

All attempts used fictional in-process fixtures and frozen installed dependencies.
No original assertion was weakened, no retry was added, and no authentication
file was changed. The fixed matrix and its explicit bounds are retained in
`review_checks.py` and `triage_login.py` in the new ignored receipt directory.

| Attempt | Result |
| --- | --- |
| Original two cases, ownership then admission, fresh pytest process; 60 s command bound | **2 passed in 1.66 s** |
| Same two cases, admission then ownership, another fresh process; 60 s bound | **2 passed in 1.96 s** |
| Related-module pass, in explicit order OIDC spike, session security, session races, ownership security, minimized admission; 300 s bound | **683 passed in 126.05 s** (128.525 s command wall). This includes the existing provider timeout/no-network and monkeypatch fault tests followed by ownership/admission cases. |
| Fixed diagnostic matrix: three sequential A/B/A logins per scenario, fresh session jars / one reused jar / ownership three jars / admission three jars; 60 s total bound | **12 successful 303 callbacks to `/_spike/complete`**. No captured exception in the four login paths; zero socket-connect/DNS attempts under guards. |
| Single deliberately delayed fictional `/token` positive control, retaining the original two-second timeout | **303 to `/_spike/rejected` in 2.079 s**, `CancelledError` -> `TimeoutError` -> `Rejected`; no session cookie or session publication. This is an injected mechanism control, not reproduction of either historical spontaneous failure. |

In the twelve successful diagnostics, login times were 0.114-0.316 s with tracing;
initialization was 0.289-1.506 s. After each login, preauth, attempts, transactions
and issuer codes were empty. Three separate jars retained three sessions; a
reused jar replaced the previous session and retained one. After clearing each
fixture, all five state counts were zero and its issuer key was absent. The
timeout control consumed the pending transaction/attempt, retained one unused
issuer code until fixture cleanup, and published no session. Diagnostic logging
contains only safe target/status/timing/counts and exception class/file/line;
no cookie, code, token, query, response payload or exception message is logged.
Tracing adds overhead, so these times are diagnostic observations only.

**Disposition:** cause of the two original failures remains **NOT ESTABLISHED**.
Simple pair-order and fixture-reuse reproductions did not fail. This does not
exclude a dependency on earlier full-suite tests, intermittent scheduling or
another environment effect. The historical local full-backend gate remains
unresolved. No third full 1061-case retry was run to seek green. A future
separately scoped investigation should capture safe callback target/status,
exchange timing and exception location on the first naturally recurring failure,
without logging credentials, relaxing timeouts or retrying login automatically.

## Track B: exact minimal indexing adoption candidate

The proposal is exactly the Python lookup replacement in
`backend/experiments/indexing_validation.py::IndexedBatch.references` and the four
single-occurrence substitutions in
`frontend/scripts/shared-rules/indexing-transforms.mjs::replacements`. Those
copies remain disabled experiments. They identify the following **three protected
files** that would require separate authorization if changed in place:

| Protected location | Exact proposed change | Required invariant |
| --- | --- | --- |
| `backend/experiments/minimized_contract.py::MinimizedBatch.references`, final commercial loop (original lines 240-241) | Immediately before the loop, build `alias_members: dict[str, list[Observation]]` by visiting `self.observations` in order and each observation's `dict.fromkeys(order_keys)`. Append the observation once per alias. Replace only `members = [o for o in self.observations if commercial.alias in o.order_keys]` with `members = alias_members.get(commercial.alias, [])`. | Keep every earlier validator and both following `require` predicates verbatim. Do not filter by domain while building the index: foreign-domain members must still reach and fail the existing domain predicate. Group order remains the existing first-seen alias order. |
| `frontend/src/features/discovery/discovery.ts::linkEvidence`, transaction branch (lines 57-65) | Build a `Map<string, EvidenceObservation[]>` within each existing relationship/domain group. Walk support in order; walk `new Set(observation.order_keys)`; append once per observation/alias. Iterate `[...aliasMembers.keys()].sort()`, and replace `support.filter(o => o.order_keys.includes(order))` with `aliasMembers.get(order)!`. | Preserve sorted alias traversal and original support order/multiplicity. A repeated alias on one row must not duplicate that row. Keep paid/cancelled predicates, conflict objects and complete conflict support verbatim. No cross-domain/relationship index. |
| `frontend/src/features/assessments/assessments.ts::assessDiscovery`, local setup and validity membership (lines 34-47) | Build `sourceAdapters: Map<string, Set<string>>` over all `graph.sources`, and `primaryMembers: Map<string, Set<string>>` over primary-role `graph.relationship_evidence`, keyed by relationship ID. Replace only the two `.some(...)` existence predicates with `sourceAdapters.get(o.source_id)?.has(o.adapter)` and `primaryMembers.get(relationship.id)?.has(o.id)`. | Use separate nested keys, preserve all adapters/primary memberships for repeated keys, and leave source/evidence arrays unchanged. Sets answer existence only; they must never deduplicate emitted evidence. All surrounding version, ID, domain, type, issue, uniqueness and support checks remain identical. |
| Same assessment file, already validated transaction evidence (lines 70-72) | `const cancelledAliases = new Set(evidence.filter(o => has(o, 'CANCELLED_BEFORE_PAYMENT_CLAIM')).flatMap(o => o.order_keys));` Then `const sameOrderConflict = evidence.some(paid => has(paid, 'PAID_RECEIPT_CLAIM') && paid.order_keys.some(key => /^order\d{4,5}$/.test(key) && cancelledAliases.has(key)));` | Preserve the paid-side regex, same-row dual claims, relationship/domain scope and every following classification/rationale/limitation. Invalid aliases must not become assessment conflicts. |

No parser, classifier, input field, public contract, explanation, oracle, action,
resource limit, timeout, executor, session code or database change belongs in
this minimal algorithm patch. The additional package/provenance work below is a
separate reviewed prerequisite; three algorithm files alone are not a complete
adoption change. Do not replace `MinimizedBatch` with the experimental subclass:
`SyntheticRegistry.admit` requires its exact class, and `admission_boundary.model_input`
rejects subclasses/extra internal state before serialization. Loosening either
guard would be a new admission policy, not this optimization.

### Semantic review and its limits

The Python AST test restores the old membership expression, removes only index
construction and requires the remaining validator AST to match exactly. Fields,
bounds, strict types and field validators are inherited unchanged. Membership
lists preserve global observation order, one entry per observation containing an
alias, including invalid foreign-domain members for rejection.

In TypeScript the discovery index is local to the original domain/type support
group; sorting its keys is equivalent to sorting the old Set of aliases. Source
and primary-edge Sets replace existential tests only. Repeated source/edge rows
remain in the graph, duplicate-role support is retained and duplicates do not
become independent corroboration. Cancellation membership is the union within
the validated relationship; the regex and paid predicate are unchanged. Unknown
claims, explanations, priority/confidence, context and unresolved paths are
outside these substitutions.

This equivalence is supported for the validated typed JSON boundary and tested
negative graphs. It is not an exhaustive equivalence claim for arbitrary JS
objects: eager index construction can visit data that an old short-circuit scan
would not visit. Null entries, getters/proxies, non-string identifiers such as
NaN (Map/Set use SameValueZero while old comparisons use `===`), or concurrent
mutation are outside that boundary. Do not widen a public graph intake or claim
identical arbitrary-object exceptions on this evidence.

The fresh combined parity run **DID NOT COMPLETE**, as recorded below; it must
not be represented as 179 passed. Independently,
the read-only numeric audit rechecked **120 archived child runs: 119 PASS / one
baseline DEADLINE**, with **59 complete successful baseline/indexed pairs**
matching input, complete result, discovery, explicit support hashes and full
output length. This includes all **32 catalog pairs**. The archive matches its
original receipt SHA-256
`0f275c9426f299ea5177e4ca043bb2f599c93a2fe90e080940b2acad4ee9e1c7`.
The killed local 10,000-commercial baseline has no complete output; its full-size
local parity remains **NOT TESTED**. Reading old measurements is not a new
benchmark execution. Historical faster CI completion is separate host evidence.

## Version, registry and provenance migration options

Current contract versions are exactly `minimized-evidence-v1`,
`phase2-normalized-v1`, `email_features_v1`, `relationship_fusion_v1`,
`email_context_v1` and `sensitivity_rules_v1`. The old registry schema/generator
are `minimized-registry-v1` / `minimized-projection-v1`. Its manifest pins eight
normalized frontend source hashes, the generator, corpus, lock and exact
whole-envelope batches/profiles. Builders verify those pins before extracting
declarations. Merely changing discovery/assessment source breaks the old
`ENGINE_PIN` checks and registry reproduction, even when result semantics match.

| Option | Consequence | Recommendation |
| --- | --- | --- |
| Retain the current isolated transform candidates | Keeps all original packages/pins and ordinary admission unchanged; supplies research evidence only. | **Current disposition.** |
| Add an immutable implementation revision with unchanged semantic wire versions | Separate indexed source/artifact identity and package manifest; old semantic contract remains exact, and old oracle hashes can be compared directly. Requires explicit owner agreement that versions describe semantics while an additional implementation revision identifies code. | **Preferred future proposal**, subject to all gates. |
| Introduce new fusion/assessment/contract or registry semantic versions | New Literal/dispatch handling, canonical envelope digests, derived registry, contract exports/client types and version rejection matrix. Preserve old versions in parallel and retain old oracles. Larger policy/API change even if outputs happen to match. | Use only if owners require version identifiers themselves to identify every implementation change. Not required merely to optimize lookup. |
| Overwrite the old registry/source pins under existing package identity | Loses historical reproducibility and confuses source provenance with semantic parity. | **Reject.** No silent repin or regeneration of existing expectations. |

For the preferred option, the separately authorized change should:

1. Preserve the historical v1 source tree/package at exact commit
   `580fddd8f081182a21bde60eb24d26005115e47f`, together with old manifests,
   builders, dependency locks, worker and immutable oracle files. Retain a
   reproducible historical build path and run it in read-only verification mode.
   A pointer to Git history alone is not proof the build still works.
2. Add a separately named source/package directory and manifest (proposed
   implementation ID `phase6c03-indexed-r1`, **not yet assigned/adopted**).
   Apply only the substitutions above to the copied declarations/validator.
   Prefer this parallel package to rewriting historical protected paths. Any
   later in-place source replacement must first provide equivalent historical
   reproduction and enumerate every protected-file change explicitly.
3. Bind that manifest to the original semantic contract and registry digest,
   approved input digests and the **existing** 70 profile oracle hashes. Add
   explicit new implementation/source/validator/build-tool/transform/worker
   digests; do not pretend the old `engine_sha256` values hash indexed code.
   A manifest references the old catalog; it does not enroll new workloads.
4. Record full source commit/tree and normalized source policy, Python validator
   hash, TS declaration selection, transform specification/hash if retained,
   Node 22.15.0 / TypeScript 5.9.3 / tldts 7.5.5, dependency locks, PSL hash,
   wrapper identity, artifact SHA, contract versions and oracle-package identity.
   Distinguish raw-file and normalized hashes: the old registry's LF-normalized
   lock hash is `cbdc95545ea0a4487e335689c912059972933e0940c2d8fabf68d3e9683769a0`,
   whereas this checkout's raw lock/artifact provenance hash is
   `a72dc674d057fe08ea893935193e3d204e69ab1a78efd68f02eb0bd38da0f3ed`.
   Both were verified; this is not a dependency change.
5. Use exact allowlisted package identity for future explicit offline selection;
   unknown/missing/mismatched revisions or hashes must fail closed. Never select
   a caller-provided artifact path, infer a revision from unchanged output bytes,
   silently fall back after rejection, or accept a browser classification as
   authority. Existing exact-type retained-state validation stays in force.
   Designing a new selector/consumer is follow-up work requiring authorization;
   it is not implemented by this proposal.
6. Produce independent old/new build and parity receipts tied to the same final
   reviewed source head. Do not overwrite old worker/provenance paths. The
   current indexed measurement worker is
   `03e7cb8cb9923a42b517feded409ff5bb2cff390aabde070fd874024f2df021f`,
   compared with original worker
   `69fcc47c8b0890c488900b4afe875aa7ce19faa6e257a691ad371fd53edff064` and
   baseline measurement worker
   `9fdc2ee12c7cff77dbad60231dcb7d25fb10f65dbffb5679af2219a2e5c9ed4f`.
   A future adopted wrapper/package has its own hash; do not reuse the experimental
   worker hash for different bytes. Adjacent provenance JSON is not a signature
   or durable, scoped evidence mapping.

No migration option, identifier, selector or version change is approved here.
Rollback for the current task is leaving the additive experiment disabled and
unmerged. Future package rollback must select the preserved old package explicitly
and must not remove deletion receipts or rewrite historical results.

## Workload claims and adoption acceptance gates

Current catalog-admissible functional scope is 32 complete envelopes / 70 profiles,
at most three sources, ten total rows, four observations, one commercial alias
and 1,977 input bytes. Individually approved files do not enroll every combination.
The 20/1000/4000/10000-row account/commercial/unresolved/duplicate constructions
are model-level capacity fixtures. In particular, 20 modeled email sources with
500 rows each cannot be produced by the current one-row-per-email adapter;
history cannot provide email commercial claims. All four full-size constructions
were previously denied by ordinary catalog admission with 422. Preserve that
denial and the failed local baseline; do not rebrand them as catalog success.

The historical indexed 10,000-commercial child took 0.441 s, validation 0.831 s;
baseline validation took 53.906 s and its child was killed at five seconds.
Account child was 0.312 s versus 4.398 s. Smaller/unresolved/duplicate cases were
mixed. These observations support the lookup proposal, not uniform speedup or
portable capacity. Parent validation precedes the child clock, and unresolved
output is about 24 MB; decode/hash/serialization costs remain material.

Every gate below is required for its stated scope. PASS means executed evidence
for the candidate's exact final source head; missing evidence is OPEN, and an
observed mismatch or exceeded required bound is FAIL/STOP. No automatic exception.

| Gate | Explicit acceptance / failure rule | Current disposition |
| --- | --- | --- |
| Authority and change scope | Separate owner authorization names protected algorithm files or parallel package, revision strategy and allowed consumers. Any extra rule/auth/contract/limit change stops for review. | **OPEN; proposal only.** |
| Historical preservation/reproduction | All 285 protected blobs, original 270/252/193 inventories, all current tracked inputs, old receipts/oracles and old package build remain verifiable. New package cannot overwrite old manifests/artifacts. | Preservation checked below; new package reproduction **NOT IMPLEMENTED**. |
| Complete semantic regression | Original 71 immutable suite plus 108 indexing cases, including all 70 existing profiles in both source orders, all 32 catalog comparisons and 44 strict deep-object TS cases. Match full discovery/assessment, support order/multiplicity, conflicts, contexts, rationales/explanations, limitations/actions and all seven unknown claims. Any drift stops; never regenerate old oracles. | Fresh combined run **INCOMPLETE / native crash**; historical 179-pass evidence preserved. Adoption code itself **NOT IMPLEMENTED**. |
| Negative admission/support/provenance | Match both validation error outcomes for the existing 32 mutations and ordered/foreign-domain cases; retain invalid-support and `INVALID_EVIDENCE` cases, duplicate handling, exact types and whole-envelope 422. Reject extra/missing/foreign/reordered references, wrong versions/package pins and retained-state tampering. No filtered-away invalid evidence, unknown-version fallback or broadened admission. | Existing indexed boundary cases tested; new package/version negatives **NOT IMPLEMENTED**. |
| Login and application regression | Establish the spontaneous local login cause, review any separately authorized fix, then execute a predeclared full original 1061-case run with zero failures/xfail/hidden retries. Preserve every failed receipt. Repeat frontend 284, Chromium nine, privacy/rollback seven; existing proposed frontend performance failures remain explicit. | **OPEN**; targeted success does not close the local backend gate. Full application suites not rerun here. |
| Tenant/schema regression | Existing 434 restricted-role DB cases before and after guarded roundtrip with ledger retained; prove no schema/RLS/ledger drift. Native and original Docker scaffold evidence labeled separately. | **NOT RERUN** in this scoped task; no database serving/adapter authorized. |
| Resource bounds and workload definition | Preserve 5 s child wall / 256 MiB process committed memory / 8 MiB input / 32 MiB output; 5000 ms browser deadline unchanged. Run bounded paired cases on named reference hosts with complete results, resource samples through serialization/write, no truncation or partial publication. Define parent/end-to-end budgets and adapter-realizable worst cases separately. Failure stops; do not raise limits or narrow capacity silently. | Old local matrix 119/120; baseline DEADLINE retained. New broad capacity/host/load/parent limits **OPEN**. |
| Artifact/provenance integrity | Independently reproduce old/new packages and check code/toolchain/lock/PSL/wrapper/validator/output/oracle identities; fail closed on every mismatch. Durable mapping must later prove owner/collection/generation bijection and complete support. | Local artifact/source pins verified; migration/durable proof **OPEN**. |
| Frozen quality and exact-head CI | Scoped checks below plus full appropriate lint/types/contracts/generator/corpus/build/audits and required push/PR/security receipts for the final adoption commit. Old CI is not a later-head receipt. | No adoption commit or fresh CI triggered here. |
| Security/isolation/durable approval | Close the relevant original security-report gaps and obtain qualified independent human review and explicit required approvals before any broader capability. | **OPEN**; AI-assisted evidence is not independent approval. |

## Remaining gaps and NOT TESTED limits

The first two local backend failures remain unresolved even if all scoped checks
pass. Not tested here: full-suite order bisection, reproducing historical host
load, long-duration/randomized/concurrent login schedules, actual provider/login
behavior, historical callback status/exception recovery or a production auth fix.
The single forced delay is not evidence those old runs timed out.

No new capacity matrix was run; complete local 10,000-commercial baseline output
parity is still missing. New adapter-realizable maxima, dense combinations of
domains/aliases/contexts, sustained-load percentiles, cold-cache/power/thermal/
paging attribution, parent peak-memory bounds/enforcement and a complete
end-to-end service deadline remain unestablished. The old wrapper reports peak
RSS before serialization; RSS is distinct from Job Object committed memory.
Do not infer a zero-cost index or treat a child budget as an end-to-end SLA.

Windows OS network-denial proof, memory exhaustion, cancellation/interruption,
hostile child/descendant cleanup, abnormal exit and malformed/oversized/exact-cap
output remain untested at this executor boundary. Node permissions are not a
malicious-code sandbox. The login diagnostic socket guard proves only its own
in-process paths, not child OS network isolation. Linux execution remains
fail-closed; Linux typechecking does not prove Linux executor isolation or portable
five-second capacity. Production artifact signing/deployment attestation is absent.

The fresh combined immutable/indexed pytest run also failed to complete because
of a native Python process failure, detailed below. Its underlying pytest
failure and native crash cause are not established. This is an additional current
verification gap, not evidence that the historical indexed parity changed or
that a resource bound was satisfied. No new whole-suite retry was made.

The provenance adapter remains unimplemented: scoped owner/collection/generation
IDs, missing/extra/foreign-reference rejection, bijections, duplicate primary
promotion, per-copy context, both deletion orders, contextual-source removal,
action/support recomputation, atomic publication and durable fences all need
their own authorized proof. The schema's finding evidence roles are
primary/corroborating/context while rules include duplicate support. A future
projection must retain duplicate membership through typed equivalence groups;
it must not relabel duplicates as corroboration or silently migrate the schema.
Durable deletion/restore, new DB/WAL/artifact sentinel checks, save/delete races,
endpoint authorization, consent and real identity/provider behavior are not
established by existing in-memory or disposable tenant tests.

TM-07 isolation/resource/portability, TM-09 durable provenance/version identity,
TM-10 conservative unknown claims and TM-13 durable survivor recomputation remain
subject to their original gates. Production G-S3, P5-F01/P5-F02, legal/provider/
security, qualified independent human review and durable lifecycle remain OPEN;
ADR-015 through ADR-022 remain PROPOSED. No production, real data, deployment,
database-backed serving, durable adapter, schema migration, Phase 6C-04/05 or
merge is authorized or performed.

## Review receipts and final verification

New receipts are local under `.local/phase6c03-adoption-review/`: `pairs.json`,
`neighbors.json`, `login-diagnostics.json`, `evidence-audit.json`, `parity.json`,
`collect.json`, `nonresource.json`, `quality.json`, `before-sha256.json` and
`final-state.json`, with the exact bounded scripts retained.
Two overly broad read-only snapshot attempts were interrupted before completion;
neither is claimed as a preservation pass. The completed bounded snapshot covers
**296 tracked files plus 59 existing Phase 6C-03 receipt/artifact files (355 total)**.
It excludes dependency caches, clean checkout copies and disposable database
directories. No old receipt or database artifact was removed. Full unrelated
historical `.local` trees were not hashed in this task.

The completed snapshot comparison found **zero changed prior files**. The 285
protected-blob checker passed; the nested preservation checker also passed
270/252/193 inventories and the original registry digest. A check with no
executed receipt remains NOT TESTED.

### Incomplete fresh combined parity run

`uv run --frozen pytest -q -x -s indexing_tests rule_tests` exited
**3221225477** after **21.449 s command wall**. Its full 2,112,087-character
output is retained in `parity.json`; it begins with 68 progress markers, then
514 repeated `Windows fatal exception: page error` traces. The first trace is
in Python `inspect.py::ismodule/getmodule/findsource`, reached while pytest was
formatting a failure report. No normal test summary or underlying assertion was
produced. Do not claim that the entire suite passed, that all 68 were independently
audited as passes, or that the failed assertion was a timeout/semantic mismatch.

A subsequent **collection-only** invocation succeeded and listed 179 cases;
it executed no tests or rule children. In that order the next case after 68
markers is `indexing_tests/test_indexing.py::test_immutable_profile[c27]`.
That identifies a follow-up candidate by position, not a captured failing node
or a recovered exception. No repeat of that profile or full combined suite was
used to get green. The original 71-case suite was not reached in this invocation.
The chain deliberately skipped the dependent quality step after failure;
independent quality/preservation checks were then invoked separately.

### Completed independent checks

| Executed command/scope | Actual result |
| --- | --- |
| Two exact login cases, two explicit orders | 2 passed in 1.66 s; 2 passed in 1.96 s; separate receipts, not four distinct test definitions |
| Five related fictional login/session/ownership/admission modules | **683 passed in 126.05 s** |
| Twelve-login diagnostic matrix and one injected timeout control | PASS for their explicitly described expectations; no spontaneous failure reproduced |
| `pytest -q --tb=no indexing_tests -k 'not immutable_profile'` | **38 passed, 70 deselected in 1.84 s**, including the 44 inner strict-object TS cases. This is an independent subset excluding all immutable child-profile reruns; it does not repair or replace the native-crash receipt. |
| Ruff check / format check on indexing model, measurement/benchmark/preservation scripts, indexing tests and original session helper | PASS; six files already formatted |
| Configured strict `mypy` and `mypy --platform linux` | PASS, 58 source files each |
| ESLint on the three indexing build/transform/differential JS scripts | PASS |
| Frontend `npm.cmd run typecheck` and strict standalone `tsc` on existing generated indexed `copy.ts` | PASS |
| `scripts.check_indexing_preservation` | PASS, 285 protected blobs unchanged |
| `scripts.check_phase6c03_preservation` | PASS, 270/252/193 inventories and original manifest digest |
| Read-only numeric/artifact/source/lock audit | PASS, 120 archived rows / 59 completed parity pairs / 32 catalog pairs; exact original and measurement-worker hashes verified |
| Before/after byte snapshot | PASS, 355 prior files unchanged: all 296 current tracked files plus 59 prior Phase 6C-03 receipt/artifact files |

The failed combined run remains **INCOMPLETE**, despite these independent
successes. No additional immutable-profile retry, 10,000-row benchmark, new
artifact build, full 1061-case backend run, full frontend tests/build/audit,
Chromium/performance run, contract export/generator, corpus check, dependency
audit, database/scaffold run or new CI was executed in this scoped task. Prior
receipts remain historical evidence, not fresh passes for this document or a
future adoption commit. No installed dependencies were updated.

Final local HEAD remains `580fddd8f081182a21bde60eb24d26005115e47f`; base/main/
origin-main remain `2038c65554501b7f0a099976ea07b75606cb7ff7`. Tracked working
files and index have no diff. The only untracked deliverable shown by Git is
`docs/PHASE6C03-ADOPTION-REVIEW.md`; ignored new diagnostics are not staged.
No commit or push was made. PR #13 remains draft/open/unmerged at the expected
head/base. Remote check receipts for the existing head are historical to the
proposal; no adoption approval is inferred from them.

**Proposed owner disposition:** defer adoption and keep C03-R01 OPEN. Retain the
four demonstrated lookup substitutions as the minimal candidate; prefer the
parallel immutable implementation-revision strategy for a future explicitly
authorized change. Require the gates above, including resolution of the two
original local login failures and the fresh parity-run crash, before claiming
adoption acceptance. This document records no approval, exception or activation.
