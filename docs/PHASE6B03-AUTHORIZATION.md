# Phase 6B-03 authorization contract and inventory

Date: 2026-11-25 (Asia/Calcutta). Implemented **fictional ASGI test harness only**.
See the [plan](PHASE6B03-PLAN.md), [report](PHASE6B03-REPORT.md),
[6A ownership design](PHASE6A-SECURITY-DESIGN.md#4-ownership-authorization-and-rls)
and [inherited session boundary](PHASE6B02-SESSION-SECURITY.md).

## Activation, identity and repository boundary

Only `experiments.ownership_fixture.create_ownership_fixture(enabled=True)` enables
this experiment. The default has no routes, authority, repository state or keys.
There is no environment flag, module-level app, serving CLI or normal-app mount.
The enabled outer ASGI fixture mounts the existing session fixture and uses its
unchanged OIDC protocol, session store, event verification and owner fences.
Normal FastAPI routes, frontend, Phase 5 local processing, corpus, migrations,
contracts, dependencies and previous ADRs are unchanged.

`AuthenticatedPrincipal` is a frozen typed value: configured issuer, exact subject,
internal owner UUID, server session digest and auth epoch. `PrincipalAuthority`
resolves the current opaque cookie through `SessionStore.lookup`. The old session
record's `owner` is the validated fictional **subject** from `SessionStore.login`,
which accepts only the fixed configured issuer; it is not the new owner UUID.
The isolated read-only registry maps exact `(issuer, subject)` pairs to assigned,
deterministic fictional UUIDs. Email and display name never enter this registry
or authority lookup. Both IdP subjects have the same fictional email; they retain
different owners. An alternate issuer is rejected, not auto-provisioned or linked.
Production random UUID allocation and identity persistence are future work.

A principal is necessary to construct `SyntheticRepository` or obtain a handle via
`OwnershipFixture.repository`. Every handle operation validates the same principal
against current session owner, digest and epoch; a cached handle does not retain
revoked authority. The `OwnerRepository` Protocol covers all supported operations;
there is no public unscoped count/find/batch/join fallback. Private row/join/delete
helpers use the constructor-bound owner predicate. Missing context and principal
mismatch deny access; invalid record/lifecycle/cursor state fails closed.

**Explicit exceptions:** auth/session lookup occurs before tenant resolution and
has no footprint API. Private `_seed`, `_Memory` and fixture `_memory` are trusted
in-process test seeding, teardown, snapshot and corruption-injection facilities,
not repositories or HTTP APIs. Python name mangling is not a sandbox against
hostile code with interpreter access. No public admin/operator bypass exists.
Future adapters must run the endpoint and repository negative matrix rather than
assuming structural typing alone enforces isolation.

## Synthetic data and supported operations

Four deterministic seed records form one parent/child pair for each fictional
owner. Every record has `synthetic=True`, an exact UUID owner and ID, a fixed code
and bounded same-owner UUID links. B has `SYNTHETIC_B_ONLY_SENTINEL`; corruption
that attributes either user's distinctive code to the wrong owner is rejected.
New IDs are server assigned; mutations accept no prose or user-selected code.

Per owner: at most eight records and sixteen opaque cursor entries. Global state
contains exactly two owner lifecycle entries and two cursor maps. Lifecycle is a
**test-only** active flag, consent-epoch placeholder and monotonically increasing
generation, initially active/1/1. This does not establish actual persistence
consent, retention, deletion or recomputation. Inactive state, changed lifecycle
while waiting and stale generation reject with 409. Real consent capture and
durable lifecycle fences remain 6C work.

The repository supports read, create, update, delete, list/page, relationship
filter, count, child join, nested child lookup and atomic batch delete. All list
rows, totals, links and nested membership predicates require the principal owner.
Delete repairs incoming links only within that owner. B's changes cannot advance
A's generation, fill A's record/cursor allocation or influence A's order/count.
Ordering uses only owned record UUIDs, with no global offset or total.

Cursors are random opaque server entries bound to the complete principal
(including session digest), owner generation, exact relationship filter, page
size and offset. Foreign/random/manipulated/other-session cursors yield 404;
stale owned cursors yield 409; malformed syntax yields 422. Cursor entries are
bounded and only stale entries for that owner can be reclaimed when allocating.
No global count, B ordering key or cursor ownership claim is returned.

## HTTP contract and non-reflecting errors

Every ownership request requires current authentication, exact HTTPS BFF origin,
loopback ASGI client, exact Host/raw path and inherited Origin/Fetch Metadata.
Forwarding and method overrides are denied. Ownership headers (`X-User-ID`, owner,
owner_id, user_id, tenant_id and X-owner/X-tenant variants) and Authorization claims
are rejected rather than interpreted. Path/query/body ownership cannot establish
a principal. Only documented route shapes and exact query keys are supported.

Mutations use strict JSON, at most 2,048 bytes, no duplicate keys or nonfinite
numbers, no extra fields, and canonical lowercase UUID strings. Only `generation`
plus `links` (create/update), `ids` (batch) or neither (delete) are accepted.
`links`/`ids` are arrays of at most eight UUID strings; objects or ownership claims
inside arrays are rejected, and duplicate IDs are rejected. GET accepts no body.
Unknown/duplicate query keys and unsupported ordering/count filters are rejected.
Cursor syntax is canonical base64url. Unsupported methods, non-ASCII paths and
fixture-root requests are rejected before framework redirects or method errors
can reflect an unvalidated URL or identifier. CSRF headers must be exact lowercase
hex tokens; malformed non-ASCII values return fixed 403.

CSRF tokens returned by GET `/_ownership/csrf` are session-bound and separated by
create/update/delete/batch action. Standard HMAC-SHA256 domain separation derives
them from that session's random POST marker synchronizer value; they do not grant
identity. They cannot be used as the old marker token or for another action or
session. A successful ownership mutation rotates this base synchronizer value,
invalidating all old ownership tokens and the old POST marker token. The unchanged
marker operation also rotates that base. Failed mutations consume no token.
This coupling is confined to the composed fixture, not a production CSRF policy.

All ownership errors have exactly `{"code":"OWNERSHIP_FIXTURE_REJECTED"}`:

| Status | Meaning |
| --- | --- |
| 401 | Missing, invalid, expired, revoked or epoch-mismatched session/principal |
| 403 | Origin/Fetch Metadata/method override or missing/foreign/wrong-action/stale CSRF |
| 404 | Authenticated foreign or missing object/relationship/cursor; identical body and safe headers |
| 409 | Stale expected generation, stale owned cursor or inactive/changed synthetic lifecycle |
| 422 | Malformed/extra ownership input, noncanonical UUID, unsupported method/schema/media, oversized fixture body |
| 429 | Owner-local bounded capacity exhausted |
| 503 | Unavailable/corrupt session or repository state/publication failure |

The stricter fixture body limit maps to fixed 422 and does not change the old
session fixture's 413/415 contract or the normal application's limits. Uniform
404 comparisons use current-generation, valid authenticated requests; validation
and stale-state errors still have their documented precedence. No ID, email,
claim, submitted field, record value or exception detail is echoed in errors.
Every ownership response uses the inherited no-store/no-cache/no-referrer/nosniff
headers and restrictive CSP; no credentialed CORS or cookie-setting error response.
This does not claim timing indistinguishability.

The ASGI-only transport has no socket fallback, delegates only fixed existing
session/issuer paths, and scrubs every handled ownership request URL to
`/_ownership/redacted` before HTTPX logging/retention. It suppresses path IDs,
queries and cursors, without logging request/response bodies. Direct production
access logging, proxies, APM, browser history, database/executor logs and external
audit retention do not exist in this experiment and are not verified here.

## Revocation and publication

Each operation validates authority, snapshots synthetic lifecycle, takes the
existing **subject** owner fence, validates again, invokes the trusted barrier
hook, then revalidates current session, expiry, epoch, CSRF and lifecycle. Reads,
count and cursor allocation also use this fence. Mutation work uses a private
copy; every link and the complete batch must be owned before any publication.
Corrupt backing records never become an unscoped view.

After draft validation, cancellation and authority are checked again. Session
publication (idle touch and mutation token rotation) must succeed before the
private repository maps are replaced. There is no await between final validation
and publication; this is atomic only within one event loop. A process crash loses
the disposable fixture. Store failure, rejected input, cancellation, stale epoch
or generation cannot publish draft records or change another owner.

The same fence serializes local logout, logout-all and signed fictional recovery/
MFA-reset events. Write-first may commit before invalidation; invalidation-first
prevents the queued write. No stale handle can commit after revocation completes.
Accepted invalidation failure inherits quarantine behavior from 6B-02. Cancellation
before commit publishes nothing, including when a test hook swallows cancellation.
Data already delivered before logout cannot be recalled.

## Current server-side authorization inventory

The immutable [Python inventory](../backend/experiments/ownership_inventory.py)
records these checks; proposed rows are labels, never routes or permissions.
For all ownership rows below: current session, exact principal UUID scope,
active synthetic lifecycle, fixed errors and inherited origin protections apply.

| Current fictional family | Owner/session and mutation checks |
| --- | --- |
| Issuer GET `/authorize`, `/jwks`; POST `/token` | Existing pinned mock protocol only; no footprint access; PKCE/code/state/token validation unchanged |
| GET `/_session/preauth` | Anonymous bounded preauth material; no principal or footprint access |
| POST `/_spike/start` | One-use preauth CSRF; optional prior session rotation; no client identity |
| GET `/_spike/callback` | Narrow OIDC state/nonce/PKCE exception; validated issuer+subject, epoch snapshot; session establishment only |
| GET `/_spike/complete`, `/_spike/rejected` | Fixed outcome only, no footprint data |
| GET `/_session/me`, `/_session/csrf` | Current revocable session/subject fence; artificial marker or CSRF material only |
| POST/PUT/PATCH/DELETE `/_session/marker` | Current session/epoch, subject fence and method/action-bound synchronizer |
| POST `/_session/logout`, `/_session/logout-all` | Current session/CSRF, fence, revoke before response; all advances owner auth epoch |
| POST `/_session/step-up` | Current session/CSRF, same validated subject, rotation; actual MFA freshness unverified |
| Signed fictional recovery/MFA-reset harness | Authenticated pinned event/sequence and subject fence; no HTTP endpoint |
| GET `/_ownership/csrf` | Current principal and fenced lifecycle check; action-bound test CSRF material |
| GET `/_ownership/records` | Every row and relationship filter owned; page/cursor principal+filter+generation scope |
| GET `/_ownership/records/count` | Same owner/filter predicates; foreign filter and missing filter target match |
| GET `/_ownership/records/{id}` | Object owner predicate, no unscoped existence check |
| GET `/_ownership/records/{id}/children` | Owned parent plus every same-owner link |
| GET `/_ownership/records/{id}/children/{child}` | Owned parent and child, exact relationship membership |
| POST `/_ownership/records` | Server-assigned ID/owner, create CSRF, owned links, expected generation, final auth/lifecycle fence |
| PATCH / DELETE `/_ownership/records/{id}` | Owned object/links, action CSRF, expected generation, final auth/lifecycle fence |
| POST `/_ownership/records/batch` | Every ID owned, batch CSRF, expected generation; one atomic draft, no partial delete |

Normal `/api/v1/health`, `/api/v1/demo` and `/api/v1/phase2/validate` retain their
existing public loopback synthetic contracts. They provide no principal or access
to this fixture. Normal OpenAPI contains no ownership/session experiment routes.

## Future proposed families: not implemented or mounted

| Family | Required owner/session checks | Consent/generation and lifecycle checks still required |
| --- | --- | --- |
| Collections, imports, sources, observations | Current session; server owner on every row/create; composite owner+collection FKs | Explicit save consent, consent epoch/revision, minimized synthetic admission, active/not expired/deleting |
| Relationships, unresolved findings, assessments, support/provenance | Same owner/collection on every join/nested read/list/filter/count/cursor | Current eligible generation; no pending deletion/expired consent; consistent rule/support versions |
| Available actions and mark opened | Owned current relationship; exact domain/type, no client URL/status | Current generation and eligible directory version; active/not revoked; mutation CSRF |
| Remove source, clear, withdraw, expiry | Owner fence; current browser session or separately authorized trusted job; scoped idempotency | Consent/revision fence, atomic recomputation, deletion intent/journal; no extra MFA for ordinary removal |
| Account deletion and receipts | Fresh authentication for account deletion; revoke all; separately scoped minimal receipt | No footprint access through receipt; journal acknowledgement and lifecycle completion |
| Background jobs, restore, operators | Trusted persisted job/control owner and separate least-privilege roles; no queue-payload authority | Epoch/generation/restore reconciliation, audited maintenance; no public admin bypass |

All future families also need actual restricted database roles, composite integrity,
forced RLS and pool-reuse/direct-SQL negatives. The existing scaffold migration
roundtrip covers none of those requirements. **G-S3 remains missing.**

## Cross-tab scope and unresolved limitations

Tests model two tab views with a local generation ticket and a data-free
`invalidate` signal, reject delayed A responses after logout/account switch, and
exercise a second ASGI client reusing the revoked shared cookie. The helper is
under `backend/tests` only; no real BroadcastChannel, frontend login, browser TLS,
cookie propagation or session integration was added. Existing nine Chromium tests
still cover the Phase 0-5 synthetic application, not experimental authentication.
Inherited issuer/BFF ports share a cookie hostname: separate provider jars and
issuer Cookie rejection remain mandatory. **Never serve this fixture.**

Locks, session authority, cursor state and data are single-process and ephemeral.
No database/RLS, durable consent, tenant schema, cross-worker revocation, production
key custody, live recovery/provider logout, actual saved footprints, secure memory
erasure or real-world identity/provider coverage is established. Two-user tests,
more test cases and GitGuardian are not independent security assurance. TM-15
proxy/database/executor/operations retention cases and full TM-06 browser login
races remain future work. Previous ADRs remain PROPOSED; no new ADR is needed for
this already proposed bounded experiment. Stop for product-owner and independent
engineering security review with the PR unmerged, before any next phase.
