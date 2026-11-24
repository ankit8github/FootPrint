# Phase 6A architecture report

Date: 2026-11-24 (Asia/Calcutta). Branch: `phase6a/security-architecture`.
Base: synchronized clean main `3029b0d60213be4d6f9f1951c9e9728d5324461d`, containing
authoritative Phase 5 merge `d0b7e50e7d459ef23e545982104205453fdbe916`.
Status: architecture and local validation complete; GitHub review delivery is
being recorded. **Proposed for review; do not merge or begin 6B.**

## Deliverables and decisions

- [Security design](PHASE6A-SECURITY-DESIGN.md): requirements S6A-01–14, actual-vs-
  proposed guarantees, explicit local/raw and minimized save boundaries, identity
  comparison, server-derived ownership/RLS, typed relational constraints, consent,
  transactional deletion, restore, keys/logging/incident responsibilities, genuine
  action verification, measured performance plan and independent legal questions.
- [Threat model](PHASE6A-THREAT-MODEL.md): nine boundaries and nineteen explicit
  attack/impact/mitigation/residual-risk/future-test cases TM-01–19.
- [Implementation plan](PHASE6A-IMPLEMENTATION-PLAN.md): thirteen reviewable future
  PR tasks (four 6B, five 6C, four 6D), dependencies, ownership, acceptance tests,
  rollback invariants and stop/go gates. No task is executed by writing the plan.
- Proposed ADR-015–020 appended to [DECISIONS.md](DECISIONS.md); existing ADRs,
  source documents 01–05, draft SQL, Phase 1–5 reports and original evidence remain
  unchanged. [G-S1–G-S7 matrix](PHASE6A-SECURITY-DESIGN.md#10-g-s1g-s7-traceability-and-sign-off)
  maps current evidence, missing controls, accountable roles and verification tasks.

The recommendation is managed Auth0 hosted OIDC plus a same-origin BFF with
server-side opaque cookie sessions, compared with maintained Django auth/session
primitives as a first-party alternative. Provider plan/region/recovery-event
capabilities and protocol client remain review items, not implemented choices.
No custom password system, token-bearing browser storage or production identity
configuration is introduced. New session/consent/role/backup controls remain absent.

The future data model must retain finite feature/context codes, per-copy source
membership and collection-local commercial aliases to recompute meaningfully
without raw files. Server-side business-rule duplication is rejected: propose
shared pure TypeScript cores behind a bounded offline executor. This is a future
6C extraction/adapter task, not a deployed analysis service. Typed schema/RLS and
server consent epochs prevent treating a checked checkbox or client `user_id`
as authorization. The old SQL is a proposal, not installed production DDL.

## Evidence status and unresolved decisions

The implemented exact synthetic SHA-256/adapter gate, browser-local transient
processing, fixed explanations, fictional directory and full survivor recomputation
remain as Phase 5. Existing API `.test`/shape validation is not server provenance
proof; no auth/tenant/persistence controls are claimed. Vite's development CSP and
scaffold CI migrations are not production hardening or tenant isolation.

Historical discrepancies are enumerated in design section 1 rather than rewriting
prior decisions: resource limits reconciled by ADR-010, Phase 5's retained browser
File references, relationship-only draft assessment FK vs unresolved evidence,
unrestricted draft metadata/dedupe/claim states, action-organization integrity and
old proposed server flow. Phase 5 merge supersedes its ADR handoff review status.
Corpus status stays **product-owner-approved, AI-assisted baseline**; no independent
blind review, calibrated confidence, real-world accuracy or compliance is claimed.

Thirty-day derived-data, fourteen-day operational-log and thirty-day backup
periods remain proposals for product/legal review. No final retention schedule
is chosen. Official sources flag staged Indian DPDP commencement and possible
CERT-In reporting/log-retention conflicts; counsel must assess actual applicability
and hosting/processors, not treat this architecture as legal advice. See cited
primary sources in the design, checked 2026-11-24. Auth0/Django/Authlib, OWASP,
PostgreSQL 17, Mermaid and Vite primary documentation were consulted; SDK examples
and vendor capabilities are not independent implementation review.

Named people for ownership/independent review, vendor/region/recovery choices,
retention and deletion-journal policies, server synthetic admission, executor
resource budgets, real directory verification and independent assessment scope
are intentionally unresolved review decisions. “Partial synthetic evidence” in
the gate matrix never closes a real multi-user/privacy operations gate.

## Executed validation

Commands use Windows Python 3.11.9, Node 22.15.0, npm 10.9.2 and uv 0.9.29 with
existing pinned dependencies. Sandbox process startup is unavailable; the working
approved execution path and command-scoped Git ownership exception are used.
No global Git configuration, app dependencies, runtime files, tests or migrations
change. Ignored cache/tool/log paths are under `.cache/` and
`.local/phase6a-validation/`. Exact commands/outputs/independent exit codes are
retained there. Diagram tooling is isolated from the app's package/lock files.

The following commands were actually executed with independent exit-code capture
by `python .local/phase6a-validation/run_checks.py backend` and `frontend` (ignored
one-off orchestration, invoked from repository root). Direct commands run inside
the indicated application directory:

| Directory | Exact executed command | Result |
| --- | --- | --- |
| backend | `uv run --frozen ruff check .` | PASS |
| backend | `uv run --frozen ruff format --check .` | PASS, 18 files |
| backend | `uv run --frozen mypy` | PASS, 18 source files |
| backend | `uv run --frozen pytest -q` | PASS, 150 tests |
| backend | `uv run --frozen python -m scripts.export_openapi --check` | PASS |
| backend | `uv run --frozen python -m scripts.export_phase2 --check` | PASS |
| backend | `uv run --frozen python -m scripts.validate_corpus` | PASS, 29 cases / six survivor snapshots / 27 files / 48 events |
| backend | `uv run --frozen pip-audit --cache-dir I:/FootPrint/.cache/pip-audit --progress-spinner off` | PASS, no known vulnerabilities |
| frontend | `npm.cmd run contracts:check` | PASS |
| frontend | `npm.cmd run lint` | PASS |
| frontend | `npm.cmd run typecheck` | PASS |
| frontend | `npm.cmd test` | PASS, 284 tests / 11 files |
| frontend | `npm.cmd run build` | PASS; unchanged main JS 527.58 kB / gzip 192.99 kB |
| frontend | `npm.cmd audit --audit-level=low --cache I:/FootPrint/.cache/npm` | PASS, zero known vulnerabilities |
| frontend | `npm.cmd run test:smoke` | PASS, nine Chromium scenarios |
| root | `.local/phase0-validation/tools/actionlint.exe -shellcheck= -pyflakes= .github/workflows/phase0.yml` | PASS; optional integrations disabled |
| root | `python .local/phase6a-validation/validate_docs.py` | PASS; local links/fragments, fences, 14 requirements, 19 future tests, 13 tasks, seven gate rows, A–I and FR-01–FR-10 coverage, five diagrams, baseline and append-only ADR checks |
| root | `node .local/phase6a-validation/validate_diagrams.mjs` | PASS, all five Mermaid blocks parsed and rendered with zero external requests |
| root | `git -c safe.directory=I:/FootPrint diff --check` | PASS |

The documentation validator checks **142 original files unchanged**, with the
entire prior DECISIONS text an exact prefix followed only by six proposed ADRs.
The manifest SHA-256 remains
`53b4ff49c5b31e4fa5b2670c757c02058d0ffab3f6b0472fe8d198a86bdd36b1`.
No raw source, oracle, report history, application/test file, API/generated schema,
dependency/lock, migration, Compose or CI workflow is modified. The sole existing
file changed is DECISIONS; four new Phase 6A Markdown files are added.

Diagram validation uses `mermaid@12.3.0`, identified through official npm metadata
then installed only in ignored tooling:

```powershell
npm.cmd view mermaid version dist.integrity --json
npm.cmd install --prefix .local/phase6a-validation/diagram-tools --ignore-scripts --no-audit --save-exact mermaid@12.3.0 --cache I:/FootPrint/.cache/npm
$env:PLAYWRIGHT_BROWSERS_PATH='I:/FootPrint/.cache/ms-playwright'
python .local/phase6a-validation/validate_docs.py
node .local/phase6a-validation/validate_diagrams.mjs
```

The renderer is locally served on ephemeral loopback and uses existing Chromium;
no external Mermaid CDN or app deployment. `mermaid.parse` and `render` both ran
for current/target trust flows, deletion sequence, restore fence and dependency
DAG. SVG/PNG artifacts are in ignored validation output. All five were visually
inspected: labeled boundaries, readable nodes/edges, deletion success vs pending,
offline restore hold and final stop node. Manual semantic review confirms no raw
file→API path, no IdP footprint access and no restore→serving bypass. The identifier
checker cannot prove architectural correctness or replace independent review.
[Mermaid API](https://mermaid.js.org/config/usage.html),
[Vite build documentation](https://vite.dev/guide/build.html).

Initial document validation found shorthand FR references were not individually
traceable; explicit FR IDs corrected this. Diagram rendering was only counted
after the document check and actual parse/render pass. No failed/unexecuted check
is presented as passed. No new future security test was implemented. TM/6B–6D
test cases in the specifications are **not executed tests**, and current
150/284/nine totals prove only the unchanged synthetic baseline. Existing browser
tests still check raw/secret egress, WS frames, console/storage, worker lifecycle,
action state, full survivor recomputation and historical routes.

P5-F01 remains a nonblocking Vite advisory; CI retains its warning and no threshold
or bundle refactor changes. P5-F02 real-world action verification stays open.
Cold-network/CPU lab budgets in the design are proposed future measurements, not
an experiment executed in 6A. Docker is unavailable on this Windows host; any
current Docker result is reported only after actual GitHub CI execution below.

## Exit and delivery

Local documentation, diagram and baseline checks passed. GitHub CI/review PR
details are recorded after delivery. No merge,
production auth/persistence/schema, real inputs, live integrations, deployment or
private-beta invitations authorized. Stop at product-owner/architecture review;
Phase 6B requires a new explicit implementation instruction.
