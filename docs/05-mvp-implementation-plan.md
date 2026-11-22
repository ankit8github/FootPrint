# PV1 — MVP Implementation Plan

**Product:** Personal Digital Footprint & Privacy Intelligence  
**Document:** 05 | **Version:** 0.1 | **Date:** 2026-11-22  
**Status:** Approved planning proposal only; no code, deployment or test results implied  
**Depends on:** `01-product-requirements.md`, `02-source-feasibility.md`, `03-evidence-data-model.md`, `03-pv1-schema.sql`, `04-security-privacy-architecture.md`

## 1. Objective and fixed scope

Build a small, demonstrable user journey:

> Select authorized `.eml` messages and/or Chrome-compatible history JSON → parse safely → discover likely digital relationships → distinguish sensitivity from confidence → show explainable evidence → open verified account/privacy links → delete imported evidence and recompute findings.

**Locked PV1 pillars:** Discover, Analyze, Classify, Visualize, Control.

**P0 adapters:** `email_eml_v1` and `browser_chrome_json_v1`. **P1:** `.mbox` if capacity and parser safety allow. **Not MVP:** new browser, extension, cookies, passwords CSV, SMS, Meta social access, Gmail/Outlook OAuth, automatic deletion or persistent surveillance.

No assumptions that emails prove data sale, current retention, saved cards, security breach, or complete footprint discovery.

## 2. Scope priorities

| Priority | Work | Required for first working demo? |
|---|---|---|
| P0 | Synthetic `.eml` and Chrome JSON fixtures; local parse; minimal evidence schema | Yes |
| P0 | Domain normalization, cautious matching, dedup, relationship and assessment rules | Yes |
| P0 | Dashboard: categories, confidence, evidence detail, unknowns | Yes |
| P0 | Manually reviewed privacy-action directory and external links | Yes |
| P0 | Source deletion with dependent recomputation | Yes |
| P0 | Automated tests, documented limitations and security checks | Yes |
| P0-Beta | Secure auth, tenancy, opt-in persistence, safe operations and retention | Before multiple real users |
| P1 | Streaming `.mbox` import | No |
| Later PV1 | Outlook/Gmail live APIs, browser extension, Meta exports, optional SMS and cookie metadata | No; each requires separate feasibility/security review |

## 3. Technical architecture recommendation

- **Frontend:** React + TypeScript + Vite. File picker, local import worker, dashboard, finding detail, source management and action links.
- **Processing:** TypeScript browser-side parsers for bounded P0 inputs where feasible. No raw email/body or full URL upload by default. For synthetic-only development, a backend parse endpoint can be used for rapid tests but must not become the default real-user path without security review.
- **Backend:** Python FastAPI + Pydantic contracts for normalized observations, relationship services, assessments and ownership checks.
- **Database:** PostgreSQL + migrations (Alembic or equivalent). Use `03-pv1-schema.sql` as a **candidate logical baseline**, not as already production-safe SQL.
- **Classification:** deterministic, versioned evidence rules first; unknown when uncertain. No external LLM P0.
- **Testing:** Pytest for backend and data semantics; Vitest for frontend/unit parser tests; Playwright for end-to-end journeys; CI security checks.
- **Deployment:** Docker Compose locally, with separate settings for test/beta and no real secrets committed. Public deployment only after all security gates.

### Logical modules

```text
frontend/
  src/features/imports/            # local parsers, validation, source UX
  src/features/findings/           # list, filters, evidence detail
  src/features/actions/            # reviewed action destinations
  src/features/privacy/            # consent, delete, retained-data view
backend/
  app/api/                         # authenticated routes
  app/contracts/                   # Pydantic typed request/response models
  app/services/                    # match, dedupe, classify, recompute
  app/db/                          # ORM/repositories + migrations
  app/security/                    # auth/tenant enforcement/redaction
  tests/
tests/fixtures/                   # exclusively synthetic input/labels
docs/                             # Step 1–5 + future decisions
```

## 4. API contracts (proposed; subject to design review)

| Operation | Possible endpoint | Request / response principle |
|---|---|---|
| Create normalized import | `POST /api/v1/imports` | Adapter, source label, **minimized observation records**, owner derived from session |
| Import status | `GET /api/v1/imports/{id}` | Owner-scoped status and counts only |
| List relationships | `GET /api/v1/relationships` | Filter by sensitivity, confidence, type and date |
| Finding details | `GET /api/v1/relationships/{id}` | Evidence kinds, rationale, limitations, source versions |
| Privacy actions | `GET /api/v1/relationships/{id}/actions` | Reviewed official URLs only |
| User action state | `POST /api/v1/relationships/{id}/actions/{action_id}` | `opened` / user-reported state; never auto-verify |
| Remove import | `DELETE /api/v1/imports/{id}` | Delete + recompute in transaction; owner-scoped |
| Remove all user records | `DELETE /api/v1/me/data` | Delete personal findings with explicit confirmation |

All mutating endpoints require authentication and CSRF protection where cookie sessions are used. Add request IDs, pagination, rate limits, bounded payloads and a stable versioned error schema.

## 5. Delivery phases with acceptance gates

### Phase 0 — Repository + working contracts

**Build:** initialize mono-repo, package/dependency lockfiles, FastAPI skeleton, React client, Postgres dev container, CI, migrations, API models, secure development configuration.

**Deliverables:** reproducible local start; unit tests in CI; no plaintext real data committed; baseline README and decision log.

**Exit:** a clean checkout can run all synthetic tests; no secret files, CI keys or user data in repository.

### Phase 1 — Synthetic datasets and ground truth

**Build:** representative, *entirely fictional* `.eml` and Chrome-history JSON, including visits, registrations, receipts, marketing, ambiguous origins, phishing/spoofing patterns, duplicate and conflicting evidence, unsafe URLs, malformed dates, and deletion cases. Construct a manually reviewed truth label file.

**Deliverables:** versioned fixture catalog, expected relationships, safe/unsafe test cases, benchmark script and metrics report.

**Exit:** independent reviewers can determine ground truth without consulting classifier outputs; no actual user data in fixtures.

### Phase 2 — Safe import pipeline

**Build:** local selection and bounded parsing, schema validation, safe domain/timestamp normalization, redaction and per-import processing state; reject unsupported file types.

**Deliverables:** client parser, strict normalized observation contract, safe errors, unit/fuzz/property tests.

**Exit:** synthetic passwords, cards, tokens, full email bodies and query-string secrets absent from backend requests, database and logs; malformed inputs fail safely.

### Phase 3 — Discovery and evidence linking

**Build:** source event deduplication, domain mapping with public-suffix awareness, cautious canonical business mapping, relationship evidence links, claim-specific confidence.

**Deliverables:** deterministically reproducible `observations`, `relationships`, `relationship_evidence`; evidence endpoint.

**Exit:** browser visit never becomes a confirmed registration; marketing sender never proves data sale; same-domain signals fuse without losing source provenance; false merges tested.

### Phase 4 — Sensitivity engine + explanation

**Build:** versioned rules: Sensitive, Medium, Low and Unknown; separate confidence and evidence state; rationale codes and limitations. Default unknown retention/sale statuses.

**Deliverables:** assessment service with testable explanations.

**Exit:** all findings expose what was observed, what was inferred, sensitivity, confidence and important unknowns; no unsupported confirmation or card-retention assertions.

### Phase 5 — Dashboard, actions and deletion

**Build:** a straightforward UI with source imports, summary counts, filters, finding detail and safe action URLs; personal data deletion and recomputation.

**Deliverables:** usable local MVP demonstrating all five pillars.

**Exit:** end-to-end import-to-finding-to-action works; action click means `opened` only; deleting one source recomputes two-source relationships; user sees deletion state clearly.

### Phase 6 — Private beta hardening

**Build:** authenticated multi-user sessions, tenant isolation, persistence consent, retention scheduler, backup/delete operations, operational monitoring without source content, deployment hardening, threat-model review.

**Deliverables:** private test environment, privacy notice draft, incident response runbook, test report.

**Exit:** pass all Step 4 gates; two-user cross-tenant test suite; no real-user invites until processing, retention, hosting and legal disclosure are reviewed.

### Phase 7 — User validation and iteration

**Build:** consented usability sessions with 15–20 participants, privacy safeguards, ground-truth checks, same task benchmark against available Yorba flow where fair and permitted.

**Deliverables:** evidence coverage, false positives, sensitivity agreement, user-comprehension, action usability, and qualitative feedback dashboard.

**Exit:** decide whether to iterate, narrow or expand based on measurements. **No product-market fit claim based only on small pilot.**

## 6. Core acceptance tests and provisional targets

| Measure | Proposed criterion | How tested |
|---|---|---|
| Account discovery precision | ≥90% | Correct discovered likely accounts ÷ all reported likely accounts |
| Account discovery recall | ≥80% | Correct discovered accounts ÷ labeled actual supported accounts |
| Sensitivity review agreement | ≥90% on adjudicated supported cases; report Unknown separately | Human-labeled fixtures and consented beta |
| Unsupported assertions of retention/sale | **Zero** | Explicit assertions + copy-review tests |
| Tenant leaks / secrets persisted | **Zero** | Two-user API tests + synthetic secret scans |
| Verified privacy-link validity | ≥95% in reviewed directory | Check destinations/HTTPS/expected service |
| Action usability | ≥80% of tested users find correct settings path without separate searching | Timed usability tasks |
| Useful action within first week | Exploratory target ≥40% | Consented beta survey / app events (no invasive activity tracking) |
| Deletion integrity | 100% of required recompute cases | Automated source delete tests and manual review |

**Important:** These are hypothetical targets from PRD and prior research, not achieved metrics. Measure precision and recall for *supported evidence*, rather than pretending that imported inputs cover a user's entire internet history. Compare same-user/same-window/same-consent conditions where possible.

## 7. First end-to-end test scenario

1. User selects a synthetic welcome email for `sample-shop.test`, a synthetic order-confirmation message, and browsing history containing visits to `sample-shop.test` plus an unrelated news site.
2. Client produces only normalized observations (domain, event type, time and safe evidence codes). Raw email bodies and URL query tokens do not leave the client.
3. Backend creates a `likely_account` and `transaction` relationship backed by linked observations, and a `visited` relationship for the news site.
4. Assessment marks the shopping relationship Sensitive for review, with claim-specific confidence; explicitly states that current card retention and data sale are unknown.
5. UI displays reasons and a pre-reviewed official account/privacy action link (synthetic/test host in development).
6. When the user deletes the email import, transaction/account evidence is removed and assessed relationships recompute from history alone. The UI must not retain stale purchase claims.

**This scenario is our first completion milestone.** No external account credentials or real email access required.

## 8. Security engineering checklist

- [ ] Strict file adapter/size/field limits and parser abuse tests.
- [ ] Client-side pre-processing; capture browser network traffic in E2E test to verify no raw payload egress.
- [ ] Secret redaction and JSON allowlist (`safe_metadata` cannot become a raw-data dumping ground).
- [ ] Versioned rules and claim-specific evidence.
- [ ] Authenticated owner-scoped queries, updates and deletes; foreign-ID tests.
- [ ] Verified action directory and malicious redirect/link tests.
- [ ] Import deletion + recomputation + account deletion tests.
- [ ] HTTPS, sessions, CSRF/XSS defenses, safe logs, encryption/backups, rate limiting.
- [ ] Dependency scanning, code review, CI checks and documented incident procedures.
- [ ] Review external privacy requirements before real-user access.

## 9. Schema issues to close before beta

Record these as tickets against `03-pv1-schema.sql`:

- Replace placeholder `retention_policy` and implement expiry & background deletion logic.
- Harden free-text/JSON metadata with typed allowlists, schema-level limits where possible and app validation.
- Verify all user-owned rows are tenant-scoped; add RLS if architecture review selects it.
- Ensure `user_actions.action_id` belongs to the relationship's organization.
- Establish a migration process, separation of migration and application DB credentials, and test restoration/migration rollback.
- Store enough non-sensitive provenance and versions for explanations to be reproducible.
- Ensure import deletion and user deletion can't leave unsupported assessments or falsely completed actions.

## 10. MVP exit and non-exit definitions

**MVP complete (local):** one full synthetic scenario, stable API contracts, all five PV1 pillars visible, deterministic tests, deletion recomputation, secret-exclusion checks, versioned documentation.

**Private beta ready:** additionally pass Step 4 security gates, have secure multi-user isolation, agreed retention and privacy notices, hosting/backup controls and documented response to incidents.

**Not a basis for public launch:** synthetic tests alone, unreviewed SQL DDL, mocked links, demo UI, a privacy policy without real enforcement, or an unaudited full-inbox integration.

**Deliberately not adding:** automated external deletion, browser replacement, always-on tracking, SMS/Meta access, full password history, generalized LLM agent, remote AI analysis.

## 11. Developer working cadence and decision log

For each phase: create focused issue(s) → write failing tests or fixtures → implement the smallest behavior → review privacy/security effects → run automated tests → record measured results and tradeoffs → proceed only after the exit gate.

Track decisions using:

| Field | Example |
|---|---|
| Decision ID | `ADR-001` |
| Proposed decision | Local-first `.eml` parsing |
| Alternative | Server-side raw email upload |
| Reason | Avoid central raw inbox storage |
| Evidence / test | Browser-network test; secret-scan test |
| Status | Proposed → Accepted after test |
| Revisit trigger | Local performance fails at pilot size |

## 12. Immediate next work items

1. Create the monorepo and testable API contracts; use existing `03-pv1-schema.sql` as draft input for migration design.
2. Implement fictional fixture set and a truth manifest *before* building classification rules.
3. Build safe local `.eml` and Chrome JSON normalization and test that no secrets leave browser memory.
4. Deliver the synthetic end-to-end demo from Section 7.
5. Only then harden auth, hosting and retention for real users.

## 13. References

- Step 1 PRD: `01-product-requirements.md`
- Step 2 Source Matrix: `02-source-feasibility.md`
- Step 3 Data Model: `03-evidence-data-model.md` and `03-pv1-schema.sql`
- Step 4 Security Architecture: `04-security-privacy-architecture.md`
- OWASP upload security: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
- OWASP API Top 10: https://owasp.org/projects/api-security-project
- NIST SSDF: https://csrc.nist.gov/pubs/sp/800/218/final
