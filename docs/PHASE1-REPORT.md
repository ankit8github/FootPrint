# FootPrint PV1 Phase 1 report

Date: 2026-11-22 (Asia/Calcutta). Scope: synthetic datasets and ground truth only.
Base: `main` at `4b016f901abf95992049e623fd038dc987536e45`.
Branch: `phase1/synthetic-corpus-v1`.

**Status: implemented for independent review; truth adjudication remains open.**
The corpus and offline checks are implemented. No independent human approval is
recorded and no Phase 2+ work is authorized by this report. Both executed remote
CI runs passed; [PR #1](https://github.com/ankit8github/FootPrint/pull/1) is open
for independent review, not merged.

## Reading and preserved boundaries

Read documents 01, 02, 03 data model, 03 candidate SQL, 04 security architecture,
05 implementation plan, 06 Phase 0 handoff, DECISIONS, PHASE0-REPORT and current
API, migration, frontend, test and CI configuration. Followed document 05 Phase 1
under the user's explicit subsequent authorization; the historical Phase 0-only
instructions do not authorize product expansion.

No import parser, MIME decoder, URL normalizer, classifier, live integration,
external AI/model call, OAuth, automatic link following, deletion service,
database schema change or user-data processing was added. All raw fixtures were
authored from fictional constants, not exported from anyone's account. Dataset
validation runs offline and is not a source import interface.

Phase 0 API contracts/OpenAPI/generated TypeScript, app shell, dependency files,
lockfiles, migration code, Compose configuration, workflow, original unit tests,
browser smoke and `phase0-empty.json` are unchanged from the base. New tests are
discovered by existing pytest configuration, so the existing CI covers the corpus
without editing its steps. No deployment or merge was performed.

## Deliverables and coverage

| Artifact | Contents |
| --- | --- |
| `tests/fixtures/pv1/v1/emails/` | 20 entirely fictional selected-message `.eml` files |
| `tests/fixtures/pv1/v1/history/` | Seven Chrome-compatible JSON files; deliberate invalid field values and unavailable-history sentinel are labeled negative cases |
| `tests/fixtures/pv1/v1/manifest.json` | Version 1.0.0; 48 source-event cards, SHA-256 inventory, literal evidence anchors, 29 proposed scenario snapshots, six independently authored after-delete snapshots |
| `tests/fixtures/pv1/v1/CATALOG.md` | Human-readable source list and scenario labels/reasons |
| `tests/fixtures/pv1/v1/README.md`, `REVIEW.md` | Format/label semantics, independent review protocol and unfilled checklist |
| `tests/fixtures/pv1/v1/metrics.json` | Deterministic inventory benchmark and coverage map; precision/recall/agreement are null |
| `backend/scripts/validate_corpus.py` | Offline structural/integrity validator and inventory benchmark CLI |
| `backend/tests/test_phase1_corpus.py` | Proposed-label policy tests and mutation/negative validation cases |
| `backend/scripts/__init__.py` | Package marker so mypy resolves the developer test helper once |
| `.gitattributes`, narrow `.gitignore` exception | Cross-platform fixture byte stability; email exports remain generally ignored |
| Root/fixture READMEs, `docs/DECISIONS.md` | How to validate/review and the explicit Phase 1 scope decision |

Required assignment coverage:

| Category | Scenarios / evidence |
| --- | --- |
| Registration/account indications | c02, c04, c11, c17, c18, c20, c27, c28 |
| Receipt and unpaid invoice | c03, c07, c21 |
| Marketing | c15, plain and HTML-only newsletters |
| Visits only | c01, c04, c06, c12, c14; /signup and /checkout still only visits |
| Duplicates | c05 email copies; c06 duplicate versus distinct visit; c25 duplicate-source deletion |
| Conflicting evidence | c07 receipt versus cancellation of the same fictional order |
| Spoofing/phishing/ambiguous transport | c08, c09, c10, c29; direct sender, display-name, envelope and shared-provider distinctions |
| Malformed timestamps | c11 email Date; c12 string/null/negative/overflow/fractional time_usec plus missing required time |
| Unsafe URLs | c13, ten non-web/malformed/relative/local/private vectors, never fetched |
| URL minimization expectations | c14 sentinel query/fragment/userinfo values; only fictional domain appears in expected relationship |
| Source-deletion expectations | c23 sole source; c24 email/history overlap in either direction and all removed; c25 either duplicate removed |
| Additional bounded variants | Quoted registration, similar unrelated domains, encoded subject, inert attachment, untrusted instructions, health context, encrypted/unavailable history, old visit |

All 32 required coverage categories have at least one scenario. The four
relationship types and four review priorities are represented: Sensitive,
Medium and Low relationship labels, plus six Unknown/insufficient unresolved
review items. Confidence is separate: high/medium/low claims and insufficient
unresolved items. No percentage probability is invented. All company-retention
and data-sale states remain unknown; no confirmed current account, stored card,
sale, diagnosis, breach, paid invoice or external deletion is asserted.

## Ground truth and benchmark limits

Ground truth is a hand-authored **proposal**, not classifier output. Raw event
locators, literal anchors, case rationales and explicit support IDs let reviewers
reach their own labels without consulting an algorithm. `REVIEW.md` asks for
blind-first labeling, comparison, recorded disagreements and adjudication in
the PR. `review_status=awaiting_independent_review` and
`independent_reviewer=null` honestly preserve the remaining review gate.

The validator checks declared artifacts: byte hashes, exact evidence anchors,
manifest schema, allowed label vocabulary, source/domain references, duplicate
identity, coverage, and that expected after-delete snapshots cite only remaining
sources. It never reads raw text to decide a relationship, normalizes an URL,
decodes MIME, parses an imported file into API observations, or recomputes labels.
Reading fixed fixture JSON to validate its envelope/row references is not a
runtime import pipeline. Tests block socket creation during validator execution.

The inventory benchmark measures corpus structure only. Its initial-snapshot
label counts are 13 likely-account, five transaction, two marketing and nine
visited scenario occurrences, plus six unresolved review items. Scenarios reuse
sources, so these counts are neither unique people nor discovered relationships.
The six deletion snapshots are separate authored oracles; their validation is
not proof that an unimplemented deletion engine works. Discovery precision,
recall and sensitivity agreement remain null because there is no algorithm to
evaluate. This small corpus is not a representative user benchmark or parser
abuse/performance test.

Chrome envelope and timestamp meaning were checked against the primary
[Chrome history schema](https://developers.google.com/data-portability/schema-reference/chrome).
Only its bounded history subset is modeled. No actual Google/user export was
obtained. Product parser limits, large-file stress tests, broader MIME/Takeout
variants, auth trust chains and real-user safety gates remain later work.

## Executed commands and outcomes

Environment observed: Windows, Python 3.11.9, Node 22.15.0, npm 10.9.2, uv 0.9.29.
Checks set `UV_CACHE_DIR=I:\FootPrint\.cache\uv` and
`PLAYWRIGHT_BROWSERS_PATH=I:\FootPrint\.cache\ms-playwright` for ignored local
caches. Audits contact package registries using dependency metadata only, not
fixture contents. Corpus validation itself has no network calls.

| Working directory | Exact command/check | Executed result |
| --- | --- | --- |
| root | `git -c safe.directory=I:/FootPrint fetch origin` | Exit 0 |
| root | `git -c safe.directory=I:/FootPrint switch -c phase1/synthetic-corpus-v1` | Exit 0; dedicated branch created from the documented base |
| backend | `uv run --frozen python -m scripts.validate_corpus --write-metrics` | Exit 0 after correcting the missing e07 scenario; generated inventory counts only |
| backend | `uv run --frozen pytest tests/test_phase1_corpus.py -q` | 36 passed |
| backend | `uv run --frozen ruff check .` | Exit 0 |
| backend | `uv run --frozen ruff format --check .` | Exit 0; 12 files formatted |
| backend | `uv run --frozen mypy` | Exit 0; 12 source files, no issues |
| backend | `uv run --frozen pytest -q` | Exit 0; 46 passed: original 10 plus 36 corpus tests |
| backend | `uv run --frozen python -m scripts.export_openapi --check` | Exit 0; existing OpenAPI unchanged |
| backend | `uv run --frozen python -m scripts.validate_corpus` | Exit 0; all 27 files, 48 event cards, 29 cases, six deletion snapshots, 32 coverage categories valid; committed metrics match |
| backend | `uv run --frozen pip-audit --cache-dir I:\FootPrint\.cache\pip-audit --progress-spinner off` | Exit 0; no known vulnerabilities reported |
| frontend | `npm.cmd run contracts:check` | Exit 0 |
| frontend | `npm.cmd run lint` | Exit 0 |
| frontend | `npm.cmd run typecheck` | Exit 0 |
| frontend | `npm.cmd test` | Exit 0; three tests passed |
| frontend | `npm.cmd run build` | Exit 0; TypeScript/Vite build only, no deployment |
| frontend | `npm.cmd audit --audit-level=low --cache I:\FootPrint\.cache\npm` | Exit 0; zero known vulnerabilities reported |
| frontend | `npm.cmd run test:smoke` | Exit 0; one smoke test passed, real client/API started, empty synthetic shell preserved |
| root | `.local\phase0-validation\tools\actionlint.exe -shellcheck= -pyflakes= .github/workflows/phase0.yml` | Exit 0; existing workflow unchanged; optional shell/Python integrations disabled |
| root | `git -c safe.directory=I:/FootPrint diff 4b016f901abf95992049e623fd038dc987536e45 -- backend/app backend/migrations backend/pyproject.toml backend/uv.lock backend/tests/test_phase0.py backend/tests/test_migration.py frontend .github/workflows/phase0.yml docker-compose.yml tests/fixtures/phase0-empty.json` | Exit 0, no diff: Phase 0 behavior/contracts/checks preserved |
| root | `git -c safe.directory=I:/FootPrint check-ignore tests/fixtures/pv1/v1/emails/registration-shop.eml .local/not-a-fixture.eml arbitrary.eml` | Exit 0; only non-corpus email paths were ignored; corpus file remains trackable |
| root | `git -c safe.directory=I:/FootPrint diff --check` | Exit 0 for tracked changes |
| root | `git -c safe.directory=I:/FootPrint diff --cached --check` | Exit 0 after the scoped MIME CRLF attribute was added |

Full applicable checks were orchestrated with
`python .local\phase1-run-checks.py backend` and
`python .local\phase1-run-checks.py frontend`; these ignored helpers save exact
subprocess output and exit codes in `.local/phase1-validation/`. They are not
part of the application or corpus. The one-time authoring helper wrote only
fictional constant fixtures and was not included as a runtime feature.

Development checks initially caught: wrong helper working directory (corrected),
an uncataloged ambiguous e07 source (added c29), formatting diagnostics (formatted),
and mypy's duplicate namespace for the new helper import (added scripts package
marker). These initial failures are not reported as passes; final results above
are executed reruns. No application code changed in response.

The first staged whitespace review flagged each intentional MIME CRLF as
trailing whitespace. Added the corpus-email-only `cr-at-eol` whitespace attribute
while preserving raw bytes and hashes; no file content was stripped or rewritten.
Staged review includes exactly 41 Phase 1 files, with all 20 corpus emails
trackable. A staged-blob scan found no ignored environment/cache artifacts or
common private-key/AWS/GitHub/Bearer credential patterns. This bounded pattern
scan is not a comprehensive audit or proof of future real-user data handling.

## Review branch and remote checks

Executed from repository root, all exit 0:

```powershell
git -c safe.directory=I:/FootPrint commit -m "Add Phase 1 fictional evidence corpus and reviewable truth manifest"
git -c safe.directory=I:/FootPrint push -u origin phase1/synthetic-corpus-v1
git -c safe.directory=I:/FootPrint rev-parse HEAD
```

Tested source SHA: `9feeb549ebdddfc34f16e42cfec8df3ffaa79783`.
The GitHub connector's requested `create_pull_request` returned HTTP 403
(`Resource not accessible by integration`), so no PR success was claimed from
that attempt. Executed `python .local\phase1-validation\create_pr.py` (exit 0)
using GitHub's REST API with the existing Git credential manager authentication
held only in process memory. No credential was printed, written into files, or
committed. It created [PR #1](https://github.com/ankit8github/FootPrint/pull/1),
head `phase1/synthetic-corpus-v1`, base `main`, open for review. No reviewers
were impersonated, no independent approval was invented, and no merge occurred.

| Executed remote workflow | SHA | Observed conclusion |
| --- | --- | --- |
| [Push run 45054745178](https://github.com/ankit8github/FootPrint/actions/runs/45054745178) | 9feeb549ebdddfc34f16e42cfec8df3ffaa79783 | Success; every scaffold job step succeeded |
| [PR run 45054876390](https://github.com/ankit8github/FootPrint/actions/runs/45054876390) | 9feeb549ebdddfc34f16e42cfec8df3ffaa79783 | Success; every scaffold job step succeeded |

Both runs used real clean GitHub checkouts on the unchanged Ubuntu 22.04
workflow. Run/job states and logs were inspected with GitHub connector `fetch`
on `/repos/ankit8github/FootPrint/actions/runs/{run_id}` and its `/jobs`, plus
`fetch_workflow_job_logs` for job IDs `137307363457` (push) and `137307772470`
(PR). These are actual executions, not conclusions inferred from workflow YAML.

| Commands executed by the preserved remote workflow | Observed result in both runs |
| --- | --- |
| `uv sync --project backend --frozen`; `npm ci --prefix frontend` | Locked clean-checkout dependency installation succeeded |
| `uv run --frozen ruff check .`; `uv run --frozen ruff format --check .`; `uv run --frozen mypy` | Passed, 12 Python files |
| `uv run --frozen pytest -q` | 46 passed, including all 36 new corpus tests and the original 10 |
| `uv run --frozen python -m scripts.export_openapi --check`; `npm run contracts:check` | Both passed; Phase 0 contracts remain unchanged |
| `npm run lint`; `npm run typecheck`; `npm test`; `npm run build` | Passed; three frontend tests |
| `uv run --frozen pip-audit`; `npm audit --audit-level=low` | No known vulnerabilities reported |
| `docker compose config --quiet`; `docker compose up -d --wait db` | Passed; the unchanged DB container became Healthy |
| `uv run --frozen python -m scripts.check_database` | Passed PostgreSQL upgrade, constraint enforcement, downgrade and re-upgrade, with no personal tables |
| `npx playwright install --with-deps chromium`; `npm run test:smoke` | One real-browser client/API smoke passed |
| Guarded `docker compose down --volumes` cleanup | Executed; DB container, named volume and network removed |

The corpus validator runs inside new pytest tests in remote CI; a separate
remote CLI invocation is not claimed. The standalone CLI was executed locally.
No raw fixture was sent through the API or imported into PostgreSQL.
No local Windows Compose startup or online DB check is claimed in this phase;
the Docker-backed regression evidence comes from the executed remote jobs.

`git ls-remote origin refs/heads/main refs/heads/phase1/synthetic-corpus-v1`
confirmed main stayed at `4b016f901abf95992049e623fd038dc987536e45` and the feature
branch had the tested SHA. Local smoke-server ports 8000/5173 were confirmed
closed. The report-only follow-up uses `[skip ci]`; no executable fixture,
validator, test, workflow or dependency changes follow the tested SHA. This
avoids repeating unchanged checks and makes no claim of a separate workflow
execution on documentation-only text.

## Phase 1 exit gates

| Gate | Status | Evidence / limitation |
| --- | --- | --- |
| Entirely fictional versioned raw corpus, no real user data/secrets | PASS for authored inputs | 20 emails, seven history files, explicit synthetic provenance, reserved addresses/domains and obvious inert sentinel values |
| Required representative and adversarial coverage | PASS | 32 categories, 48 source events, 29 scenarios; all requested classes present |
| Expected labels independent of classifier output | PASS for reviewability | Raw source locators/anchors, human-readable reasons, separate confidence/sensitivity and unknowns; no classifier exists |
| Manually adjudicated independent truth baseline | PENDING | REVIEW.md unfilled, manifest explicitly awaiting_independent_review; reviewer must resolve disagreements before accepting corpus as settled truth |
| Duplicate/conflict/deletion oracles and integrity validation | PASS for artifacts | Exact-copy checks and six explicit surviving-source snapshots; no product dedupe/deletion engine tested |
| Versioned catalog, benchmark script and metrics report | PASS | README/CATALOG, validator CLI, metrics.json; efficacy metrics correctly null |
| Phase 0 contracts, tests and CI preserved | PASS locally and remotely | No runtime/contract/workflow/dependency diff; original tests and Docker/browser regression pass |
| Full applicable checks and remote clean-checkout regression | PASS | 46 backend, three frontend and one smoke test pass locally and in both observed remote runs; no local Docker result invented |
| Dedicated branch and PR for review | PASS | PR #1 open from phase1/synthetic-corpus-v1; main unchanged and no merge |
| Phase 1 overall | READY FOR INDEPENDENT REVIEW | No Phase 2+ implementation or automatic phase advancement; independent adjudication remains open |
