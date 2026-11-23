# FootPrint PV1 Phase 4 report

Date: 2026-11-23 (Asia/Calcutta). Branch: `phase4/local-synthetic-assessments`.
Base current main: `018a85b08c7a26828a8c5fcfe8535c35610cfdd3`, after Phase 3 merge
`3e4843e1aef7a739a44892209ca7c8c12c5837b4`. Status: implemented and validated for
review. [PR #4](https://github.com/ankit8github/FootPrint/pull/4) is open and
unmerged; no deployment or real-user processing.

## Implementation plan and evidence gap

Read the product requirements, evidence model, security architecture, phase plan,
ADRs, approved corpus 1.1.0, Phase 1–3 reports and current parser/discovery code.
The baseline remains **product-owner-approved, AI-assisted baseline**, not
independent blind human review; no reviewer is invented.

Phase 3 already retains explicit account, receipt/cancellation, unpaid-invoice,
newsletter and visit features. It deliberately does not retain the clinic source's
appointment-portal context. Neither its sender domain nor generic account feature
alone justifies the c18 health-context priority. Add one bounded, allowlisted
`CLINIC_APPOINTMENT_PORTAL_CONTEXT` code, requiring both an ASCII clinic-account
subject cue and an unquoted appointment-portal account-request statement. Subject,
body, diagnosis and identifiers are never returned. Sender attribution stays
unverified; this contextual setting is not a personal health attribute.

1. Keep existing Phase 2/3 outputs and versions intact; derive the single optional
   context feature inside the same hash-gated browser worker boundary.
2. Add deterministic `sensitivity_rules_v1` assessments with independent priority,
   evidence state/confidence, evidence-linked rationale codes, fixed human-readable
   explanations and explicit unknown claims. No global domain/risk score.
3. Add a separate minimal read-only `/phase4` inspector, retaining all existing
   routes. No dashboard filters, summary workflow, action links or source deletion.
4. Compare all 29 cases and six independently rebuilt survivor sets as immutable
   oracles. Measure labeled assessment agreement and Unknown separately on this
   reused synthetic development set; no real-world accuracy claim.
5. Test context abuse, duplicates/conflicts, order/subset semantics, rationale
   support, Unknown, constrained rendering and local privacy; run all Phase 0–3
   regressions, contracts, audits, clean checkout and GitHub CI/Docker checks.
   Record exact results/limitations/exit gates, then open PR #4 without merging.

No persistence/schema expansion, real-user inputs, auth, external AI, deployment
or Phase 5 functionality is authorized.

## Implemented behavior and architectural decisions

ADR-012 in [DECISIONS.md](DECISIONS.md) records the rule table and context decision.
`assessSelectedFiles` runs inside a dedicated module worker. The existing exact
approved-byte gate, 20-file / 1-MiB-email / 10-MiB-total / 10,000-record bounds,
safe MIME/URL/UTC handling and five-second worker deadline remain enforced.
All six invalid/missing c12 Chrome timestamps remain excluded, never replaced
with import time. No API, dependency, lockfile, migration or personal schema changes.

The optional discovery context sink derives the single contextual code from the
same approved bytes as discovery, without a second file read. The sink exposes
only observation IDs and enumerated codes. Context requires a bounded ASCII
subject (256 characters maximum) plus decoded, unquoted plain-body context
(16,384 aggregate characters maximum). HTML, attachments, encoded subjects,
ambiguous origins, forwarded/quoted/negated text and injected instructions cannot
supply context. It neither interprets diagnosis text nor authenticates a sender.
Ordinary Phase 2/3 outputs and version identifiers remain identical; a literal
comparison verifies the optional sink is the sole change in the discovery service.

`phase4-assessment-v1` contains the unchanged discovery graph, separately linked
`email_context_v1` codes and `sensitivity_rules_v1` assessments. Assessment IDs and
source IDs are batch-local; the envelope records versions and every assessment
records its rule ID. No current-time, random or remote input affects assessment.
No domain-wide aggregate score or category lookup by domain/case/fixture ID.

| Evidence basis | Review priority | Evidence dimension and explanation |
| --- | --- | --- |
| Explicit ordinary account request/notification | Medium | Original inferred/Medium account claim remains separate |
| Account plus linked clinic appointment-portal context | Sensitive | Contextual review, no diagnosis/treatment/health-attribute inference |
| Same-order paid/cancelled claims | Sensitive | Original inferred/Low confidence; both contradictory claims preserved |
| Paid-order message claim | Sensitive | Message financial-interaction claim, not payment confirmation |
| Explicit unpaid-invoice-only evidence | Medium | Commercial interaction; no completed purchase/payment or retained credentials |
| Valid visit-only relationship | Low | Observed/High source-record evidence, not an account |
| Newsletter relationship | Low | Inferred/Low; no retention/sharing/sale inference |
| Unresolved/unsupported context or invalid support | Unknown | Missing evidence never defaults to Low |

Priority does not derive from confidence. For example, cancellation-only category
context outside the approved cases can remain Unknown while the independently
supported commercial relationship stays inferred/Medium. No unsupported
combination is forced into a stronger category just to increase coverage.

Every rationale uses the approved code vocabulary and canonical source support.
HEALTH_CONTEXT cites only the specific contextual observation, not every account
source. Missing, mismatched, stale or duplicate-primary links produce Unknown
without fabricated support. Exact copies retain alternate Phase 3 provenance;
they never increase priority/confidence. Removed sources cannot remain cited in
fresh remaining-source test inputs. Source deletion itself is not implemented.

Every assessment explicitly keeps sender authenticity, current account activity,
payment completion, retained payment credentials, company retention, data sale
and breach status unknown/insufficient; retention/sale fields also stay unknown.
No sensitive personal attribute value, breach or confirmed company-held data is
inferred. Excluded rows and empty survivors have no assessment, rather than
invented Unknown/Low findings.

All human-readable prose comes from fixed maps of rule, rationale and limitation
codes, with no source interpolation. The separate read-only `/phase4` inspector
shows priority, evidence state, claim confidence, source/row support, rationale
and limitations. Its renderer independently selects fixed text and ignores
worker-supplied prose; unsafe domains/IDs and prototype-key codes are not shown.
React text is escaped. It displays at most 200 bounded assessment records, without
dashboard filters, category summaries, action links or source-management workflows.
Clear, consent withdrawal, completion/error, timeout and unmount terminate the
worker; minimized results remain only in memory until clear/page close.

The strict existing API rejects assessment/context/explanation extensions and
multipart, without body echo or logging. The browser never calls it. No network,
DOM parsing, HTML rendering, source storage, analytics or external service API is
used by the worker. The draft SQL remains a proposal and is not installed.

## Immutable-oracle comparison and measured agreement

[PHASE4-METRICS.json](PHASE4-METRICS.json) is reproduced by
`npm.cmd --prefix frontend run phase4:metrics`. Baseline: corpus 1.1.0, SHA-256
`53b4ff49c5b31e4fa5b2670c757c02058d0ffab3f6b0472fe8d198a86bdd36b1`.
All 29 scenarios and six survivor snapshots are unchanged read-only test oracles.
Original raw files, hashes, labels, blank review materials, archives and Phase 1–3
reports/metrics are preserved. Original Phase 1 null classifier metrics describe
that historical artifact phase; they are not rewritten as Phase 4 measurements.

| Evaluation | Snapshots | Expected/predicted assessments | Matching priorities | Agreement | Unknown expected/predicted | Exact compared snapshots |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Initial scenarios | 29 | 34 / 34 | 34 | 1.000 | 6 / 6 | 29/29 |
| Survivor subsets | 6 | 6 / 6 | 6 | 1.000 | 0 / 0 | 6/6 |

Initial non-Unknown labels: 28/28 match (five Sensitive, 13 Medium, ten Low).
All six expected Unknown items remain Unknown; none is forced Low. Initial
Unknown rate is 6/34 (17.65%). Survivor labels are one Sensitive, three Medium,
two Low; Unknown rate 0/6. Across both groups the priority confusion matrix has
only diagonal counts: Sensitive 6, Medium 16, Low 12, Unknown 6. Missing and
unexpected predictions are zero. Empty/excluded-only snapshots have no label and
do not inflate the assessment denominator.

Keys are `(snapshot, domain, relationship_type)` or `(snapshot, unresolved support)`.
Agreement = matching keyed priorities / (expected items + unexpected predictions).
Missing predictions disagree; an empty denominator is null, never perfect accuracy.
This counts relationship occurrences, not independent people or distinct companies.
Overlapping cases and source reuse are intentional. This is **development-set
agreement only**, with rules designed using these known synthetic examples; it is
not a holdout evaluation, independent blind review, calibrated confidence or
real-world accuracy. Corpus approval status is **product-owner-approved,
AI-assisted baseline**; no reviewer or independent judgment is fabricated.

Exact comparisons include priority, rationale codes, domain/type, state/confidence,
canonical support, unknown retention/sale, exclusions and duplicate groups.
Rationale-specific support, explicit unknown claims, deterministic output and
semantic reverse-order stability are additionally asserted. Canonical duplicate
IDs may change with source order; source membership and semantic outputs remain
stable. Survivor tests independently analyze remaining files, not mutable deletion.
Tests also remove the sole contextual source from a fresh same-domain account set,
prevent stale health rationale, and distinguish different-order commercial claims
from same-order contradictions. Arbitrary future inputs are not oracle-approved.

## Executed local checks

Windows; Python 3.11.9, Node 22.15.0, npm 10.9.2, uv 0.9.29. Commands below use
the existing locked dependencies; no package/lock updates. Shell execution uses
the working approved fallback and command-scoped Git safe.directory. Caches are
ignored: `UV_CACHE_DIR=I:/FootPrint/.cache/uv` and
`PLAYWRIGHT_BROWSERS_PATH=I:/FootPrint/.cache/ms-playwright`.
Each command's exit code is checked independently; exact outputs are retained in
`.local/phase4-validation/backend.json` and `frontend.json`.

| Directory | Exact executed command | Result |
| --- | --- | --- |
| `backend/` | `uv run --frozen ruff check .` | PASS |
| `backend/` | `uv run --frozen ruff format --check .` | PASS, 17 files |
| `backend/` | `uv run --frozen mypy` | PASS, 17 source files |
| `backend/` | `uv run --frozen pytest -q` | PASS, 143 tests |
| `backend/` | `uv run --frozen python -m scripts.export_openapi --check` | PASS |
| `backend/` | `uv run --frozen python -m scripts.export_phase2 --check` | PASS |
| `backend/` | `uv run --frozen python -m scripts.validate_corpus` | PASS, 29 cases, six snapshots, 27 files, 48 events |
| `backend/` | `uv run --frozen pip-audit --cache-dir I:/FootPrint/.cache/pip-audit --progress-spinner off` | PASS, no known vulnerabilities |
| `frontend/` | `npm.cmd run contracts:check` | PASS |
| `frontend/` | `npm.cmd run lint` | PASS |
| `frontend/` | `npm.cmd run typecheck` | PASS |
| `frontend/` | `npm.cmd test` | PASS, 230 tests in nine files, final context-hook version |
| `frontend/` | `npm.cmd run build` | PASS, final context-hook version; chunk-size advisory disclosed |
| `frontend/` | `npm.cmd audit --audit-level=low --cache I:/FootPrint/.cache/npm` | PASS, zero known vulnerabilities |
| `frontend/` | `npm.cmd run test:smoke` | PASS, seven Chromium scenarios, final context-hook version |
| repository | `npm.cmd --prefix frontend run phase4:metrics` | PASS, 36 oracle/measurement tests; artifact reproduced |
| repository | `.local/phase0-validation/tools/actionlint.exe -shellcheck= -pyflakes= .github/workflows/phase0.yml` | PASS; optional integrations disabled |
| repository | `git -c safe.directory=I:/FootPrint diff --check` | PASS |
| repository | `python .local/phase4-validation/preservation.py` | PASS, exact checked paths saved in preservation.json; original tests/oracles/contracts/migrations/locks/history preserved; only optional context hook differs in discovery service |

New tests cover narrow positive/negative/encoded context, bounded subject/plain
text, quoted/forwarded/negated/injected content, unsafe origin, ignored HTML and
attachments, malformed MIME encoding, same-byte source provenance, priority vs
confidence, invalid/stale support, rationale-specific links, duplicates, Unknown,
same/different-order claims, and subset/order consistency. Rendering tests inject
hostile prose, HTML, raw IDs, URL domains and prototype keys; none is displayed.
Privacy tests prohibit network/storage/DOM/log calls. Backend tests reject new
assessment/context fields without echo/logging and verify no new upload route.
All prior Phase 0–3 tests and the existing 65-second subprocess-test harness bound
are unchanged; the production worker remains five seconds.

Playwright selects all 27 approved sources in bounded batches using real workers.
It checks clinic/context, invoice, conflict, Unknown, exclusions, transient reset,
raw/synthetic secret HTTP URLs/headers/bodies, WebSocket frames, console output,
external requests, rendered HTML/links, cookies, local/session storage, IndexedDB
and service workers. Altered/arbitrary and oversized file bytes fail closed.
Mobile layout has no page overflow; its viewport screenshot was visually inspected.
Production bundle scans find no raw recipient/order/invoice/secret sentinels.

Development check history: the first type check caught an overly narrow test-only
metrics key type; it was corrected without changing labels or production rules.
All 35 oracle comparisons passed on their first runtime execution. Source review
then replaced an initial second-read context approach with a code-only hook over
the same approved bytes; the final complete frontend suite passed for that change.
Vite's build emits a greater-than-500-kB main-chunk advisory. It exits successfully;
no warning threshold is raised or behavior refactored to hide it. No independent
security assessment, performance guarantee or real-user readiness is claimed.

## Limitations and exit gates

- Only unchanged approved synthetic bytes are accepted; the hash registry is
  unchanged. Narrow English/MIME/ASCII patterns are deliberately corpus-focused,
  not comprehensive mail understanding, negation/spoofing detection or diagnosis.
  Subject and appointment-portal cues may be untrusted claims; sender authenticity
  remains unknown. Unsupported category combinations stay conservative.
- Confidence is an ordinal claim tier copied from discovery, not a probability.
  Sensitivity is contextual review priority, not proof of unsafe storage, breach,
  real health data, completed payment or data sale. No personal attributes inferred.
- IDs are reproducible within an ordered batch, not stable across reorder/subset
  changes. No persistent identity or source manager. Survivor analysis in tests is
  not a deletion engine, and worker termination is not secure-memory erasure.
- This inspector is a Phase 4 development surface, not a completed MVP or Phase 5
  dashboard/actions/deletion workflow. No auth, persistence, personal schema,
  general imports, external AI or production deployment. No real personal data.
- Exit requires successful local and clean-checkout/CI/Docker checks, unchanged
  oracles, defined agreement/Unknown measurements, explained limitations and an
  open review PR. Human review and merge are separate gates. PR #4 must remain
  open/unmerged; main stays at the pre-Phase-4 base. Implementation/validation
  gates are met by the evidence below; human review/merge remain pending.

## Fresh-checkout and GitHub CI/Docker evidence

Validated executable commit: `e9e9d0e4397f6e7f2cd2b717f8f01a5587a97285`.
This report-only follow-up changes no executable input. The PR checks tab records
checks on the current review head; explicit executed implementation runs are:

- [Push CI 45129420629](https://github.com/ankit8github/FootPrint/actions/runs/45129420629):
  **SUCCESS**, every job and step.
- [PR CI 45129643671](https://github.com/ankit8github/FootPrint/actions/runs/45129643671):
  **SUCCESS**, every job and step.

Decoded job logs independently confirm 143 backend tests, 230 frontend tests,
seven Chromium scenarios, zero-known-vulnerability npm/pip audits, and
`PASS: PostgreSQL upgrade, constraint enforcement, downgrade, re-upgrade; no
personal tables.` Both clean Ubuntu 22.04 runners use Python 3.11.9, Node 22.15.0
and uv 0.9.29 with locked installs. Contract/lint/format/types/corpus/build checks
and disposable DB cleanup passed. No workflow modification or skipped check used.
Vite's disclosed chunk-size advisory is also present in CI; the build passes.

Docker is unavailable on the Windows host. Actual CI execution, rather than
inference from configuration, verifies these existing commands:

```text
docker compose config --quiet
docker compose up -d --wait db
uv run --frozen python -m scripts.check_database  # backend/
docker compose down --volumes
```

Only the disposable scaffold migration is exercised; no personal schema or
assessment/observation persistence is installed. No local Docker pass is claimed.

Fresh Windows remote-clone commands (from repository root, then clone root):

```powershell
git -c safe.directory=I:/FootPrint clone --no-hardlinks --branch phase4/local-synthetic-assessments https://github.com/ankit8github/FootPrint.git I:/FootPrint/.local/phase4-clean-checkout-e9e9d0e
uv sync --project backend --frozen
npm.cmd ci --prefix frontend --cache I:/FootPrint/.cache/npm
```

No untracked environment, .env, virtualenv, node_modules or source file was copied
from the working tree. All fresh locked installs passed. From the clone's
`backend/`, the local table's ruff check/format, mypy, pytest, both API export
checks and corpus validation passed (143 tests). From its `frontend/`, contracts,
lint, typing, unit tests (230), build and all seven Playwright scenarios passed.
Every clean-checkout command exited zero on its first execution. The full command
arrays, outputs and exit codes are retained in
`.local/phase4-validation/clean-checkout.json`. Original Phase 3's subprocess-test
timeout remains 65 seconds; the five-second production deadline is unchanged.

The GitHub connector's creation attempt returned a permission-denied integration
error. PR #4 was opened through the repository's existing Git credential helper;
credentials stayed in memory and were never logged or saved. This changes no
application permission or authentication behavior.

Final review remains a human gate. Main remains
`018a85b08c7a26828a8c5fcfe8535c35610cfdd3`; no PR merge is authorized here.
No Phase 5 dashboard/actions/deletion, deployment, real personal data, persistence
or external AI was implemented or enabled. Work ends with the open review PR.
