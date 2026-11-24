# Phase 6B-02: experimental session security

Date: 2026-11-24. Status: implemented fictional ASGI experiment, **not production
authentication approval**. See the [plan](PHASE6B02-PLAN.md),
[report](PHASE6B02-REPORT.md), [6A design](PHASE6A-SECURITY-DESIGN.md) and
[identity feasibility](PHASE6B01-IDENTITY-FEASIBILITY.md). ADR-015–021 remain
PROPOSED; ADR-022 proposes retaining this experimental boundary.

## Activation and trust boundary

`experiments.session_fixture.create_session_fixture(enabled=True)` is an explicit
Python test-harness call. The default factory has no routes, store or event keys.
There is no environment activation, module-level app, serving CLI, normal-app
mount, login UI or frontend change. Normal OpenAPI and historical APIs are intact.
The existing OIDC implementation, issuer and 84 tests are unchanged. The new
transport dispatches the new BFF and the fixed old issuer, never the old BFF.

The only owners are the fixed fictional issuer plus `fictional-a` or `fictional-b`.
Only `Protocol.finish`'s validated identity reaches HTTP session creation. Browser
JSON must be exactly `{}`; request ownership headers are rejected. Equal email
claims do not merge identities. Service methods and failure hooks are trusted
test-harness interfaces, not remote identity assertions or public APIs.

The transport uses ASGI calls only, exact HTTPS loopback origins/paths, no network
fallback, discovery or redirects followed automatically. Host, raw path, loopback
ASGI client and forwarded-header checks reject alternate routing. These assertions
do not establish TLS, trusted proxy configuration or browser enforcement.

**Cookies are not port scoped.** The inherited mock issuer and BFF use different
ports on the same loopback hostname. A real browser could send BFF cookies to that
issuer. The session transport rejects any issuer-bound Cookie header; tests use a
separate empty-cookie provider client. This is deliberate ASGI fixture isolation,
not a browser-compatible SSO deployment. Never serve this fixture. A future
separately reviewed deployment needs genuinely separate provider/BFF hosts and
real browser/TLS tests.

## Handles, metadata and lifecycle

Handles use `secrets.token_urlsafe(32)`: 32 random bytes, 43 canonical base64url
characters. Only SHA-256 digests index server records. No password or signature
scheme is invented. Cookies hold the opaque handle alone, never identity claims,
OIDC tokens or JWT payloads. Records retain the digest, fixed owner key, epoch,
creation/last-seen/absolute timestamps and seven action-bound synchronizer tokens.
Records suppress their repr. Control records hold active/quarantine flags, epoch,
event sequence and an artificial marker count; no footprint or personal data.

| Resource | Bound and behavior |
| --- | --- |
| Sessions | Eight total, four per owner; reject capacity exhaustion without live eviction |
| Owners and locks | Exactly two fixed fictional subjects, one lock each |
| Preauth entries / OIDC attempts | Sixteen each; five-minute server deadlines; expired entries pruned on successful allocation/start |
| CSRF values | Seven 32-byte random values per authenticated session, one per method/action |
| Marker / epoch / event sequence | Integers bounded at 1,000,000; reject exhaustion |
| Browser JSON / cookies / signed event | At most 64 bytes / 1,024 characters / 4,096 characters |

Idle expiry is `now - last_seen >= 1800`; absolute expiry is
`now >= created + 43200`, using the server's injected monotonic clock. Valid reads
or marker commits may refresh idle time. Rejected requests do not refresh it.
Rotation retains the original creation/absolute deadline, even across a modeled
account switch; it does not extend the twelve-hour window. Fresh login after an
expired cookie requires a new OIDC transaction and creates a new lifetime.
The durations are experimental proposed values, not finalized product policy.

Successful login and modeled step-up allocate a new random handle and CSRF set,
atomically retire the old record and check current owner epochs under ordered
owner locks. Step-up additionally requires an existing valid session, its CSRF
token and the same validated issuer+subject; it does **not** prove actual MFA or
provider authentication freshness. Unknown fixation cookies cannot select a
session. Preauth and OIDC binding cookies never become authenticated handles.
An OIDC attempt captures epochs before exchange; recovery during exchange makes
its later callback fail rather than resurrecting access.

`__Host-fp_session` is Secure, HttpOnly, SameSite=Lax, Path=/, no Domain. It has no
Max-Age/Expires: server expiry is authoritative. Both binding cookies have the same
security attributes and five-minute Max-Age. Deletion uses the same attributes,
Path=/ and Max-Age=0/expired Expires. A lost logout response cannot restore a
revoked handle. Browser session restoration remains outside this experiment.

Cleanup takes both owner locks and removes expired records. Expiry is checked on
every protected operation regardless of cleanup. Fixture teardown and ASGI
lifespan shutdown discard session/pending maps, OIDC state and event-key references
and mark the store unavailable. Python memory/crypto objects are not guaranteed
zeroized; cancellation after publication but before cookie delivery may leave a
bounded unreachable record until cleanup/expiry. No persistent storage is used.

## HTTP and CSRF contract

Every non-callback BFF request, including reads, requires exact Origin and Fetch
Metadata: BFF origin, `same-origin`, `cors`, `empty`. No permissive fallback for
missing/duplicate values, credentials-enabled CORS or proxy/method overrides.
Every POST/PUT/PATCH/DELETE also requires exactly one X-CSRF-Token and exact allowed
JSON media type (`application/json`, optionally `; charset=utf-8`), bounded strict
JSON `{}`. No identity data or marker contents are accepted.

| Endpoint | Authority and effect |
| --- | --- |
| GET `/_session/preauth` | Same-origin bootstrap; random binding cookie plus memory-only CSRF value; no authentication |
| POST `/_spike/start` | Unexpired binding and one-use preauth token; starts bounded existing OIDC flow |
| GET `/_spike/callback` | Sole GET establishing/rotating authentication; exact registered redirect, one-use transaction cookie/state, nonce, PKCE and all old token checks |
| GET `/_session/csrf`, `/_session/me` | Validate session/store/owner/epoch under fence; tokens or fictional marker count; successful idle touch |
| POST/PUT/PATCH/DELETE `/_session/marker` | Valid session and method/action-specific CSRF; consume token and atomically increment artificial in-memory marker |
| POST `/_session/step-up` | Valid session and one-use action token; initiate fictional reauthentication, never assert MFA performed |
| POST `/_session/logout`, `/_session/logout-all` | Valid session and action token; revoke before response and delete session cookie |
| GET completion/rejection | Fixed fictional mode only |

Synchronizer values are returned in no-store responses for a hypothetical
memory-only client; no frontend or browser storage API is introduced. Replays,
cross-session and cross-action tokens fail. GET bootstrap/CSRF reads allocate
security material or touch idle metadata; they cannot commit a marker or logout.
The old issuer's token endpoint is an isolated OAuth back-channel form exchange,
not a browser session mutation. There is no event HTTP/webhook route.

Errors use fixed, non-reflecting bodies; callback failures redirect to a fixed
queryless rejection path. Every BFF response is no-store, no-cache, no-referrer,
nosniff and has a restrictive CSP. The ASGI transport scrubs handled URL queries
before HTTPX logging; it does not prove upstream ingress/browser-history scrubbing.
No production logging adapter is added. SameSite is additional protection, not
the sole CSRF defense. XSS that can execute within the origin can still obtain
CSRF values; HttpOnly alone does not prevent authenticated request abuse.

## Revocation fence and failures

Every protected request checks store availability, record shape/digest binding,
expiry, owner activity/quarantine and current `auth_epoch`. Missing, corrupt,
expired or mismatched state fails closed. Marker commit and invalidation use the
same owner lock. The marker rechecks session, epoch, expiry and CSRF after its last
suspension and publishes without an intervening await.

| Lock order / failure | Required result |
| --- | --- |
| Marker first | Marker may commit, then revocation removes authority; subsequent stale commits fail |
| Logout/all/event first | Invalidation finishes before waiting marker rechecks; marker cannot commit |
| Logout | Remove current digest before acknowledging; other owner sessions remain valid |
| Logout-all / accepted recovery event | Advance owner epoch and remove all owner sessions; other owner unaffected |
| Provider unavailable | Local logout still revokes; response explicitly says upstream unverified |
| Invalid browser/event authentication | No session, epoch, marker or identity-state mutation |
| Store/publication failure | Fixed failure, no success acknowledgment; no partial marker publication |
| Cancellation before lock acceptance | No revocation claimed; existing session may remain valid |
| Accepted invalidation fails/cancels after fence | Quarantine owner before suspension; stale access stays denied even if availability returns |

Quarantine is an intentional security-state change for an **authenticated**
invalidation attempt, not for malformed/rejected requests. A correctly signed
next-sequence event can retry and complete invalidation; otherwise tear down the
fixture. A store outage before browser logout authentication cannot establish an
accepted revocation: no success is reported and no durability guarantee exists.
There is no automatic reactivation. Ordered dual-owner locks prevent modeled
account-switch deadlocks. These locks provide only one-process/one-event-loop
serialization, not database transactions or distributed revocation.

## Fictional recovery and MFA-reset events

The trusted harness generates a short-lived ephemeral RSA key; maintained joserfc
verifies pinned RS256 signatures and exact header/claim shape, issuer, audience,
identity issuer+subject, kind, integer times, sixty-second maximum lifetime and
sequence bounds. A fixed-owner strictly-next sequence rejects duplicates and gaps
without an unbounded replay set. Out-of-order future events fail until missing
events arrive; this is a fictional delivery contract, not a verified Auth0 event
format or availability guarantee. Event kind is recovery or MFA-reset; either
advances epoch under the same fence. Invalid signatures/authentication never reach
the store. There are no provider credentials, webhook provisioning, key rotation
or actual recovery/MFA operations. Production authenticated delivery, retries,
durable ordering, monitoring and provider coverage remain unresolved dependencies.

## Evidence and remaining gates

The [report](PHASE6B02-REPORT.md) maps SS-01–SS-12 to executed tests. They cover
both barrier-controlled race orders, failures/cancellation, cookie header
serialization, leak guards, lifecycle teardown and original-app route absence.
ASGI assertions do not establish real browser TLS/cookie/CSRF behavior. Existing
Playwright runs exercise the unchanged synthetic product, not a browser login UI.
Python-level network/write guards are regression evidence, not OS-level isolation
or forensic proof of erased memory. No tenant isolation, durable revocation,
backup deletion or production security readiness is claimed.

Future authorization is required for production credential/key custody, TLS and
proxy trust, provider selection/events, durable session storage, account recovery,
tenant repositories and independent security review. The six 6A ADRs and Auth0
selection remain conditional; named owners, legal/retention decisions and review
gates remain unresolved. No Phase 6B-03/6C, real imports, provider provisioning,
personal-data persistence, deployment or beta users are authorized here. P5-F01
bundle remediation and P5-F02 genuine action verification remain future issues.

Design references reviewed 2026-11-24: opaque handles/server-side lifecycle and
rotation follow [OWASP session guidance](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html);
synchronizer tokens plus origin/Fetch Metadata checks follow
[OWASP CSRF guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).
Cookie prefix, host/path and attribute semantics are documented by
[MDN Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie).
These references inform the experiment; they do not certify its implementation.
