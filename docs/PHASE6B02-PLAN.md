# Phase 6B-02 plan and acceptance checklist

Date: 2026-11-24. Written before implementation. Branch:
`phase6b/opaque-session-csrf`. Verified clean synchronized main:
`fb0db1300a117e07a7992a7b2675bd8a8ebe5faa`, containing Phase 6B-01 merge
`bfaa9585167771f6e49b849ec9ecb88fa0501579`.

Implement only a default-disabled ASGI session fixture and bounded ephemeral
service in `backend/experiments`. Reuse the unchanged 6B-01 Protocol and MockIssuer;
preserve the old factory/tests, app routing, frontend, dependencies, contracts,
migrations and immutable corpus. No normal-app import, env activation, serving CLI,
live provider, real account, durable store or footprint repository.

1. Add digest-only opaque sessions, fixed fictional owners, strict metadata and
   limits, deterministic server clocks, exact expiry and same-owner ordered fences.
2. Add secure cookies, pre-auth login CSRF and session/action-bound one-use tokens.
   Reauthentication must pass existing OIDC validation, rotate handles, retire the
   old handle and preserve its original absolute deadline.
3. Validate Origin/Fetch Metadata/JSON before any browser mutation. GET bootstrap
   only allocates bounded pre-auth security material; GET CSRF/read may refresh idle
   metadata, never login/logout or commit a marker. OIDC callback is the sole GET
   that can establish/rotate authenticated state. The unchanged mock token endpoint
   is an isolated OAuth back-channel form exchange, not a browser session mutation.
4. Use a shared owner fence for marker commit, logout/all and signed fictional
   recovery/MFA-reset events. Recheck handle/epoch/expiry/state at final commit.
   Invalid browser requests leave session/identity state untouched. Authenticated
   invalidation failure/cancellation after fencing intentionally quarantines access;
   it never returns successful revocation. No real provider logout is claimed.
5. Add adversarial and barrier-controlled race tests, full regressions/audits,
   baseline/docs validation and fresh GitHub CI/Docker scaffold checks. Open PR #8
   with exact head/inventory/results; do not merge.

| ID | Acceptance evidence required |
| --- | --- |
| SS-01 | Validated fictional OIDC login only; issuer+subject ownership, equal email never links; old 84 OIDC tests unchanged |
| SS-02 | 32-byte handles, only digests in store, exact __Host-fp_session attributes/deletion; no token or identity cookie payload |
| SS-03 | Idle 30-min/absolute 12-hour boundary, rotation/fixation/stale-cookie denial, original absolute deadline preserved |
| SS-04 | Every protected request validates store, record, active identity and current epoch; corrupt/unavailable/missing state fails closed |
| SS-05 | Bounded sessions/preauth/attempts/metadata, cleanup/shutdown, deterministic clocks, no live eviction on limit failure |
| SS-06 | Preauth login and per-session/action CSRF; missing/wrong/replayed/cross-session tokens rejected without state changes |
| SS-07 | Exact Origin, Fetch Metadata, JSON, method/path and same-origin checks; no credentialed CORS; fixed safe errors/headers |
| SS-08 | Logout before response, logout-all owner epoch, other identity unaffected, provider outage independent of local logout |
| SS-09 | Signed, bounded fictional recovery/MFA events: authentication/type/time/identity/replay/order negatives and epoch invalidation |
| SS-10 | Both lock orders for mutation vs logout/all/event; final recheck, failure/cancellation/quarantine and no stale commit/resurrection |
| SS-11 | DEBUG log/error/URL/cookie leak checks; no network fallback or persistent writes; no browser storage APIs/login UI introduced |
| SS-12 | Normal app/default fixture absent routes; full previous tests/contracts/corpus/29 scenarios/six survivors and scaffold migrations preserved |

Only an artificial bounded in-memory marker may be committed. No Phase 6B-03,
Phase 6C, tenant tables/RLS, personal-data save APIs, beta users, deployment or
real-user processing. Production TLS/browser/proxy behavior, persistent revocation,
provider credential custody and verified recovery-event delivery remain separate
review tasks. Existing proposed ADR history and unresolved 6A decisions stay intact.
