# FootPrint PV1 Phase 1 report

Date: 2026-11-23 (Asia/Calcutta). Scope: fictional datasets and ground truth only.
Status: **product-owner-approved, AI-assisted baseline**, corpus **1.1.0**.
PR: [#1](https://github.com/ankit8github/FootPrint/pull/1), existing branch
`phase1/synthetic-corpus-v1`, base `main` at
`4b016f901abf95992049e623fd038dc987536e45`.

The product owner explicitly authorized the taxonomy decisions and conditional
merge after validation. The AI assistant applied the decisions and inspected the
fictional raw sources, all 29 cases and six independent deletion setups. No
independent blind human review was performed; `independent_reviewer` remains null.
This baseline closes the product-owner-approved Phase 1 artifact scope without
claiming the original independent-review gate was fulfilled in that form.

## Decisions and resulting behavior

| Item | Approved baseline |
| --- | --- |
| Transaction meaning | Evidence of a financial/commercial interaction; name the interaction. It does not prove completed payment or retained credentials. |
| c07 | Transaction, Sensitive review / Low confidence. The receipt says paid; the correction says cancelled before payment. These contradictory payment claims remain explicit; neither resolves actual payment. |
| c12 | All six invalid/missing browser-history timestamps excluded under strict MVP P0 validation. String, null, negative, overflow, fractional and missing values yield no relationship; annotated event times remain null. |
| c21 | Unpaid invoice, transaction, Medium review / Medium confidence. No payment, successful purchase or retained payment credentials asserted. |
| Other cases and deletions | Remaining 26 cases and all six deletion snapshots retained. Surviving claims cite surviving evidence only; duplicates do not increase confidence. |

[Accepted taxonomy decision](PHASE1-TAXONOMY-DECISION.md) records authority,
reasoning, all six deletion outcomes and version compatibility. ADR-009 supersedes
the historical proposed ADR-008 and affected guidance in the earlier artifact work.
Document 03 now distinguishes strict browser-history validation from c11's
malformed email Date, which remains an account indication with null event time.

## Deliverables, metrics and preserved history

The updated manifest, validator, tests, catalog, guides, deterministic metrics,
data-model clarification and decision record agree on baseline 1.1.0. The validator
pins its exact status and approval provenance, forbids a fabricated independent
reviewer, and rejects eligible browser-history annotations with invalid/missing
timestamps. It still validates authored artifacts rather than deriving labels.

| Inventory / initial labels | Result |
| --- | --- |
| Raw files / events | 27 / 48: 20 emails and seven history files |
| Cases / deletion snapshots / coverage categories | 29 / 6 / 32 |
| Event dispositions | 24 eligible, 18 excluded, six unresolved |
| Relationship occurrences | 13 likely-account, five transaction, two marketing, eight visited |
| Review priority | Five Sensitive, 13 Medium, ten Low; six separate Unknown unresolved items |
| Confidence | Eight High, 17 Medium, three Low; six separate insufficient unresolved items |
| Discovery precision / recall / sensitivity agreement | All null; no parser/classifier exists |

Counts are scenario occurrences, not distinct users or discovered relationships.
Coverage tags include negative fixtures: c12's visits-only source tag does not
indicate that its excluded rows establish a visit. Deletion labels are counted
separately. Retention and data-sale states remain unknown throughout.

[Archive](../tests/fixtures/pv1/v1/archive/README.md) preserves proposal 1.0.0's
manifest, metrics, catalog, guide and original report. Original REVIEW.md,
HUMAN-REVIEW-WORKSHEET.md and PHASE1-TAXONOMY-PROPOSAL.md remain unchanged and
unfilled. Their pending/proposed statements are historical, not the current
approval status. Full prior state and original tooling remain in commit
`8afdacdb9b3a3011eb4944c743bd5a1e3e923cc5`. No Git history is rewritten.
All 27 original raw files, SHA-256 hashes, event IDs, locators and anchors are
unchanged. Original email `corpus=1.0.0` markers record raw-source provenance.

## Executed local validation

Windows; Python 3.11.9, Node 22.15.0, npm 10.9.2 and uv 0.9.29. Local cache paths:
`UV_CACHE_DIR=I:\FootPrint\.cache\uv` and
`PLAYWRIGHT_BROWSERS_PATH=I:\FootPrint\.cache\ms-playwright`.
The Windows sandbox failed before process startup; repository commands used the
approved shell fallback and command-scoped Git safe.directory. No machine-wide
Git safety configuration was changed.

| Directory | Executed commands/checks | Result |
| --- | --- | --- |
| backend | `uv run --frozen ruff check .`; `uv run --frozen ruff format --check .`; `uv run --frozen mypy` | PASS; 12 files formatted, no typing issues |
| backend | `uv run --frozen pytest -q` | PASS; 76 tests (original ten plus 66 corpus tests) |
| backend | `uv run --frozen python -m scripts.validate_corpus` | PASS; all 29 cases, six deletion snapshots, raw hashes, coverage and committed metrics |
| backend | `uv run --frozen python -m scripts.export_openapi --check` | PASS; existing contract unchanged |
| backend | `uv run --frozen pip-audit --cache-dir I:\FootPrint\.cache\pip-audit --progress-spinner off` | PASS; no known vulnerabilities found |
| frontend | `npm.cmd run contracts:check`; `npm.cmd run lint`; `npm.cmd run typecheck` | PASS |
| frontend | `npm.cmd test`; `npm.cmd run build` | PASS; three tests, TypeScript/Vite build |
| frontend | `npm.cmd audit --audit-level=low --cache I:\FootPrint\.cache\npm` | PASS; zero known vulnerabilities |
| frontend | `npm.cmd run test:smoke` | PASS; one Playwright test using real local API/client, empty synthetic mode, keyboard/mobile checks, no external browser requests or errors |
| root | `.local/phase0-validation/tools/actionlint.exe -shellcheck= -pyflakes= .github/workflows/phase0.yml` | PASS; optional integrations disabled |
| root | Preservation comparison against 8afdacd | PASS; original review documents, archived proposal/report, all 27 raw source bytes and hashes preserved |
| root | Phase 0 runtime/contract/dependency/workflow/migration diff against 4b016f9 | PASS; no diff |
| root | `git diff --check` and staged whitespace check | PASS |

Ignored orchestration `.local/phase1-run-checks.py` saves exact outputs in
`.local/phase1-validation/backend.json` and `frontend.json`. New tests cover all
29 policy expectations, six deletion dimensions/support sets, all six invalid-time
promotion mutations, explicit payment boundaries, rejection of invented review
claims and preservation of unchanged case/deletion history. The first local typing
check caught three chained empty-list assertions; they were corrected and the
complete backend suite rerun successfully. No expectation was changed to fit a
classifier. Corpus validation remains offline, including a socket-blocking test.
Security regression checks retain read-only endpoints, rejected uploads/hosts,
unknown retention/sale claims and loopback-only browser traffic.

## GitHub CI and completion record

Both GitHub CI runs completed successfully for tested source commit
`c493d1773038cb1d240f8340cc04699680a0197c`:

- [Push CI 45112506429](https://github.com/ankit8github/FootPrint/actions/runs/45112506429): SUCCESS.
- [PR CI 45112512337](https://github.com/ankit8github/FootPrint/actions/runs/45112512337): SUCCESS.

Observed successful steps include locked dependency installation, Python and
client checks (including audits), disposable Docker database startup and migration
roundtrip, Playwright browser smoke, database cleanup and post-job cleanup. Local
Docker execution is not claimed. This report-only follow-up changes no executable
artifact and deliberately allows CI to run again; the final head's successful
checks are verified before merge.

The final completion record is [PR #1](https://github.com/ankit8github/FootPrint/pull/1):
its merged metadata provides the authoritative merge SHA. The SHA and final-head
CI run links are recorded in the PR description and delivered final report after
GitHub confirms the merge. A merge commit retains all prior commits; no squash,
rebase or branch deletion is used. No merge is inferred from a pre-merge test SHA.

## Boundaries and exit status

Phase 1 artifact gates pass locally: fictional inventory, approved authored
baseline, explicit uncertainty, coverage, duplicate/conflict/deletion oracles,
version preservation, deterministic metrics and unchanged Phase 0 behavior.
Remote clean-checkout validation also passed, including Docker and browser checks.
Phase 1 baseline work is complete under the product owner's explicit approval
basis. Publication follows the authorized merge procedure above. Independent blind
human review was not performed; no reviewer identity or independent attestation
is claimed.

No Phase 2 parser, classifier, normalizer, source importer, deletion engine,
OAuth, external integration, model service, schema expansion, deployment or
real-user data processing was implemented. The app/API remain the Phase 0 empty
synthetic shell. Small fictional corpus checks do not establish production safety,
algorithm accuracy, real-world retention/sale or external deletion correctness.
The final action is the authorized merge after successful final-head CI, followed
by recording its SHA and delivering this report. Work stops at Phase 1.
