# PV1 — Codex Phase 0 Handoff

**Status:** Instructions for Codex, not completed implementation.
**Scope:** Phase 0 ONLY (repository scaffold + working contracts). Do not implement the discovery engine, import real user data, connect OAuth providers, or deploy publicly.

## Required reading
Read all these files before modifying code:
1. `docs/01-product-requirements.md`
2. `docs/02-source-feasibility.md`
3. `docs/03-evidence-data-model.md`
4. `docs/03-pv1-schema.sql`
5. `docs/04-security-privacy-architecture.md`
6. `docs/05-mvp-implementation-plan.md`

If any required file is missing, stop and report it. The documents are design baselines; the SQL is a *candidate* schema, not production-approved.

## Assignment
Build a reproducible, local-only monorepo scaffold for **Personal Digital Footprint & Privacy Intelligence PV1** using:
- Frontend: React + TypeScript + Vite
- Backend: Python + FastAPI + Pydantic
- Database: PostgreSQL with local Docker Compose and an explicitly reviewed initial migration (do not apply unreviewed draft SQL blindly)
- Testing: Vitest, Pytest, and minimal Playwright smoke-test setup
- CI: lint/typecheck/unit tests with sensible dependency pinning and lockfiles

Deliverable layout: `frontend/`, `backend/`, `tests/fixtures/` (synthetic-only), `docs/`, and top-level README, `.gitignore`, `.env.example`, `docker-compose.yml` (as appropriate). Include `docs/DECISIONS.md` and `docs/PHASE0-REPORT.md`.

For now, implement only:
- an accessible app shell with a clearly labeled **synthetic demo** state, no real file upload processing;
- a FastAPI `/health` or `/api/v1/health` endpoint returning non-sensitive status;
- typed, versioned *empty* API contracts that anticipate authorized normalized observations / evidence / assessments without accepting raw email uploads;
- PostgreSQL developer configuration, with *no hardcoded real credentials*, and no public production setup;
- unit tests and one smoke test showing frontend and backend start;
- instructions to start/stop/test locally on Windows + VS Code.

## Hard constraints
- Preserve PV1's five pillars (Discover, Analyze, Classify, Visualize, Control) but do not implement full functionality in Phase 0.
- P0 future sources are only user-selected `.eml` and Chrome-compatible history JSON. No Gmail/Outlook OAuth, passwords CSV, cookies, SMS, Meta, browser extension, tracking, web scraping or automatic external deletion.
- Never commit secrets, real personal data, actual mailbox contents, tokens, card numbers, or API credentials.
- Do not send raw records to any external API or LLM.
- Do not claim a website currently retains or sells information solely from email or browser history.
- Document any disagreement or ambiguity between source documents in `docs/DECISIONS.md`; request approval before a material scope/security decision.
- Do not deploy or invite real users.

## Execution protocol
1. Inspect the provided documents and environment; briefly propose an implementation outline.
2. Create the smallest scaffold that satisfies Phase 0.
3. Run local tests, lint and typechecks where toolchain exists; if tools are unavailable, state exactly what was not run.
4. In `docs/PHASE0-REPORT.md`, document files added, commands executed, results (pass/fail), architecture decisions, risks, and next-phase dependencies.
5. At completion explain the architecture in everyday language: where frontend, API, DB and tests live; what information flows between them; what is *not* implemented.
6. Do not mark Phase 0 complete if clean-checkout setup or test reproducibility is unverified. Report blockers explicitly.

## Definition of done
- A new developer can follow README steps on a clean checkout to start client, API and local database.
- Browser sees only an obviously synthetic app shell.
- API health endpoint works.
- Tests and checks are runnable and their results are reported.
- No real personal data, secrets or unnecessary permissions are required.
- Decisions and limitations are recorded honestly.
