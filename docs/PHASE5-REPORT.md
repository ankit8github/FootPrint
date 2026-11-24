# FootPrint PV1 Phase 5 report

Date: 2026-11-24 (Asia/Calcutta). Scope: first integrated browser-local,
synthetic-only MVP. Branch: `phase5/integrated-synthetic-mvp`.
Base: clean synchronized main `20709ccc21fec9c49b0af7c316fdc9a0f1caee96`, whose
parent is Phase 4 merge `f3dd579db4ef87d4adbbb2d771224deba6923133`.
Status: implementation and validation complete; PR #5 open for product-owner /
architecture review. This report follow-up changes documentation only.
Review only: no merge or deployment authorized.

## Architecture and experience

The pre-coding [plan and acceptance checklist](PHASE5-PLAN.md) records the sequence
and gates. ADR-013/014 in [DECISIONS.md](DECISIONS.md) document the design.
`/phase5` integrates consent, selected-file parsing, discovery, assessment,
claim counts/filters, explanations, synthetic action opening and source removal.
Existing `/`, `/phase2`, `/phase3`, `/phase4` remain unchanged.

`LocalSession` owns one ordered list of File references outside React state.
It starts a fresh existing Phase 4 module worker for each selection or removal.
`assessSelectedFiles` reuses the exact Phase 2 SHA-256/adapter gate and bounded
parsers, Phase 3 `relationship_fusion_v1` and Phase 4 `email_context_v1` /
`sensitivity_rules_v1`. None of these engines, versions or rules is changed.
No business logic, label lookup or fixture/case IDs enter the integration.
No backend ingestion, action-state or deletion API, contract or migration added.

React receives only safe source ordinals, minimized results, fixed statuses and
transient opened IDs. The source manager hides filenames/content and distinguishes
identical selected instances. Engine IDs renumber on recomputation; provenance
maps them back to stable selected-source labels. Details reuse fixed explanation,
rationale and limitation maps, separate observed/inferred state, ordinal confidence
and review priority, and preserve all seven unknown claims. Counts describe
claims, not unique companies or people. Priority/type/confidence filters combine;
Unknown and excluded outcomes remain explicit. Findings paginate at 50; provenance
and excluded row indices show up to 200, with complete counts and all supporting
source labels. Loading, failure, empty, filtered-empty and clear outcomes have
accessible status/alert text, named controls and native disclosure details.

## Privacy actions

Two literal `.test` destinations have separate
[source-review records](PHASE5-ACTION-REVIEWS.md). These are reviewed fictional
demonstration entries, not independently verified real-world links or live privacy
controls. Exact domain and relationship type scope each association. Nothing is
derived from email URLs, history paths, inferred organization names or redirects.
Other findings show **No verified direct link available** and manual guidance.

Only explicit native user link activation opens a new tab, with
`noopener noreferrer`. State becomes **opened** (opening requested), never
successful deletion, user-reported completion or verified external response.
No automatic unsubscribe, revoke, delete, network discovery or redirect following.
E2E intercepts the exact fictional destination locally; it contacts no `.test`
host and verifies absent referrer and null opener. No real endpoint pass claimed.

## Removal, recomputation and memory lifecycle

Removal immediately drops the entire old discovery/assessment result and opened
state, terminates in-flight work, and reruns the unchanged engines exclusively
from remaining File references. Exact duplicate alternatives are promoted when
the primary selected copy is removed. Unsupported claims, priorities, rationales,
context, provenance and action associations disappear; no stale mutable graph is
patched. All opened associations reset even if a relationship survives.

Completion, error, messageerror, timeout, supersession, clear, consent withdrawal,
pagehide and unmount terminate workers and clear timers. Worker identity guards
ignore obsolete replies. Failures discard selected references and require a new
selection. Pagehide also withdraws consent to handle back/forward-cache restores.
No main-thread or server parsing fallback exists. Clear-all and withdrawal drop
sources, results and actions; the file input is immediately reset after selection.

File references remain transiently available for recomputation until removed or
cleared. No raw file/text buffers are stored in React state or persistent storage.
Structured cloning may create browser-managed backing-store references/copies;
temporary decoded bytes/text and correlation maps exist inside the bounded worker.
Termination and dropping references are lifetime controls, not guaranteed immediate
GC, secure memory erasure, protection from compromised client JavaScript, or OS
swap/backups erasure. Removal does not delete original disk files, external-company
records or persistent backups. No persistence/backup service is implemented.

## Immutable oracle and security evidence

Corpus 1.1.0 remains **product-owner-approved, AI-assisted baseline**; independent
blind review was not performed. Manifest SHA-256 remains
`53b4ff49c5b31e4fa5b2670c757c02058d0ffab3f6b0472fe8d198a86bdd36b1`.
All 29 scenarios and six deletion snapshots, original files/hashes, archives,
review worksheets and prior metrics/reports are immutable. New session tests
compare all 29 initial cases and perform actual removals for all six survivor
oracles: domain/type, state/confidence, priority/rationales, support, unknown
retention/sale, exclusions and duplicate groups. Additional cases cover both
removal orders for exact email/history copies, reordered paid/cancelled conflicts,
sole clinic-context removal, stale replies, supersession, deadline, safe failures,
invalid association IDs and renderer injection. Known corpus agreement is
development-set evidence, not real-world accuracy or calibrated probabilities.

The exact approved synthetic SHA-256 gate and `.test` restriction are unchanged.
20 files, 1 MiB/email, 10 MiB/batch, 10,000 records, five-second worker deadline,
MIME/JSON depth/header/part/string bounds remain in force. No HTML/attachment
rendering, source logs, raw/minimized upload, external model or real-user data.
New backend tests reject session/action extensions without secret echo/logs and
prove no upload/delete/action API was added. Existing Phase 0–4 regressions run.

Both integrated browser scenarios inspect HTTP URL/header/body content, sent and
received WebSocket frames, console and page errors for raw markers/secret
sentinels. Only local GET development traffic is permitted, except the explicitly
clicked exact synthetic destination intercepted by the test. All 27 approved
sources process in bounded real-worker batches. Altered/arbitrary inputs stay
excluded; oversize selection fails safely without showing filenames/content.
Cookies, local/session storage, IndexedDB and service-worker registrations are
empty; reload/withdrawal/navigation clear results. Worker instrumentation verifies
all created workers terminate after the main import/removal journey. Unit tests
cover in-flight cancellation, the exact deadline, constructor/post/message errors,
late callbacks and unmount without publishing into a disposed React view.

## Executed checks and UX inspection

Windows environment: Python 3.11.9, Node 22.15.0, npm 10.9.2, uv 0.9.29, pinned
existing dependencies. The sandbox fails before process startup; commands use
the working approved execution path and command-scoped Git ownership exception,
without global Git changes. Caches are ignored `.cache/uv`, `.cache/npm`,
`.cache/pip-audit` and `.cache/ms-playwright`. Exact command arrays, independent
exit codes and outputs are kept in ignored `.local/phase5-validation/`.

The initial full working-tree run passed 150 backend / 280 frontend tests and nine
Chromium scenarios. Defensive summary/duplicate-order additions passed the full
frontend rerun (283), then final provenance and post-message cleanup passed 54
focused session/UI tests and both integrated browser scenarios. The fresh remote
checkout at the exact executable commit passed the entire final suite:

| Directory | Executed command | Result |
| --- | --- | --- |
| backend | `uv run --frozen ruff check .` | PASS |
| backend | `uv run --frozen ruff format --check .` | PASS, 18 files |
| backend | `uv run --frozen mypy` | PASS, 18 source files |
| backend | `uv run --frozen pytest -q` | PASS, 150 tests |
| backend | `uv run --frozen python -m scripts.export_openapi --check` | PASS |
| backend | `uv run --frozen python -m scripts.export_phase2 --check` | PASS |
| backend | `uv run --frozen python -m scripts.validate_corpus` | PASS, 29 cases / six snapshots / 27 files / 48 events |
| backend | `uv run --frozen pip-audit --cache-dir I:/FootPrint/.cache/pip-audit --progress-spinner off` | PASS, no known vulnerabilities |
| frontend | `npm.cmd run contracts:check` | PASS |
| frontend | `npm.cmd run lint` | PASS |
| frontend | `npm.cmd run typecheck` | PASS |
| frontend | `npm.cmd test` | PASS, 284 tests / 11 files |
| frontend | `npm.cmd run build` | PASS; main JS 527.58 kB / gzip 192.99 kB |
| frontend | `npm.cmd audit --audit-level=low --cache I:/FootPrint/.cache/npm` | PASS, zero known vulnerabilities |
| frontend | `npm.cmd run test:smoke` | PASS, nine Chromium scenarios |
| root | `.local/phase0-validation/tools/actionlint.exe -shellcheck= -pyflakes= .github/workflows/phase0.yml` | PASS; optional integrations disabled |
| root | `python .local/phase5-validation/preservation.py` | PASS, 127 original paths unchanged; only README, DECISIONS and route selector modified among existing files |
| root | `git diff --check` / staged whitespace check | PASS |

All previous oracle/metrics tests execute in the final frontend suite; no prior
metrics file is rewritten. Production bundle scans find no raw synthetic body,
recipient, order/invoice, attachment, password or URL-secret sentinels. Local
documentation links resolve. No raw selected source content is logged by the app.

Keyboard skip-link focus, named filters, consent gating, disclosure interaction,
opening state, duplicate provenance, survivor labels, filtered-empty outcomes,
and 390-pixel viewport/no horizontal overflow are exercised in Playwright.
Desktop detail and mobile survivor screenshots were visually inspected for
readable hierarchy, stacked controls, wrapped safe provenance and clear Unknown /
external-deletion limitations. They are synthetic only:

- [Desktop explanation and opened state](images/phase5-desktop-detail.png)
- [Mobile remaining-source findings](images/phase5-mobile-survivor.png)

Development corrections: TypeScript caught Worker error-handler variance; lint
caught a render-time ref read. Tests caught an incorrect expectation that a
disposed controller publishes into an unmounted view, and the browser caught
ambiguous filter label names. Types/callback usage and accessible names were
corrected without changing engines or labels. No failed run is counted as pass.

## Limitations and exit gates

- Synthetic exact-byte selection only. Narrow English/MIME/context patterns and
  known overlapping examples are not general-purpose imports or user evaluation.
- Priority, claim confidence and evidence state remain independent; current
  account, payment completion, credential retention, retention, sale and breach
  remain unknown. No sensitive personal attributes or current company records.
- `.test` links are fictional and ordinarily unavailable; opening is not completion.
  Link review is AI-assisted source review, not independent human/live verification.
- Browser memory is transient, not securely erased. Five seconds bounds worker
  processing rather than UI latency or guaranteed hardware performance.
- Existing Vite main-chunk size concern remains nonblocking and tracked; no
  unrelated refactor, dependency update or warning-threshold change.
- No public deployment, real data, auth/tenancy, personal persistence, external
  AI, general upload, auto-action or Phase 6. Beta security/operations gates remain
  future work. This is no independent security audit or compliance certification.
- Exit requires complete local/fresh-checkout checks, actual successful GitHub
  CI including Docker migration roundtrip, preservation and a review PR with exact
  head/CI evidence. Product-owner/architecture review and merge remain separate.

## Fresh checkout, GitHub CI and delivery

Executable implementation commit: `b6cd0aefd262a950af768be29941abc8c288cf05`.
Both complete clean Ubuntu 22.04 GitHub runs passed every job and step:

- [Push CI 45327472455](https://github.com/ankit8github/FootPrint/actions/runs/45327472455): **SUCCESS**.
- [PR CI 45327652362](https://github.com/ankit8github/FootPrint/actions/runs/45327652362): **SUCCESS**.

Decoded logs independently confirm 150 backend tests, 284 frontend tests, nine
Chromium scenarios, zero-known-vulnerability npm/pip audits, and
`PASS: PostgreSQL upgrade, constraint enforcement, downgrade, re-upgrade; no personal tables.`
Locked installs, contracts, lint/format/types, corpus, build, database cleanup
and post-job cleanup all succeeded. Actual CI executes:

```text
docker compose config --quiet
docker compose up -d --wait db
uv run --frozen python -m scripts.check_database  # backend/
docker compose down --volumes
```

Docker is unavailable on the Windows host; no local Docker pass is claimed.
Only the original disposable scaffold tables/migration are exercised; no
personal-data schema is installed. CI retains the existing Vite >500-kB advisory
with the passing build. The 527.58-kB main bundle is a nonblocking performance
concern for later review, without threshold changes or unrelated refactoring.

A separate fresh Windows remote clone at the exact executable commit also passed
all 18 install/check commands independently, with no environment file, virtualenv,
node_modules or source copied from the working tree:

```powershell
git -c safe.directory=I:/FootPrint clone --no-hardlinks --branch phase5/integrated-synthetic-mvp https://github.com/ankit8github/FootPrint.git I:/FootPrint/.local/phase5-clean-checkout-b6cd0aef
uv sync --project backend --frozen
npm.cmd ci --prefix frontend --cache I:/FootPrint/.cache/npm
```

The remaining commands are the backend/frontend table above, including both
audits and all nine browser scenarios. Full arrays, outputs and exit codes are in
`.local/phase5-validation/clean-checkout.json`. The unchanged 65-second test-only
cross-language harness bound remains separate from the five-second production
worker deadline. Fresh checkout and both CI runs passed on first execution.

[PR #5](https://github.com/ankit8github/FootPrint/pull/5) targets main and is open,
unmerged. The GitHub connector could read but returned integration permission
denied for PR creation; the authorized creation used the repository's existing
Git credential helper. Credentials remained in memory, never logged or saved.
No app permissions were changed. No review comments/threads were present at the
implementation evidence check; no independent human review is claimed.

This final documentation-only follow-up records completed evidence and the
acceptance checklist. Final-head check links and exact review head are maintained
in the PR description and delivery response, avoiding a self-referential commit
hash inside its own report. Main remains unchanged at the base SHA above.
No merge, deployment, real-user data or Phase 6 work performed. Stop for review.
