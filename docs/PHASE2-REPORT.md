# FootPrint PV1 Phase 2 report

Date: 2026-11-23 (Asia/Calcutta). Scope: safe synthetic-only import pipeline.
Branch: `phase2/local-synthetic-import`, based on updated main at Phase 1 merge
`f0d7974e620e5d11b5fa923669a47a6afa97e5e3`.
Status: implementation complete; final validation and review PR publication underway.
No merge, deployment, real-user data or later phase is authorized.

## Implemented behavior and data flow

The separate `/phase2` browser view accepts explicit selection of `.eml` and Chrome
JSON. Raw bytes are read only inside a module worker after file/batch size checks;
SHA-256 is compared to the exact approved corpus 1.1.0 registry before any adapter
runs. Unknown/modified files fail closed. Registry entries contain IDs, adapters
and hashes only, not raw fixtures or ground-truth relationship labels. Files from
other sources cannot be processed merely by adding a synthetic header or checkbox.
The actual application/test work used only fictional fixtures and generated text.

Versioned adapters `email_eml_v1` and `browser_chrome_json_v1` return allowlisted
records, safe issue codes and random per-selected-file source IDs plus row indices.
Nothing is uploaded, persisted or used for an account/relationship/priority claim.
Results live in React memory; workers terminate on completion/error, five-second
deadline, clear, consent withdrawal or unmount. Selection is cleared immediately.
The UI displays at most 200 rows, with counts for all bounded rows; clearing the
transient view is not a database or dependent-deletion engine.

MIME supports a deliberately small CRLF/plain-text/multipart mixed/alternative
subset with folding, base64/quoted-printable validation and restricted charsets.
Raw bytes must decode as UTF-8. Subject/display names/Message-ID and raw or decoded
text are discarded. No HTML rendering or DOM conversion occurs: HTML-only content
is unresolved. Attachment headers are inspected only to skip the part before
payload interpretation/decoding. Encoded attachment payload is never processed.
Unsupported charsets, malformed headers/multipart and message/rfc822 fail safely.
Email output is unclassified record evidence with unverified sender origin;
contradictory transport/authentication headers yield unresolved records. Claimed
authentication headers never establish sender authenticity or organization identity.

The pinned `tldts` 7.5.5 dependency uses bundled ICANN and PRIVATE public-suffix data.
The [primary library documentation](https://github.com/remusao/tldts/tree/master/packages/tldts)
describes its domain and private-suffix options. No DNS or suffix/network fetches
occur. Strict host/authority validation rejects malformed, IP/private/local and
non-web inputs; import output is further restricted to reserved `.test` domains.
Only registrable domain survives; URL path, query, fragment, port and userinfo are
omitted. Chrome time_usec must be a nonnegative safe integer within 1970-2100;
UTC output retains microseconds. All six c12 invalid/missing times are excluded.
Malformed/missing email Date yields null with an explicit time status, as in c11.
Only exact raw history rows deduplicate within the same source. Distinct URL/time
rows and separately selected copies retain separate provenance. No cross-source
fingerprint, fusion, relationship inference or confidence adjustment is produced.

## Resource and API boundary decisions

ADR-010 in [DECISIONS.md](DECISIONS.md) reconciles documents 02 and 04 under the
user's explicit authority to make and document this choice:

| Bound | Enforced value |
| --- | --- |
| Email / combined file bytes | 1 MiB per email / 10 MiB total |
| Files / aggregate records | 20 / 10,000, including issue and duplicate rows |
| Worker lifetime | Five seconds per batch; termination instead of main-thread fallback |
| JSON structural budgets | Depth eight, 16,384-character strings, two-million-step lexical budget |
| MIME structural budgets | 16 entities, four nested multipart levels, 16,384-character headers, 998-character physical header lines |
| API bytes / sources / records | 8 MiB actual request bytes / 20 / 10,000 aggregate |

Byte units are explicitly binary MiB. A file within byte limits may still fail a
structural/encoding/record budget. Whole-file parsing is bounded, not a general
streaming mailbox implementation or a production throughput guarantee.

`POST /api/v1/phase2/validate` is a separate mounted FastAPI/Pydantic boundary with
its own generated OpenAPI/TypeScript. It validates only structured observations
and issue/provenance records, returning a count. It has no database/service calls
or logging. It rejects multipart/non-JSON before parsing, limits streamed bytes,
rejects duplicate/prototype JSON keys and non-JSON constants, forbids extra fields
at every model level, checks strict types/codes/canonical domains/valid UTC times,
and enforces source and duplicate-reference consistency. Raw bodies, addresses,
subjects, filenames, URLs, arbitrary metadata and excerpts are not contract fields.
All validation errors are static codes without Pydantic input/details or body echo.
The UI never calls this endpoint, including for minimized records. A caller's
synthetic-only flag is not authentication or proof of source provenance; this is
loopback synthetic-demo infrastructure, not a real-user endpoint.

## Preserved Phase 0/1 baseline

The original `/` demo and health/demo responses remain empty, and its original
OpenAPI/client contract and tests are unchanged. The only runtime integration is
a separate import view and mounted normalized validation boundary. The original
Phase 1 manifest/metrics/raw evidence/catalog/review materials, all 29 scenarios
and six deletion snapshots are untouched, as are backend dependencies, migration,
Compose and the candidate SQL. No personal-data tables are created.
The Phase 1 status remains **product-owner-approved, AI-assisted baseline**;
independent blind human review is not claimed. Parser tests are syntax/safety
checks, not predictions of the Phase 1 relationship/sensitivity labels. Corpus
precision, recall and sensitivity agreement remain null. The preserved Phase 1
metrics runtime-parser flag describes the historical Phase 1 artifact baseline;
it is not a capability flag for the new Phase 2 browser implementation.

## Executed validation

Environment: Windows, Python 3.11.9, Node 22.15.0, npm 10.9.2, uv 0.9.29.
The existing Windows sandbox cannot start processes; approved command execution
uses the working shell fallback and command-scoped Git safe.directory only.
Caches: `UV_CACHE_DIR=I:\FootPrint\.cache\uv`,
`PLAYWRIGHT_BROWSERS_PATH=I:\FootPrint\.cache\ms-playwright`; dependency audits
contact registries using package metadata only. No fixture is sent to an API/model.
Local commands completed successfully:

| Directory | Exact executed commands/check | Outcome |
| --- | --- | --- |
| root | `npm.cmd install --save-exact tldts --prefix frontend --cache I:/FootPrint/.cache/npm` | PASS; pins 7.5.5, already present transitively; no unrelated dependency updates |
| backend | `uv run --frozen ruff check .`; `uv run --frozen ruff format --check .`; `uv run --frozen mypy` | PASS; 15 source files, no issues |
| backend | `uv run --frozen pytest -q` | PASS; 128 tests: original 76 plus 52 Phase 2 boundary tests |
| backend | `uv run --frozen python -m scripts.validate_corpus` | PASS; unchanged 1.1.0, all 29 cases/six snapshots, hashes and metrics |
| backend | `uv run --frozen python -m scripts.export_openapi --check`; `uv run --frozen python -m scripts.export_phase2 --check` | PASS; original contract unchanged, new contract current |
| backend | `uv run --frozen pip-audit --cache-dir I:\FootPrint\.cache\pip-audit --progress-spinner off` | PASS; no known vulnerabilities |
| frontend | `npm.cmd run contracts:check`; `npm.cmd run lint`; `npm.cmd run typecheck` | PASS; original and new generated clients current |
| frontend | `npm.cmd test` | PASS; 91 tests, including every corpus adapter output validated directly by Pydantic through local stdin |
| frontend | `npm.cmd run build` | PASS; Vite/TypeScript including a separate bundled worker; no deployment |
| frontend | `npm.cmd audit --audit-level=low --cache I:\FootPrint\.cache\npm` | PASS; zero known vulnerabilities |
| frontend | `npm.cmd run test:smoke` | PASS; three Playwright scenarios, including unchanged Phase 0 smoke and two real-worker import tests |
| root | `.local/phase0-validation/tools/actionlint.exe -shellcheck= -pyflakes= .github/workflows/phase0.yml` | PASS; optional integrations disabled |
| root | `git diff --check`, documentation local-link check and preservation diff against f0d7974 | PASS; original Phase 0/1 tests/contracts/corpus/migrations/Compose/report preserved |

Ignored orchestration `python .local/phase2-run-checks.py backend` and `frontend`
saved command arrays, exit codes, elapsed time and exact stdout/stderr under
`.local/phase2-validation/`. After adding the cross-language/unmount test coverage,
frontend lint/typecheck/unit tests were rerun successfully (91 tests). Security
checks include API body/log non-disclosure, forbidden raw fields at four nesting
levels, multipart rejection, actual streamed-byte limits, duplicate/prototype keys,
invalid UTC/domain/type values and provenance/duplicate constraints. Parser tests
cover spoofed origin, inert injection/HTML, ignored invalid attachment payloads,
encoded plain text/subject, malformed MIME, unsafe URLs, all c12 values, exact-row
deduplication, 200 deterministic malformed samples and synthetic resource limits.

Playwright intercepts context requests, restricts methods/hosts, checks request
URLs/headers/bodies and WebSocket frames for raw content/sentinel leakage, observes
console/page errors, processes all 27 approved sources and rejects arbitrary or
oversized bytes. It verifies no cookies, local/session storage, IndexedDB or service
workers remain. Injection content creates no images/frames/forms or outbound
requests. A 390px viewport screenshot was visually inspected; the bounded table
scrolls horizontally without page overflow. Clear and reload remove transient data.
Worker timeout/cancel/unmount behavior is separately covered with controlled timers.

The first development run exposed strict UUID parsing at FastAPI's Python boundary,
malformed-host normalization and parser lint/test formatting errors. These were
fixed before the final full checks. No ground-truth expectation was changed to fit
parser results, and no product accuracy or independent security review is claimed.
A local Docker executable/engine is unavailable (`Get-Command docker` found none).
Docker startup/migration/cleanup is verified in clean-checkout GitHub CI instead;
no local Docker pass is invented. Clean-checkout and remote results follow in the
completion evidence added after those runs finish.

## Limitations and exit gates

No general RFC-complete mail parsing, arbitrary Takeout variants, HTML extraction,
cryptographic sender verification or production memory/performance claim. The
synthetic hash gate deliberately restricts the usable UI to the approved corpus;
new fictional samples require an explicitly reviewed registry update. Non-synthetic
host normalization is tested with invented strings, but actual imports and API
observations remain `.test` only. Pinned public-suffix data requires maintenance.
Five-second execution protects responsiveness; it is not a semantic security audit.

No persistence, PostgreSQL observation writes, auth/tenancy, discovery/fusion,
sensitivity/confidence rules, action links, live OAuth, external model calls or
deletion/recomputation engine exists. Production rate limiting, real-user consent,
auth, retention, operational security, supported export expansion and independent
security review remain later explicit gates. Synthetic testing does not establish
private-beta readiness or complete the MVP. This phase ends with an open PR for
review, never a merge or deployment.
