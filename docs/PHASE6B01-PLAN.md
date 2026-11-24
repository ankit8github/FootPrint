# Phase 6B-01 implementation plan

Date: 2026-11-24. Scope: authorized local fictional OIDC experiment only.
Base: `167da1d9da59acbb5cfb67cb67a5a2ea78cfefbb`, containing Phase 6A merge
`756989a1ddc1e6fa108b320bddd16361e3c4a6d9`.
Branch: `phase6b/oidc-protocol-spike`. Written before implementation.

1. Preserve normal FastAPI registration, frontend, contracts, corpus, migrations
   and CI. Place the spike in `backend/experiments`, with no import from `app`.
   Default fixture construction exposes no routes; explicit test activation uses
   pinned loopback origins and in-process ASGI transports, never network sockets.
2. Review/pin maintained Authlib HTTPX2 OAuth client and joserfc verification in
   the dev dependency group. Use their PKCE/JWS/JWK/claim machinery, not custom
   signature/password cryptography. Record versions, audit and lock changes.
3. Implement bounded, ephemeral five-minute transactions: random state, nonce,
   PKCE verifier and browser transaction binding; consume before code exchange,
   recheck deadline after exchange; expire/clear state on completion/shutdown.
   A transaction cookie is not an authenticated session. No user accounts created.
4. Use fixed issuer/client/callback/endpoints, openid only, RS256 only, strict
   public JWKS and token claim/time validation. Reject dynamic discovery, redirects,
   duplicate parameters and provider/claim errors with fixed responses and clean
   303 completion URLs. Keep protocol values out of logs and retained HTTP objects.
5. Add isolated mock issuer and adversarial tests, including two fictional subjects
   with the same unsolicited email claim. Identity is issuer+subject only. Prove
   default invisibility, no external egress, no footprint transmission and cleanup.
6. Research current official provider/alternative documentation; separate published
   capabilities from unverified plan, region, cost and recovery/MFA reset questions.
   Recovery-driven local session invalidation belongs to future 6B-02.
7. Run local lint/format/types/unit/contracts/corpus/audits, unchanged frontend and
   browser checks, documentation/baseline checks, then fresh push/PR GitHub CI with
   Docker scaffold migrations. Open PR #7, record exact head/results/limitations;
   do not merge. Failed/unexecuted tests are not reported as passing.

## Security acceptance checklist

| ID | Required executed evidence |
| --- | --- |
| OIDC-01 | Positive code+PKCE S256 exchange, openid only, exact callback/client/issuer |
| OIDC-02 | State/nonce/binding randomness, five-minute boundary, one-use/replay and post-exchange expiry |
| OIDC-03 | Wrong issuer/audience/client/nonce/signature/algorithm; missing nonce; alg=none; expired/future/ill-typed times rejected |
| OIDC-04 | Reused/invalid code and PKCE mismatch rejected; no retry fallback |
| OIDC-05 | Redirect manipulation, dynamic issuer/discovery/token/JWKS URLs and token header URL hints cannot select a network target |
| OIDC-06 | Malformed/oversized/ambiguous/private/incorrect-use JWKS, provider timeout/unavailability, invalid responses fail closed |
| OIDC-07 | Two issuer-subject identities sharing an email remain distinct; only the pair survives validation |
| OIDC-08 | No codes/tokens/raw claims in app/HTTP logs, errors, completion URLs, browser storage, persistent writes or retained transaction state |
| OIDC-09 | Disabled factory and normal app expose no spike/auth/provider routes; activated fixtures require loopback and perform no real network calls |
| OIDC-10 | No footprint input accepted/transmitted; all previous tests/oracles/contracts/migration behavior unchanged |

Future BFF integration must independently implement initiation CSRF, durable opaque
sessions, identity ownership, account recovery/MFA-reset epoch invalidation,
logout, production TLS/proxy log policy and provider verification. None is supplied
by this protocol experiment. Proposed ADR-015–020 and all unresolved 6A decisions
remain unchanged. No live provider, personal data, persistence, login UI, RLS,
deployment, external integration, Phase 6B-02 or Phase 6C is authorized.
