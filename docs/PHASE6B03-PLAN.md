# Phase 6B-03 implementation plan

Date: 2026-11-25 (Asia/Calcutta). Scope: fictional, disposable ASGI ownership and
negative authorization tests only. Written before implementation.

Preflight: clean main and fetched origin/main both
`0dc69cc296a53d88353da573ed35a882c209bc3f`; verified
`394130d0776eca2f27d52f806d172ba5ca626117` is an ancestor. Branch:
`phase6b/ownership-negative-tests`. No local changes were reset. No AGENTS.md found.
Read 6A plan 6B-03, security design section 4, TM-01/03/05/06/15,
6B-02 session security/report, proposed ADR-015 through ADR-022, session store,
fixture/events/tests, normal router, Phase 2 admission and Phase 5 local session.

## Acceptance IDs

| ID | Required evidence |
| --- | --- |
| OA-01 | Frozen typed principal bound to validated fictional issuer/subject, current session digest and auth epoch; fixed isolated UUID registry; shared email never joins identities |
| OA-02 | Every repository constructor/operation requires principal; private disposable backing state has no public unscoped repository helpers; corrupt records/context fail closed |
| OA-03 | Two-user positives and symmetric foreign/random read/update/delete/list/filter/count/join/nested/batch negatives; reject ownership in every client location |
| OA-04 | Fixed 401/403/404/409/422 failures, matching foreign/missing safe headers; no ID, sentinel, claims or secrets reflected/logged |
| OA-05 | Owner/session/filter/generation-bound opaque bounded cursors; owner-only counts/order; B-only changes cannot affect A metadata |
| OA-06 | Owner fence plus current-session/epoch checks after acquisition and last suspension before atomic mutation publication; both logout/all/recovery lock orders |
| OA-07 | Expiry, epoch mismatch, outage, corrupt/missing state, cancellation and rejected writes never publish partial changes or affect the other owner |
| OA-08 | Isolated two-tab invalidation/late-response helper tests; explicitly no claim of browser login integration |
| OA-09 | Default-disabled unmounted fixture, teardown, no network/persistence, unchanged normal routes/contracts/frontend/corpus/migrations/previous ADRs |
| OA-10 | Endpoint inventory: current fictional routes and future footprint families, owner/session/consent/generation/lifecycle requirements and missing future checks |
| OA-11 | Full backend/frontend/contracts/corpus/oracles/browser/audits plus exact-head push/PR CI, GitGuardian and scaffold migration evidence |

## Implementation sequence

1. Add typed principal/authority and immutable fixed issuer+subject to UUID registry.
   Bootstrap session lookup is the explicit auth-only exception, never a footprint
   repository. Existing validated session owner denotes the fixed issuer subject.
2. Add a mandatory owner-scoped Protocol and bounded synthetic repository handles.
   All operations share one guarded dispatcher: authenticate, take existing owner
   fence, reauthenticate, validate records/lifecycle, execute on owner-only view,
   reauthenticate before publication. Mutations use copy-on-write and generation
   preconditions. No await follows the final guard before publication.
3. Compose a separate default-disabled ownership ASGI factory with the unchanged
   session factory. Strict bounded JSON, UUID/path/query/header allowlists,
   action-bound session CSRF, fixed safe errors and scrubbed transport URLs.
   Add only fictional create/read/update/delete/list/count/join/nested/batch routes.
4. Exercise positive operations and symmetric adversarial matrix, cursor/count
   probes, injected corruption, barriers/failures/cancellation and test-only tab
   generation clearing. Assert repository state and absence of sentinel bytes.
5. Write authorization inventory and report; preserve all historical files unless
   an explicit narrow change is required. No new ADR is currently needed: this
   implements the experiment already described by PROPOSED ADR-017/022.
6. Run existing frozen validation commands and meaningful new tests; review diff,
   unchanged baselines and Markdown links. Commit/push branch, open separate PR
   against main (number assigned by GitHub), inspect exact-head CI/check logs.
   Record final SHA and evidence in PR body to avoid self-referential report SHA.

## Boundaries and stop

No durable auth/tenant tables, migrations, real accounts/providers, actual saved
footprints, production routes, frontend login, deployment, new data egress,
Phase 6B-04 or 6C. Mock locks are one process/one event loop; tests do not prove
PostgreSQL/RLS, timing indistinguishability, browser integration, production
security, legal compliance or independent review. G-S3 remains missing. Previous
ADRs stay PROPOSED. Rollback: discard fixture and feature branch; normal app is
unchanged. Stop with PR open and unmerged for product-owner and independent
engineering security review before any next phase.
