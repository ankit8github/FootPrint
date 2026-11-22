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
| `tests/fixtures/` | One empty synthetic response; no Phase 1 corpus |
| `docker-compose.yml` | Loopback-only disposable PostgreSQL developer service |
| `.github/workflows/phase0.yml` | Checks only; no deployment or CI credentials |
| `docs/` | Original baselines, decisions, and observed Phase 0 results |

Not implemented: parsing, normalization, discovery, classification, findings,
privacy actions, deletion/recomputation, auth/tenancy, retention, cloud hosting,
or third-party integrations. Those need later phase instructions and security
gates. Email/history evidence does not prove current company retention or sale.
Do not start Phase 1 based on this scaffold. See the report for remaining gates.
