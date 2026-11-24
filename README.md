# PV1 — Phase 0 local scaffold

Personal Digital Footprint & Privacy Intelligence: Discover, Analyze, Classify,
Visualize, Control. **Synthetic demo only. Do not import personal records, expose
these servers publicly, or treat this as a completed MVP.**

The browser displays planned pillars and an empty state. It requests only
`GET /api/v1/demo` through a local Vite proxy. FastAPI returns empty typed
collections; `GET /api/v1/health` reports process liveness. The HTTP app does not
connect to PostgreSQL. Database access is limited to explicit migration commands,
which create only scaffold metadata and Alembic's version table.

## Prerequisites

- Windows PowerShell and VS Code (open this folder with `code .`).
- Python 3.11 (validated with 3.11.9), Node 22.15.0 / npm 10.9.2.
- uv 0.9.29 on PATH. No virtual-environment activation is necessary.
- Docker Desktop running Linux containers, with Docker Compose v2 supporting
  `up --wait`. Installation/startup is a developer prerequisite, not automated here.
- Internet access for the first locked dependency/image/browser downloads.

Use only newly generated, disposable local database credentials. No external API
credentials, mail accounts, OAuth permissions, or real data are required.
See [decisions](docs/DECISIONS.md) and [verification report](docs/PHASE0-REPORT.md).

## Clean checkout setup (PowerShell, repository root)

If `.env` does not exist, create it once:

```powershell
python -c "from pathlib import Path; import secrets; p=Path('.env'); assert not p.exists(), '.env already exists'; p.write_text('POSTGRES_PASSWORD='+secrets.token_hex(24)+'\nPOSTGRES_PORT=55432\n', encoding='utf-8')"
uv sync --project backend --frozen
npm.cmd ci --prefix frontend
docker compose config --quiet
docker compose up -d --wait db
Push-Location backend
uv run --frozen alembic upgrade head
uv run --frozen alembic current
Pop-Location
```

`.env.example` documents the two supported variables. Compose and migration
tooling read root `.env`; the HTTP server does not need it. The DB listens only
on `127.0.0.1:55432`. Never use `docker compose config` without `--quiet` in shared
logs because expanded configuration contains the disposable password.

## Start and stop in VS Code

Open two integrated PowerShell terminals. In the first, from repository root:

```powershell
Set-Location backend
uv run --frozen python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

In the second, from repository root:

```powershell
Set-Location frontend
npm.cmd run dev
```

Open `http://127.0.0.1:5173`. The status should say
“Local API connected · empty demo contract”. Test health separately with:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

Press Ctrl+C in each terminal to stop the client and API. From repository root,
`docker compose down` stops the DB and preserves its local volume. To discard
**this project's disposable local DB**, use `docker compose down --volumes`.
Changing `.env`'s password does not update an already initialized volume; use a
fresh disposable volume when changing that password. No production setup exists.

VS Code can use `backend/.venv/Scripts/python.exe` as its Python interpreter.
If ports 8000, 5173, or 55432 are busy, stop the conflicting local process before
running checks; the smoke test deliberately refuses to reuse existing servers.
If a managed environment blocks the default uv cache, set `$env:UV_CACHE_DIR`
to a writable local directory before running uv and Playwright.

## Run checks

In `backend/`:

```powershell
uv sync --frozen
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy
uv run --frozen pytest -q
uv run --frozen python -m scripts.export_openapi --check
uv run --frozen pip-audit
```

In `frontend/`:

```powershell
npm.cmd ci
npm.cmd run contracts:check
npm.cmd run lint
npm.cmd run typecheck
npm.cmd test
npm.cmd run build
npm.cmd audit --audit-level=low
npx.cmd playwright install chromium
npm.cmd run test:smoke
```

Stop manually started API/client processes first. Playwright starts and stops
its own API and Vite server, checks real health and proxy connectivity, synthetic
labels, no file picker, keyboard skip link, narrow viewport, browser errors, and
browser HTTP requests staying on loopback. It uses no DB and no source records.

With the disposable local DB running, from `backend/`:

```powershell
uv run --frozen python -m scripts.check_database
```

This checks upgrade, the phase CHECK constraint, downgrade, and re-upgrade. It
refuses databases containing tables other than the two Phase 0 scaffold tables.
It removes/recreates only scaffold metadata, and leaves the DB at migration head.
Unit tests also compile migration upgrade/downgrade SQL without a DB.

On Linux/macOS, use the same commands with `npm`/`npx` instead of `.cmd`, normal
`cd` instead of PowerShell location commands, and `npx playwright install
--with-deps chromium` on a fresh CI machine. CI performs these checks and the
Compose migration roundtrip; a workflow file is not evidence that CI has run.

## Update contracts deliberately

After changing Pydantic output models, from `backend/` run
`uv run --frozen python -m scripts.export_openapi`, then from `frontend/` run
`npm.cmd run contracts:generate`. Commit `openapi.json` and `src/api.generated.ts`
with the model change. Contract checks detect stale generated files. These are
provisional read-only output types, not an approved future ingestion schema.

## Layout and boundaries

| Path | Responsibility |
| --- | --- |
| `frontend/` | Accessible React/TypeScript/Vite shell, generated API types, Vitest, Playwright |
| `backend/app/` | FastAPI routes and Pydantic v1 output contracts |
| `backend/migrations/` | Reviewed Alembic scaffold migration; no candidate personal tables |
| `backend/tests/`, `backend/scripts/` | Contract/unit tests, schema export, DB verification |
| `tests/fixtures/` | Empty demo response and versioned fictional Phase 1 corpus |
| `docker-compose.yml` | Loopback-only disposable PostgreSQL developer service |
| `.github/workflows/phase0.yml` | Checks only; no deployment or CI credentials |
| `docs/` | Original baselines, decisions, and observed Phase 0 results |

The Phase 0 view does not implement discovery, classification, findings,
privacy actions, deletion/recomputation, auth/tenancy, retention, cloud hosting,
or third-party integrations. Those need later phase instructions and security
gates. Email/history evidence does not prove current company retention or sale.
Phase 1 artifacts were separately authorized; see the Phase 1 report. The separately authorized Phase 2 lab is documented below.

## Phase 1 test-data corpus (separate from the running shell)

The separately authorized Phase 1 work adds only fictional test artifacts and
offline validation. Start with [the corpus guide](tests/fixtures/pv1/v1/README.md)
and [review catalog](tests/fixtures/pv1/v1/CATALOG.md). The app/API still behave
exactly as the Phase 0 shell; no raw fixture is uploaded or processed by it.

From `backend/`, run `uv run --frozen python -m scripts.validate_corpus` for
integrity, coverage and proposed-label checks, or `uv run --frozen pytest -q`
for the existing suite plus corpus regression/mutation tests. The original CI
workflow discovers these tests without modification. Corpus 1.1.0 has status
**product-owner-approved, AI-assisted baseline**. No independent blind human
review was performed and no reviewer is recorded. The approved transaction
meaning covers financial/commercial interaction evidence; c07 keeps Sensitive/Low
with contradictory payment claims, c12 excludes all six invalid/missing history
timestamps, and c21 is an unpaid invoice with Medium/Medium. No parser/classifier
accuracy is measured. Original review materials and 1.0.0 are preserved.
See the [taxonomy decision](docs/PHASE1-TAXONOMY-DECISION.md) and
[PHASE1-REPORT.md](docs/PHASE1-REPORT.md) for results, history and boundaries.


## Phase 2 synthetic local import lab

On branch `phase2/local-synthetic-import`, start the same loopback API and Vite
commands above, then open `http://127.0.0.1:5173/phase2`. The root empty demo and
Phase 0 health/demo contracts remain unchanged. Read the synthetic-only notice,
check the consent box, and select unchanged `.eml` or Chrome JSON files from
`tests/fixtures/pv1/v1/`. Exact approved byte hashes are required; other files are
rejected. Do not select actual personal records. The raw fixture content is not copied
into the browser bundle or fetched from the server; you select local files.

Limits: 20 files, 1 MiB per email, 10 MiB total, 10,000 records, five-second worker
deadline. Source files, bodies, addresses, full URLs and filenames never appear in
results or requests. The lab shows domain/time/code/provenance records, explicit
unresolved/excluded records, and within-source exact-history duplicate markers.
No email relationship or sensitivity rule runs. HTML-only evidence stays
unresolved; attachments are ignored. Clear results or close the page to discard
transient state; nothing is saved. There is no API upload button or analysis call.

`POST /api/v1/phase2/validate` tests a strict minimized JSON contract only and
returns a count. The UI never calls it. It does not persist or process a file.
Raw/multipart payloads and unknown fields are rejected without echo or logging.
The separate contract is exported with `uv run --frozen python -m scripts.export_phase2`
in `backend/`, then `npm.cmd run contracts:generate` in `frontend/`. Checks add
`uv run --frozen python -m scripts.export_phase2 --check`; existing commands still
run all Phase 0/1 tests plus Phase 2 tests and Playwright import/egress scenarios.

See ADR-010 in [DECISIONS.md](docs/DECISIONS.md) for reconciled size limits, parser
subset, provenance and trust limits, and [PHASE2-REPORT.md](docs/PHASE2-REPORT.md)
for executed checks and review gates. Phase 2 does not authorize persistence,
discovery/fusion, sensitivity rules, action links, OAuth, auth, deletion engines,
deployment, real users or later phases. Review PR only; do not merge.

## Phase 3 synthetic evidence inspector

Open `http://127.0.0.1:5173/phase3` using the same loopback development commands.
Select only unchanged approved corpus files after reading the notice. This
read-only development inspector uses a separate, transient browser worker with
the same SHA-256 gate and bounds. It extracts a narrow set of safe feature codes,
then links explicit evidence to cautious domain/type relationships. The root demo
and Phase 2 lab keep their existing behavior. No source or result is uploaded.

Sender domains alone create no email relationships. Account/transaction claims
remain inferred with unverified sender attribution; visits do not prove accounts.
Transactions mean commercial interaction evidence: an unpaid invoice is included,
contradictory receipt/cancellation claims stay visible, and payment completion or
retained credentials remain unknown. Exact copies retain duplicate provenance
without increasing confidence. Ambiguous, spoofed, quoted or injected evidence
has explicit unknown outcomes. No HTML, attachment or body is rendered; the
inspector displays only the minimized graph and source/row support as inert text.
Clear results or close the page to discard transient state.

`npm.cmd --prefix frontend run phase3:metrics` reproduces
[PHASE3-METRICS.json](docs/PHASE3-METRICS.json) against the unchanged 29-case,
six-snapshot 1.1.0 oracle. These are known synthetic development measurements,
not independent review or real-user accuracy. Sensitivity/review priority remain
unassessed. Existing test/check commands include Phase 3 automatically.

Read ADR-011 in [DECISIONS.md](docs/DECISIONS.md) and
[PHASE3-REPORT.md](docs/PHASE3-REPORT.md) for architecture, precise executed
results, limitations and exit gates. No Phase 4 sensitivity, Phase 5 dashboard,
actions/deletion engine, personal schema, persistence, auth, general imports,
external AI or deployment is included. PR #3 is for review only; do not merge.

## Phase 4 synthetic assessment inspector

Open `http://127.0.0.1:5173/phase4` with the same loopback development commands.
Select only unchanged approved corpus files. The same exact-byte SHA-256 gate,
file/record limits and five-second worker deadline apply. The Phase 0–3 routes
and outputs keep their existing behavior; all processing remains transient in
the browser. No source or assessment is uploaded or saved.

The read-only inspector explains `sensitivity_rules_v1` priorities separately
from evidence state and claim confidence. It shows fixed rationale text, source/
row support, limitations and unknown claims. Clinic appointment-portal context
warrants review without a diagnosis or personal-attribute inference; an unpaid
invoice remains Medium, and contradictory paid/cancelled claims remain Sensitive
with Low evidence confidence. Sender authenticity, current account activity,
payment completion, retained credentials, retention, sale and breach status stay
unknown. Low is not a safety guarantee; ambiguous evidence stays Unknown.

A single bounded `email_context_v1` code fills the clinic-context gap without
retaining source prose. Explanations use fixed vocabulary and no source-derived
text, personal identifiers or URLs. Clearing or closing discards results.
There are no dashboard filters, action links, source-deletion engine, persistence,
auth, general imports, external AI or deployment.

Run `npm.cmd --prefix frontend run phase4:metrics` to reproduce
[PHASE4-METRICS.json](docs/PHASE4-METRICS.json) against the unchanged 29-case,
six-snapshot 1.1.0 baseline. Assessment agreement describes this known synthetic
development set only; it is not real-world accuracy or independent blind review.
Existing check commands include the new tests automatically. See ADR-012 in
[DECISIONS.md](docs/DECISIONS.md) and [PHASE4-REPORT.md](docs/PHASE4-REPORT.md)
for exact checks, limitations and exit gates. PR #4 is for review; do not merge.

## Phase 5 integrated synthetic MVP

Open `http://127.0.0.1:5173/phase5` using the existing loopback start commands.
Consent and select only unchanged approved corpus v1.1.0 `.eml` and Chrome JSON
files. The integrated flow runs the unchanged Phase 2–4 gate, parsers, discovery
and assessment engines in a bounded browser worker; nothing is uploaded or saved.

Review claim counts and independent priority/type/confidence filters, expand a
finding for fixed explanations, observed vs inferred evidence, confidence,
unknown claims and safe source/row provenance. Source labels identify selection
instances rather than filenames. Results paginate at 50; provenance/excluded
indices display up to 200 with complete counts. Synthetic action links are
literal reviewed `.test` examples, not real verified services; opening records
only transient `opened`, never successful deletion. Other findings display
“No verified direct link available”. See [action review records](docs/PHASE5-ACTION-REVIEWS.md).

Remove any source to discard old findings/actions and fully recompute from the
remaining selected files, including duplicate alternatives. Clear-all, consent
withdrawal, navigation or closing discards the session and terminates work.
Removal does not delete original files, external-company records or persistent
backups. A single list of File references stays outside React state for
recomputation; no raw-text copies or persistence are introduced. Browser memory
reclamation is not secure erasure. All existing file/MIME/JSON/count limits and
the five-second worker deadline apply. No general or real-person imports.

Existing check commands discover all new session/oracle, boundary and Playwright
checks. [PHASE5-PLAN.md](docs/PHASE5-PLAN.md), ADR-013/014 and
[PHASE5-REPORT.md](docs/PHASE5-REPORT.md) document implementation and executed
validation. Phase 0–4 routes, APIs, contracts, corpus, migrations and locks remain
preserved. No auth, persistent personal data, external AI, public deployment or
Phase 6. PR is for product-owner/architecture review; do not merge.
