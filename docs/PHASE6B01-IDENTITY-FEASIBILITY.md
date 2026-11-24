# Phase 6B-01 identity-provider feasibility

Date/source check: 2026-11-24. **Conditional recommendation; no vendor selected,
provisioned, purchased or tested with live credentials.** Read with the
[plan](PHASE6B01-PLAN.md), [report](PHASE6B01-REPORT.md) and
[Phase 6A identity design](PHASE6A-SECURITY-DESIGN.md#3-identity-and-session-recommendation).
ADR-015–020 remain PROPOSED. This experiment does not close G-S3, G-S6 or G-S7.

## Local client selection and review basis

Use **Authlib 1.9.10** for authorization URL construction, PKCE S256 and OAuth
authorization-code exchange through its HTTPX2 integration. Use **joserfc 1.8.0**
for RSA JWK import, RS256 verification, strict JWT JSON decoding and claim registry
validation. These are exact development pins, with hashes/transitives in
`backend/uv.lock`; neither is imported by the normal app. No Authlib Starlette
session integration, password handling or custom signature cryptography is used.

Review performed: current official HTTP-client docs/changelog, installed
`AsyncOAuth2Client.create_authorization_url`, `_fetch_token`, token response
parsing and `OAuth2Token` expiry handling; joserfc JWK/JWT APIs and actual negative
tests. The review found that Authlib adds `expires_at`, accepts response JSON
through its parser and retains the token on its client. The spike validates the
bounded raw token response in a compliance hook before parsing, rejects duplicate
JSON keys, pins parameters and clears the ephemeral client's token in `finally`.
JWKS requests explicitly withhold the access token. Library defaults alone are
not the application's validation policy. Authlib's current HTTPX integration uses
the already pinned HTTPX2 dependency.
[Authlib HTTP clients](https://docs.authlib.org/en/stable/oauth2/client/http/index.html),
[Authlib changelog](https://docs.authlib.org/en/stable/upgrades/changelog.html),
[joserfc JWT guide](https://jose.authlib.org/en/guide/jwt/),
[joserfc JWT API](https://jose.authlib.org/en/api/jwt/).

New resolved packages are Authlib 1.9.10, joserfc 1.8.0, cryptography 50.0.2,
cffi 2.1.1 and pycparser 3.12. Existing package versions must remain unchanged.
Installed metadata identifies BSD-3-Clause for Authlib/joserfc/pycparser, MIT-0 for
cffi and Apache-2.0 OR BSD-3-Clause for cryptography. This is a metadata inventory,
not independent legal or supply-chain approval. Audit results are in the report;
absence of known advisories is not proof of security. No dependency is a verified
production integration merely because its test cases pass.

The mock's narrow profile requires fixed issuer/client/callback and RS256,
one 2048-bit RSA public signing key with exponent 65537 and known kid, essential
integer iat/exp/nbf, exact string audience/issuer/nonce and an allowlisted fictional
subject. It rejects multi-audience tokens, extra JOSE headers, optional token
extensions and rotation ambiguity. These restrictions are test policy, **not a
claim to support arbitrary conformant OIDC providers**. A production adapter
requires separate metadata, key rotation/cache, token profile and outage review.
The fixture models a public test client (`token_endpoint_auth_method=none`) with
PKCE, avoiding any provisioned secret. It does not establish a production BFF's
confidential-client authentication. Review client-secret custody or maintained
private-key authentication separately; PKCE is not a substitute for that decision.
[OIDC Core token validation](https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation),
[PKCE S256](https://www.rfc-editor.org/rfc/rfc7636.html).

## Auth0 candidate and maintained first-party alternatives

The following are published documentation findings, not tenant-level verification.
All commercial figures are a dated page snapshot in USD, not a FootPrint quote.

| Area | Published evidence checked 2026-11-24 | Unverified question / decision owner |
| --- | --- | --- |
| Auth0 B2C price | Pricing page's displayed monthly 500-MAU setting shows Free $0 (up to 25,000 MAU), Essentials $35 and Professional $240. Enterprise is sales-quoted. Pro/Enterprise MFA features differ by plan. [Pricing](https://auth0.com/pricing) | PO/finance: actual B2C/B2B classification, required MAU tier, annual vs monthly, taxes/currency, MFA factor entitlements, support, event/log and rate-limit costs. No quote or budget approval |
| Region | Auth0's official Teams SDK documents public-cloud locality values US, Europe, Australia, Japan, Canada and UK. [Auth0 SDK locality definition](https://github.com/auth0/teams-go/blob/main/tenants.go) | PO/legal/operations: current availability for the required plan, actual primary/replica/backups/logs/telemetry/support/subprocessors and cross-border access. This list neither guarantees residency nor proves another region unavailable; no region selected |
| Hosted recovery | A post-change-password Action can notify another system after a database-connection password reset/change; it runs asynchronously relative to the change. [Trigger](https://auth0.com/docs/customize/actions/explore-triggers/post-change-password) | Identity/security: connection coverage, event authenticity, replay protection, delivery delay, ordering, retries/loss and plan entitlement. A notification hook is not proof of prompt local invalidation |
| OIDC back-channel logout | Auth0 documentation states availability with Enterprise subscriptions and requires RP processing of server logout tokens. [Back-channel logout](https://auth0.com/docs/authenticate/login/logout/back-channel-logout) | PO/identity: confirm actual plan entitlement and price; implement and test local invalidation separately. Do not assume $35/$240 tiers meet the recovery/logout requirement |
| Initiators | The documented configurable initiators include password-changed, session-expired/revoked and account-deleted. They select session termination events rather than cause them. [Initiators](https://auth0.com/docs/authenticate/login/logout/back-channel-logout/oidc-back-channel-logout-initiators) | Identity/security: exact password/recovery/admin-reset/disable/account-link/MFA-reset coverage across every connection, all devices and event loss. MFA reset is not established by this initiator list |
| MFA factor removal | Official support guidance says removing a factor does not itself terminate current sessions or trusted-device cookies; those are separate operations. [Support article, updated 2025-09-10](https://support.auth0.com/center/s/article/Deleting-an-MFA-factor-does-not-remove-the-Trusted-Device-cookie-of-kill-any-current-session) | Identity/security/operations: supported end-to-end reset event, local epoch revocation and provider remembered-device/SSO invalidation. Never equate factor deletion with global logout |
| Local vs upstream logout | Ending FootPrint's future local session, Auth0 SSO and upstream social/enterprise SSO are separate operations. [Auth0 logout](https://auth0.com/docs/authenticate/login/logout) | Identity/security: exact registered post-logout destination, failure behavior, federation limitations and verified per-device/all-device semantics. No logout endpoint exists in this spike |

**Inference/recommendation:** Auth0 remains a realistic conditional managed option
for a small team, but recovery/MFA invalidation and Enterprise back-channel costs
may invalidate the assumed economics. Keep vendor selection open until an owner
obtains written capability/region/price evidence and a separately authorized
sandbox test. No contact, signup, provider provisioning or credential creation was
performed. Public documentation research is the only external provider activity.

| Maintained alternative | Strength / work FootPrint would own | Feasibility conclusion |
| --- | --- | --- |
| First-party identity service using Django's maintained auth/server-session primitives | Built-in password/session/reset machinery and session authentication hashes; MFA, recovery assurance, notification delivery, abuse controls, patching, operations and FastAPI integration remain the team's work. Current-password changes may deliberately preserve the caller's session, so FootPrint's future all-session policy still needs explicit enforcement. [Django auth/session docs](https://docs.djangoproject.com/en/5.2/topics/auth/default/) | Viable fallback after a separate ADR and ownership decision. No Django dependency or first-party credential store introduced here; no custom password cryptosystem |
| First-party-hosted maintained Keycloak OIDC service | Mature OIDC/back-channel functions; own hosting, database, TLS/hostname trust, upgrades, backup and recovery operations. [Keycloak admin guide](https://www.keycloak.org/docs/latest/server_admin/index.html), [hostname security](https://www.keycloak.org/server/hostname) | Another candidate if operations capacity is funded. Product capabilities do not prove the chosen configuration's recovery/MFA invalidation. No service installed or provisioned |

No option is automatically approved, cheaper in total cost, legally compliant or
independently assessed. Named owners, hosting, retention and legal review from 6A
remain unresolved. Proposed 30/14/30-day periods are not finalized by this work.

## Future same-origin BFF contract — not implemented

The local experiment returns an internal `(issuer, subject)` value, then the HTTP
callback discards it and redirects to a fixed completion path. It creates no user
or authenticated session. Two fictional subjects share an unsolicited email claim;
that claim is never requested as a scope, returned as identity, logged or used for
linking. Email equality, verification flags and names must never choose an account.

Future 6B-02 needs an independently reviewed interface from validated issuer/subject
to server-owned identity and an opaque revocable server session. It must add
initiation CSRF/Origin/Fetch-Metadata protections, exact production callback and
TLS/proxy handling, cookie rotation, idle/absolute expiry, logout/all, current
account/epoch checks and fail-closed stores. The spike cookie is only a one-use
five-minute protocol binding, never a reusable login session. These functions are
not present and are not authorized in PR #7.

Recovery/MFA-reset dependencies for 6B-02 and later independent review:

1. Enumerate password change/reset, account recovery, MFA enrollment deletion/reset,
   provider account disable/delete/link changes and administrator recovery. Establish
   exactly which authenticated event covers each; unspecified events block live go.
2. Validate event issuer/audience/signature/type/time, bind the exact issuer+subject
   or session ID, reject event replay, and handle delivery retries/out-of-order events.
   Never use an email address or untrusted webhook field as ownership proof.
3. Advance the local auth epoch and revoke all affected sessions under the same owner
   fence as future mutations; recheck at commit. Prove logout cannot race a writer.
   Local logout must succeed even if upstream logout fails.
4. Test recovery invalidation end to end against the separately approved provider,
   including loss/delay/outage. The <=60-second target in 6A remains a proposed gate,
   not an achieved latency or vendor SLA. Polling/log review alone must not silently
   substitute for the reviewed guarantee. No event ingestion exists in this spike.
5. Account for trusted devices, upstream SSO and every existing local session;
   independently review recovery assurance/MFA fallback and operator controls.

No live provider claim is proven by the local mock. This deliverable ends at
feasibility and protocol review, not production authentication readiness.
