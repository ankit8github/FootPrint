# FootPrint PV1 Phase 3 report

Date: 2026-11-23 (Asia/Calcutta). Scope: browser-local synthetic discovery and
evidence linking only. Branch: `phase3/synthetic-evidence-linking`, based on current
main `d151fe290787079d6cedea1f3c30b30dd7512809`, after Phase 2 merge
`04fcc45baa8278231948d05577b469fa8fd9cc46`.
Status: implemented and validated for review. [PR #3](https://github.com/ankit8github/FootPrint/pull/3)
is open and unmerged. Local, fresh-checkout and GitHub CI/Docker evidence is
recorded below. No merge or deployment.

## Evidence gap and implementation plan (before implementation)

Phase 2 deliberately emits unclassified email observations and unverified claimed
sender domains. A claimed sender domain alone establishes neither an account,
transaction nor marketing relationship. Phase 3 must extract actual bounded
message evidence before linking any such claim; sender attribution stays unverified.

1. Reuse the approved SHA-256 gate, size/time/MIME/URL/time controls and transient
   worker boundary. Extract only enumerated features from safe plain-text parts
   and a narrow subject newsletter cue. Never read attachment or HTML payloads as
   evidence, execute instructions, or emit raw text/addresses/URLs/identifiers.
2. Link evidence using deterministic source/row IDs, exact-copy provenance and
   domain/type keys. Keep ambiguous/spoofed/quoted/injected inputs unresolved;
   visits remain visits. Preserve same-order receipt/cancellation contradictions
   with Low claim confidence and no payment outcome assertion. Do not increase
   confidence for duplicates or browser corroboration of account/payment claims.
3. Compare in-scope fields against all 29 initial cases and six independently
   rebuilt survivor sets, using unchanged corpus 1.1.0 read-only test oracles.
   Sensitivity/priority fields are explicitly unassessed, not manufactured.
   Define precision/recall over (case, domain, relationship type), report denominators,
   separate survivor results and disclose development-set reuse; no product or
   independent/blind-review accuracy claims.
4. Preserve Phase 0-2 behavior/contracts/tests; run backend/frontend/browser,
   contracts/audits and clean-checkout GitHub CI/Docker checks. Record precise
   executed outcomes, limits and exit gates. Open a review PR; do not merge.

No draft personal-data schema, persistence, auth, general real-user imports,
Phase 4 sensitivity, Phase 5 dashboard/actions/deletion engine, external AI or
deployment is authorized. The Phase 1 status remains product-owner-approved,
AI-assisted baseline, not independent blind human review.

## Implemented architecture

ADR-011 in [DECISIONS.md](DECISIONS.md) records the extraction gap, design and
trust boundaries. `/phase3` is a minimal read-only development inspector, not the
Phase 5 product dashboard. `/` and `/phase2` retain their existing behavior.

- The shared exact approved-byte SHA-256/adapter gate still precedes decoding.
  All ADR-010 limits remain: 20 files, 1 MiB/email, 10 MiB/batch, 10,000 records,
  five-second worker lifetime, bounded JSON/MIME/headers/URLs/times. Only the
  unchanged 27 approved synthetic source files can reach browser adapters.
- The optional MIME plain-text visitor leaves Phase 2 unclassified output intact.
  `email_features_v1` emits enumerated account-request, account-notification,
  paid/cancelled commercial claim, unpaid-invoice and newsletter cues, plus
  quoted/injection flags. It scans at most 16,384 aggregate decoded plain-text
  characters. HTML/attachments are ignored; encoded subjects are not decoded.
  The ASCII subject newsletter cue supports c15 at Low confidence without using
  HTML. Plaintext excerpts, subjects, addresses, commercial references and URLs
  are never emitted. Quoted lines/inline quotes, forwarded context, explicit
  negation and instruction markers have conservative handling.
- `relationship_fusion_v1` links only explicit features at exact canonical
  domain/type keys. Claimed authentication passes never verify sender identity.
  Ambiguous/mismatched origins, unsupported welcome messages, quoted/injected
  text and unsafe inputs remain explicit unknowns/exclusions with fixed codes.
  Delivery-provider domains and similar brand names do not establish ownership.
- Source IDs and row-based evidence IDs are deterministic for the same ordered
  selection. Primary/duplicate support links retain each selected source instance.
  Exact email byte copies and exact history rows/file copies are deduplicated;
  different paths/times, nonidentical files, Message-ID, or coincident minimized
  features are insufficient. Copies never increase confidence. IDs are batch
  local and can change when input order/subsets change.
- Visits are observed/High source-record evidence. Likely accounts are
  inferred/Medium, marketing inferred/Low, and commercial transactions
  inferred/Medium unless contradictory same-order claims lower them to Low.
  These tiers concern each claim, not a global domain score or probability.
  Additional unknown claims explicitly use state unknown/confidence insufficient
  for sender authenticity, current account, payment completion, retained payment
  credentials, retention and sale where relevant.
- Exact same-domain, case-sensitive order references receive opaque batch-local
  aliases inside the worker. No plaintext reference or stable raw-content hash
  leaves it. Paid and cancelled-before-payment claims for the same alias preserve
  both sources as a conflict, without last-message-wins. c07 is inferred/Low;
  c21 is inferred/Medium unpaid-invoice interaction. Neither asserts completed
  payment or retained credentials. c07 Sensitive and c21 Medium review priority
  are preserved in the oracle but not computed by Phase 3.
- Files/maps live inside a terminated worker; minimized results live only in
  React memory. Completion/error/timeout/clear/consent withdrawal/unmount stop
  processing. No fetch, XHR, sockets, HTML rendering, attachment processing,
  external model, storage or logs are used by discovery. Clearing is transient
  lifetime management, not secure memory erasure or a source-deletion engine.
- No API/schema/migration expansion is necessary. Existing FastAPI/Pydantic
  boundary contracts remain byte-for-byte unchanged and reject graph/features,
  raw bodies, URLs, sender addresses, arbitrary metadata and multipart. The
  browser never calls this endpoint. PostgreSQL is only used for the existing
  disposable scaffold migration check in CI, never imported evidence.

## Read-only oracle validation and measured results

[PHASE3-METRICS.json](PHASE3-METRICS.json) is reproducible with
`npm.cmd --prefix frontend run phase3:metrics`. Oracle SHA-256:
`53b4ff49c5b31e4fa5b2670c757c02058d0ffab3f6b0472fe8d198a86bdd36b1`.
All original raw sources, manifests, proposed review materials, approved 1.1.0,
1.0.0 history, taxonomy record and earlier reports remain unchanged.

| Evaluation | Snapshots | TP | FP | FN | Precision | Recall | Exact in-scope matches |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Initial scenarios | 29 | 28 | 0 | 0 | 1.000 | 1.000 | 29/29 |
| Independently rebuilt survivor sets | 6 | 6 | 0 | 0 | 1.000 | 1.000 | 6/6 |

A discovery item is `(snapshot_id, canonical_domain, relationship_type)`;
TP is the prediction/ground-truth intersection, FP prediction-only, FN
ground-truth-only. Precision = TP/(TP+FP), recall = TP/(TP+FN); zero denominators
produce null, not perfect scores. Snapshots overlap and reuse sources; these
counts are not independent observations or unique-person/company counts.
This is a known synthetic development corpus used to design the rules, not a
holdout set, independent blind review, calibrated probability or product accuracy.

Exact comparison covers domain, relationship type, observed/inferred state,
claim confidence, canonical support, unresolved support, excluded event IDs and
duplicate groups. Tests additionally verify event kinds, eligible source domains,
time status and UTC times, determinism, support
referential integrity, alternate duplicate provenance and absence of raw fields.
Sensitivity/review priority and sensitivity agreement are **unassessed** (null),
not zero or inferred from Phase 1 labels. The original Phase 1 structural metrics
remain historical and unchanged. All six c12 timestamps are strictly excluded.
Six deletion snapshots are read-only survivor-input tests, not a deletion engine.

## Executed validation

Commands run from the indicated directory on Windows, using the locked existing
dependencies. `UV_CACHE_DIR` and `PLAYWRIGHT_BROWSERS_PATH` point to ignored local
caches. Every command below is checked for its own exit status. No dependencies
or lockfiles changed. Final local reruns passed; remote evidence is recorded separately below.
Interim failures and resolutions are disclosed below.

| Directory | Executed command | Result |
| --- | --- | --- |
| `backend/` | `uv run --frozen ruff check .` | PASS |
| `backend/` | `uv run --frozen ruff format --check .` | PASS, 16 files |
| `backend/` | `uv run --frozen mypy` | PASS, 16 source files |
| `backend/` | `uv run --frozen pytest -q` | PASS, 136 tests |
| `backend/` | `uv run --frozen python -m scripts.export_openapi --check` | PASS, original contract unchanged |
| `backend/` | `uv run --frozen python -m scripts.export_phase2 --check` | PASS, strict boundary contract unchanged |
| `backend/` | `uv run --frozen python -m scripts.validate_corpus` | PASS, 29 cases/6 snapshots/27 files/48 events |
| `backend/` | `uv run --frozen pip-audit --cache-dir I:/FootPrint/.cache/pip-audit --progress-spinner off` | PASS, no known vulnerabilities |
| `frontend/` | `npm.cmd run contracts:check` | PASS |
| `frontend/` | `npm.cmd run lint` | PASS |
| `frontend/` | `npm.cmd run typecheck` | PASS |
| `frontend/` | `npm.cmd test` | PASS, 158 tests in 6 files |
| `frontend/` | `npm.cmd run build` | PASS, both isolated workers bundled |
| `frontend/` | `npm.cmd audit --audit-level=low --cache I:/FootPrint/.cache/npm` | PASS, zero vulnerabilities |
| `frontend/` | `npm.cmd run test:smoke` | PASS, 5 Chromium scenarios |
| `frontend/` | `npm.cmd run phase3:metrics` | PASS, 36 oracle/measurement tests; artifact reproduced |
| repository | `.local/phase0-validation/tools/actionlint.exe -shellcheck= -pyflakes= .github/workflows/phase0.yml` | PASS; ShellCheck/Pyflakes integrations disabled |
| repository | `git diff --exit-code d151fe290787079d6cedea1f3c30b30dd7512809 --` followed by corpus, API/migration, generated contracts and original regression paths | PASS before the documented single test-timeout adjustment below |

New coverage includes bounded feature text, malformed/encoded MIME, adversarial
HTML/attachments, claimed-pass/spoofed/conflicting origins, quoted/forwarded and
injection text, exact-copy versus coincident-feature deduplication, distinct
domains/orders, conflicting receipt provenance, unpaid invoices, invalid
URL/time exclusions, altered-byte/wrong-adapter rejection, no I/O/log/storage
calls, worker lifetime and late-message rejection, graph rejection at the API,
real-browser egress and raw sentinel checks. Existing huge-JSON/record/file/MIME
stress tests, generated-contract checks and Phase 0–2 tests remain present.
Browser tests select all 27 approved files in bounded batches; monitor HTTP
URLs/headers/bodies, outgoing WebSocket frames and console output; forbid
nonlocal requests/non-GET requests; verify no raw sentinel egress, rendered
HTML/external links, cookies, browser storage, IndexedDB or service workers.

Development failures resolved: the first leakage assertion matched the legitimate
`synthetic_only` field because its sentinel regex was too broad; it now checks
actual raw sentinels. Type checking found an untyped metrics accumulator. A
Windows helper converted an initial UTF-8 BOM to literal characters; it was
removed and explicit UTF-8 reads/writes used. ESLint found redundant quote escapes.
A new test incorrectly assumed two existing fixtures shared a domain; source
inspection corrected the test and added a separate repeated-claim check. None
of these resolutions changed the corpus, oracle labels, approved hashes or
scope. No failed check is represented as passing before its successful rerun.

## Limitations and exit gates

- Only exact approved synthetic bytes are supported. Narrow English patterns,
  limited MIME subset and ASCII subject cue are deliberately corpus-focused;
  negation, quotation and spoofing handling are incomplete for arbitrary mail.
  Claimed sender identity is never verified. No supported real-user ingestion,
  independent security review or private-beta readiness is claimed.
- Confidence is a deterministic claim tier, not a calibrated score. Contradiction
  matching requires exact domain/reference; missing/different/ambiguous references
  do not establish conflict resolution or payment truth. Import order defines
  transient IDs. No persistent identity, retained evidence or source management.
- No Phase 4 sensitivity engine or Phase 5 dashboard/actions/deletion engine.
  No auth/OAuth, draft personal schema, persistence, external AI/service, real
  personal data or production deployment. Later work requires separate authority.
- Phase 3 exit requires all local and clean-checkout/CI checks, unchanged oracles,
  exact in-scope comparisons, documented limits and an open review PR. These
  implementation/validation gates are met by the evidence below. Human review
  and any later merge remain separate gates. PR #3 must remain unmerged; main
  stays at the pre-Phase-3 base.

## Clean checkout and GitHub CI/Docker evidence

Validated implementation commit: `a9051d535264094308d42cac0094db3698452a41`.
Follow-ups strengthen oracle assertions, align an existing test harness timeout
and record results without changing executable browser/API code. The PR checks tab records checks for the current
review head; this report names the executed implementation runs explicitly.

- [Push run 45123183705](https://github.com/ankit8github/FootPrint/actions/runs/45123183705):
  **SUCCESS**, every job and step.
- [PR run 45123313262](https://github.com/ankit8github/FootPrint/actions/runs/45123313262):
  **SUCCESS**, every job and step.
- Both clean Ubuntu 22.04 runs used Python 3.11.9, Node 22.15.0 and uv 0.9.29,
  locked installs, 136 backend tests, 158 frontend tests, five Chromium scenarios,
  all lint/type/format/contract/corpus/build checks and zero-known-vulnerability
  audits. Decoded job logs confirm counts as well as successful step status.
  No workflow changes, bypasses or skipped check commits were used.
- Docker is unavailable on this Windows host. Actual CI commands passed:
  `docker compose config --quiet`, `docker compose up -d --wait db`,
  `uv run --frozen python -m scripts.check_database` (in `backend/`), and
  `docker compose down --volumes`. The existing check verifies scaffold-only
  upgrade, CHECK constraint enforcement, downgrade and re-upgrade; no personal
  tables or imported observations are installed. Disposable credentials and DB
  exist only for that existing infrastructure test; cleanup passed.

Fresh Windows remote clone (not a copy of the working tree):

```powershell
git -c safe.directory=I:/FootPrint clone --no-hardlinks --branch phase3/synthetic-evidence-linking https://github.com/ankit8github/FootPrint.git I:/FootPrint/.local/phase3-clean-checkout-a9051d5
uv sync --project backend --frozen
npm.cmd ci --prefix frontend --cache I:/FootPrint/.cache/npm
```

From that clone's `backend/`: ruff check/format check, mypy, pytest (136 PASS),
both API export checks and corpus validation passed with the exact commands in
the local table. From its `frontend/`: contracts, lint, typing, all 158 tests,
build and all five Playwright scenarios passed with the commands in the table.
The first unit run had one failure: the existing Phase 2 subprocess contract
test took 5.162 seconds against Vitest's 5-second default. An unchanged complete
rerun passed (158/158; 6.89 seconds total), but a subsequent final-head repeat
took 5.841 seconds and timed out again. This is an intermittent Windows process
startup issue, not solely cold start. The test already permits two Python
subprocesses 30 seconds each; its outer timeout now allows 65 seconds for those
existing bounds plus runner overhead. Only that test's harness timeout changed;
every assertion and fixture is preserved, and the browser worker still terminates
at five seconds. Both implementation Linux CI runs passed on their first attempt.
After alignment, the complete local frontend rerun passed contracts, lint, typing,
158 unit tests, build, zero-vulnerability audit and all five Playwright scenarios.
Final remote harness validation is recorded in PR checks. A Windows console encoding
error initially masked the printed failure; its saved UTF-8 log identified the
timeout and the validation helper now prints UTF-8. Original failure logs are
retained locally, not overwritten by the rerun.

Local tool versions: Python 3.11.9, uv 0.9.29, Node v22.15.0, npm 10.9.2,
Git 2.46.0.windows.1. Ignored execution logs are retained in
`.local/phase3-validation/{backend,frontend,clean-checkout}.json`; public durable
evidence is the linked CI runs and this report. Bundle scanning additionally
passed for raw synthetic sender/recipient, order/invoice and secret sentinels.
Mobile Chromium layout passed without horizontal overflow and its viewport
preview was visually inspected. No UI polish or unrelated refactoring followed.

Preservation check executed from repository root before the test-timeout-only
adjustment (exit 0); all listed paths except that test file remain unchanged:

```powershell
git -c safe.directory=I:/FootPrint diff --exit-code d151fe290787079d6cedea1f3c30b30dd7512809 -- tests/fixtures backend/app backend/migrations backend/tests/test_phase0.py backend/tests/test_phase1_corpus.py backend/tests/test_phase2.py frontend/src/features/imports/parsers.test.ts frontend/src/features/imports/ImportLab.test.tsx frontend/e2e/imports.spec.ts frontend/e2e/smoke.spec.ts frontend/openapi.json frontend/phase2-openapi.json frontend/src/api.generated.ts frontend/src/phase2.generated.ts
```

The report follow-up also ran
`node node_modules/vitest/vitest.mjs run src/features/discovery/oracles.test.ts`
from `frontend/`: 36/36 PASS, including added event-kind/domain/time-status
assertions. CI repeats the full suite for the review head. Corpus 1.1.0 remains
**product-owner-approved, AI-assisted baseline**; independent blind review was not
performed and no reviewer was invented. PR #3 remains open for review; main is
unchanged at `d151fe290787079d6cedea1f3c30b30dd7512809`. No merge SHA exists for
Phase 3, and no deployment, real personal data or later phase work followed.
