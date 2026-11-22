# Phase 0 decisions

Date: 2026-11-22. Scope: local scaffold only. These are implementation decisions,
not independent security approval or permission to process personal information.

## ADR-001 — Phase 0 overrides broader MVP P0 priorities

Accepted. Documents 02–05 use P0 for source/feature priorities; document 06 uses
Phase 0 for repository and contracts only. Follow the explicit handoff: no
parsers, fixture corpus/ground truth, discovery, classifier, account integration,
action directory, deletion service, auth implementation, deployment, or real data.
The five pillars remain visibly planned in the shell. Phase 1 has not begun.

## ADR-002 — Review candidate schema without installing personal-data tables

Accepted for the scaffold. `03-pv1-schema.sql` remains unchanged as design input.
The reviewed executable migration `backend/migrations/versions/0001_scaffold.py`
creates only an empty `scaffold_metadata` table, with a primary key and a CHECK
restricting its phase value to `phase0`. Alembic creates its revision table.
Downgrade drops only scaffold metadata. No seeds, extension privileges, users,
observations, or findings are needed to demonstrate migration mechanics.

Review of the candidate DDL:

- Composite owner foreign keys are useful, but do not implement authorization.
- Free text and unrestricted JSON can admit sensitive material; postpone them.
- Placeholder retention is not an enforceable expiry/deletion policy.
- `user_actions.action_id` does not enforce the relationship's organization.
- Cascade deletion alone does not recompute surviving assessments.
- Verified retention/sale/confirmation states need claim-specific evidence gates.
- Migration/app role separation, tenant tests, backup reconciliation, and possible
  RLS remain required before real-user persistence.

Installing the entire candidate now would add unused, insufficiently reviewed
storage. Personal tables require a later explicit schema review and migration.
The local developer DB role owns only this disposable scaffold; the API has no
database driver calls or credentials. It is not a beta application role design.

## ADR-003 — Read-only, versioned, empty contracts

Accepted. `/api/v1/health` reports process liveness, not DB readiness.
`/api/v1/demo` returns API version, synthetic mode, and three empty collections.
Future output types describe minimal observations, evidence links, and separate
assessment dimensions. Collection lengths are constrained to zero in Phase 0.
No request model, raw-file endpoint, metadata bag, user identity field, or
operational processing service is exposed. Retention/sale remain `unknown`;
`confirmed` is excluded. Vocabulary is provisional until later fixture review.
Domain fields are bounded placeholders, not a domain-normalization implementation.

Pydantic generates committed OpenAPI, and openapi-typescript generates client
types. CI checks both for drift. One empty synthetic JSON response is shared by
unit tests; it is not a Phase 1 evidence corpus.

## ADR-004 — Local transport and disposable database

Accepted. Client, API, and PostgreSQL commands bind to loopback. The Vite proxy
forwards `/api` to the local API, avoiding a broad CORS policy. No third-party
scripts, fonts, telemetry, or external model calls are included. CSP allows Vite
development HMR locally. A fresh per-process nonce permits Vite's inline React
refresh preamble; the browser smoke test caught the initial missing nonce.
This is not a production serving configuration or a production nonce policy.
API access logging is disabled in documented start/smoke commands.

`.env.example` has an empty password; README generates a new disposable local
password into ignored `.env`. Only migration tooling reads it. PostgreSQL image
is minor-version pinned; Docker pull/start and image scanning require Docker.
Patch upgrades and dependency audit databases must be rechecked over time.

## ADR-005 — Defer unresolved baseline choices

Document 02 proposes 1 MB/100 email files and 10 MB/50,000 history records;
document 04 proposes 5 MiB/20 files and 20 MiB/10,000 records. Neither is a locked
product requirement. No limit is selected because no parser or ingestion exists.
Resolve with synthetic stress tests before Phase 2, with approval for material
scope/security choices. Exact Chrome nesting, retention values, authentication,
hosting, encryption/backup operations, action ownership and verification remain
open. PRD's `04-threat-model.md` reference points conceptually to the supplied
`04-security-privacy-architecture.md`; no required document is missing.

## ADR-006 — Tooling and verification boundaries

Accepted. Lock direct npm/Python dependencies exactly and commit transitive npm
and uv locks. Use Python 3.11, Node 22, npm 10, and uv 0.9.29 for this baseline.
Normalize the original directory spelling `Docs` to `docs` for Linux CI paths.
At the initial handoff Git had no commit or remote. During Phase 0 validation,
the user supplied `https://github.com/ankit8github/FootPrint.git` for the reviewed
scaffold push and remote CI. See the report for executed commands and outcomes.
No deployment workflow exists.
The first remote run showed that ubuntu-latest now selects Ubuntu 26.04, which
has no setup-python build for the pinned Python 3.11.9. Pin CI to Ubuntu 22.04,
verified in actions/python-versions' manifest, and guard DB cleanup on `.env`
existence when setup fails before database initialization. These are Phase 0
validation fixes, with no product behavior or dependency changes.
The Phase 0 report distinguishes observed local results, native PostgreSQL
fallback checks, local Docker Engine absence, the failed initial CI run, and
the successful Docker-enabled clean-checkout run on Ubuntu 22.04.

Reference checks: [Vite prerequisites](https://vite.dev/guide/),
[FastAPI output contracts](https://fastapi.tiangolo.com/tutorial/response-model/),
[PostgreSQL 17.12 release](https://www.postgresql.org/docs/release/17.12/).
These inform tooling choices; they do not replace local validation.

## ADR-007 — Explicitly authorized Phase 1 artifacts only

The user's subsequent Phase 1 request supersedes the historical Phase 0-only
working scope for this corpus work. Runtime behavior and Phase 0 contracts,
tests, lockfiles, migrations, and CI remain unchanged. The new corpus is under
`tests/fixtures/pv1/v1/`; the only executable addition is offline artifact
validation and its tests, discovered through existing pytest configuration.
The scripts package marker gives mypy a single stable module name for the new
test-helper import. There is no import adapter, parser, normalizer, classifier,
deletion engine, external model call or new API endpoint.

Ground-truth labels are hand-authored proposals with source-byte hashes, literal
evidence anchors, reasons and explicit before/after-deletion snapshots. The
validator checks integrity and references, not the semantic truth of a label.
Independent human adjudication remains pending in the review PR; no fictional
reviewer approval or accuracy metric is invented. Timestamp/sensitivity/source
handling expectations are corpus proposals, not implementation of Phase 2+
policy. Invalid times are annotated null; missing required history time is an
explicit excluded-record case. Existing unresolved parser limits stay open.

The Chrome wrapper and UNIX-microsecond timestamp meaning were checked against
the official source linked in the corpus README. The fixed reference clock
and reserved fictional domains make review reproducible. General `.eml`
ignoring stays in force, with one narrow corpus-directory exception. Scoped
Git attributes preserve fixture hashes across Windows/Linux. Corpus inventory
metrics do not measure product precision/recall or deletion correctness.
