# Phase 6A architecture report

Date: 2026-11-24 (Asia/Calcutta). Branch: `phase6a/security-architecture`.
Base: synchronized clean main `3029b0d60213be4d6f9f1951c9e9728d5324461d`, containing
authoritative Phase 5 merge `d0b7e50e7d459ef23e545982104205453fdbe916`.
Status: documentation-only finalization authorized and
[PR #6](https://github.com/ankit8github/FootPrint/pull/6) merged using a merge
commit. **All six new ADRs remain PROPOSED; do not begin Phase 6B.**
The earlier review handoff below is historical; the finalization section records
the later explicit merge authorization and authoritative merge evidence.

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

## Fresh GitHub CI and review delivery

Design commit: `4adee877240b4891c07e3cda18dbf9bc74178dc0` on
`phase6a/security-architecture`, based on the unchanged main SHA above.

| Run/check | Actual result |
| --- | --- |
| [Push CI 45333899161](https://github.com/ankit8github/FootPrint/actions/runs/45333899161) | SUCCESS, every job step completed successfully |
| [PR CI 45334038151](https://github.com/ankit8github/FootPrint/actions/runs/45334038151) | SUCCESS, every job step completed successfully |
| [GitGuardian 138241783758](https://github.com/ankit8github/FootPrint/runs/138241783758) | SUCCESS; not an independent security assessment |

The unchanged workflow ran fresh Ubuntu 22.04 checkouts with pinned Python/Node/uv,
locked installation, Python lint/format/types/150 tests/contracts/corpus/audit,
client contracts/lint/types/284 tests/build/audit, disposable Docker PostgreSQL,
and nine Chromium browser scenarios. The push job log explicitly reports:
`PASS: PostgreSQL upgrade, constraint enforcement, downgrade, re-upgrade; no personal tables.`
This is only the existing scaffold check, not the proposed tenant schema, RLS or
production migration/deletion proof. The >500-kB Vite warning remains unchanged.

Delivery commands actually executed from the repository root include:

```powershell
git -c safe.directory=I:/FootPrint commit -m "docs: propose Phase 6A security architecture and review gates"
git -c safe.directory=I:/FootPrint push -u origin phase6a/security-architecture
python .local/phase6a-validation/delivery.py create-pr
python .local/phase6a-validation/delivery.py ci
python .local/phase6a-validation/delivery.py review-state
```

The GitHub connector returned HTTP 403 for PR creation; the repository's existing
Git credential helper and GitHub REST API created the explicitly requested PR.
Credentials stay in process memory, with no credential output or saved token.
The ignored delivery helper records safe PR/run/job/step metadata. CI status was
verified through GitHub's API, and the push job log was inspected for test counts,
audits and the migration roundtrip. No review approvals are inferred from CI;
at this check there were no submitted reviews or inline review comments.

This report-only follow-up records the successful design-commit evidence above.
Its exact final head and fresh final push/PR check links are recorded in the PR
description after verification, avoiding a self-referential commit hash in this
file. Local documentation/baseline checks are rerun after this report edit.

## Exit and delivery

All four documents, six proposed ADRs, gate matrix and unchanged synthetic baseline
were delivered for product-owner/architecture review in **PR #6**. At the original
handoff, main was unchanged and the feature branch was clean and synchronized.
P5-F01 and P5-F02 remain open future issues.

The original instruction prohibited merging; the later explicit finalization
instruction authorized only verification, a merge commit and this completion
record. It does not authorize production auth/persistence/schema, real inputs,
live integrations, deployment, provisioning or private-beta invitations. Phase 6B
requires a new explicit implementation instruction. Architecture acceptance,
vendor suitability, named owners, legal/retention decisions and independent
security review remain unresolved.

## Authorized finalization — 2026-11-24

The product owner's subsequent instruction explicitly authorized merging the
verified head with existing Git credentials, while keeping all six ADRs PROPOSED
and all unresolved decisions open. Merging the documentation is not implementation
approval, vendor selection approval, legal sign-off or independent assessment.

- Verified PR head: `53f3b27ec158717ec19b4489acce012cb90bf296` (unchanged).
- Verified base main: `3029b0d60213be4d6f9f1951c9e9728d5324461d`.
- Authoritative merge commit: [`756989a1ddc1e6fa108b320bddd16361e3c4a6d9`](https://github.com/ankit8github/FootPrint/commit/756989a1ddc1e6fa108b320bddd16361e3c4a6d9).
- GitHub merge time: `2026-11-24T06:24:46Z`; PR state is closed/merged.
- Merge parents, in order: the verified base and verified PR head above. The
  GitHub API used `merge_method: merge` and the exact expected head SHA, and the
  returned SHA was confirmed against PR metadata and both commit parents. No
  squash or rebase was used.

### Reverified final-head evidence before merge

| Evidence | Reverified result |
| --- | --- |
| [Final push CI 45334424885](https://github.com/ankit8github/FootPrint/actions/runs/45334424885) | SUCCESS, exact expected head; every job and step succeeded |
| [Final PR CI 45334433307](https://github.com/ankit8github/FootPrint/actions/runs/45334433307) | SUCCESS, exact expected head; every job and step succeeded |
| [Final GitGuardian 138243033329](https://github.com/ankit8github/FootPrint/runs/138243033329) | SUCCESS, exact expected head; not independent security review |
| Review/discussion state | Zero submitted reviews, zero inline review comments and zero discussion comments; no blocking review comments |
| GitHub mergeability | `mergeable: true`, `mergeable_state: clean`; PR open, not draft, target main |
| Diff and local checks | Only five expected Markdown paths; local links/fragments, requirements, seven gates, append-only ADR and unchanged baseline checks passed |

Both final CI workflows include the unchanged lint/types/contracts/audits, backend
150 tests, frontend 284 tests, nine browser scenarios and Docker migration checks.
These remain evidence for the synthetic scaffold, not proposed tenant controls.
All check-run conclusions were successful; any legacy commit-status contexts were
also checked for failures. Verification was repeated immediately before merging.

[Post-merge main CI 45340260553](https://github.com/ankit8github/FootPrint/actions/runs/45340260553)
also completed successfully on authoritative merge
`756989a1ddc1e6fa108b320bddd16361e3c4a6d9`, including the Docker migration and
browser steps. Its check run succeeded; no new security controls are inferred.

### Synchronization and preserved scope

Local main was fast-forwarded from the original base to the authoritative merge.
This completion edit changes only this report after the merge. ADR-015–020 are
unchanged and **PROPOSED**. The other three Phase 6A design documents, original
history, application, tests, dependencies, workflow, API contracts, migrations and
immutable corpus remain unchanged. The manifest SHA-256 remains the value recorded
above. The synthetic gate and local transient processing are preserved.

Finalization commands executed from the repository root:

```powershell
git -c safe.directory=I:/FootPrint fetch origin
python .local/phase6a-validation/finalize.py verify
python .local/phase6a-validation/validate_docs.py
python .local/phase6a-validation/finalize.py merge
git -c safe.directory=I:/FootPrint switch main
git -c safe.directory=I:/FootPrint merge --ff-only origin/main
git -c safe.directory=I:/FootPrint show -s --format='%H%n%P%n%s' HEAD
python .local/phase6a-validation/finalize.py ci-current
python .local/phase6a-validation/validate_finalization.py
```

The finalization validator first rejected its own zero-padded ADR identifier
comparison; the ignored checker was corrected without changing any ADR. Its
successful rerun checks merge parents, report-only completion scope, all other
PR files unchanged, all six PROPOSED statuses and the unchanged corpus hash.

The ignored helper uses the existing credential helper in memory and records
safe verification/merge metadata without tokens. No new provider or authentication
configuration is introduced. Final report validation, report-only commit/push and
clean synchronized main verification complete this task; their exact resulting
head is reported in the finalization response rather than embedded in its own
commit. Future performance remediation and real action verification remain open.

Stop after finalization. No Phase 6B, auth implementation, personal-data persistence,
draft personal-data schema installation, provider provisioning, deployment or
real-user processing occurs. Unresolved vendor, ownership, legal, retention and
independent-security-review decisions remain unresolved.
