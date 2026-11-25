# Phase 6C-01 proposed admission security boundary

Written before implementation. New endpoint inventory: GET `/_admission/csrf`
requires current fictional principal and origin; POST `/_admission/validate`
requires the same principal, distinct action CSRF, explicit test-seeded consent,
exact consent epoch and expected revision, bounded strict body, structural
validation and complete registry equality. Both exist only when the ASGI fixture
is explicitly constructed with `enabled=True`; default has no routes/state/keys.
There is no normal app import/mount/OpenAPI, serving CLI, environment activation,
socket, Node executor, DB, disk write, save route or public consent/admin bypass.

Server issuer+subject-derived owner is mandatory; client owner/user/tenant/header
claims, Authorization, path/query identifiers and unknown fields are denied.
Consent controls are two-owner bounded synthetic in-memory test data, initially
not granted. Trusted Python test setup can explicitly grant/change/withdraw
fictional admission consent, separate from local-processing or future save
consent. No browser API grants it. Corrupt controls/registry/session fail closed.
Each granted control also pins the fictional session auth epoch; a new epoch
requires trusted test setup to grant consent again. This is not durable consent.
Direct Python calls run the same authorization preconditions before serializing
or validating supplied data, then revalidate every envelope field; Pydantic object
type alone is insufficient because `model_copy`/`model_construct` skip validation.

Order: exact transport/host/path/header checks; authentication; same-origin;
action CSRF and current explicit consent; media/length/transfer checks; bounded
stream; strict JSON/depth; typed envelope/preconditions; owner fence; revalidate
session/epoch/CSRF/consent/revision; test barrier; revalidate; structural/registry
membership; cancellation and final guards; fixed validation-only receipt with no
await between final guard and receipt creation. No admitted batch state is stored.
Logout/recovery uses unchanged subject fence. Admission-first may finish before
invalidation; invalidation-first denies queued admission. Already delivered
receipts cannot be recalled; canceled/delayed work cannot publish stale authority.
No distributed/durable guarantee or timing indistinguishability is claimed.

Fixed error body: `{"code":"ADMISSION_FIXTURE_REJECTED"}`. Status: 401 absent/
invalid/revoked principal; 403 origin/CSRF/no explicit consent; 409 stale consent
epoch/revision; 413 body ceiling; 415 unsupported media/encoding/transfer;
422 malformed/extra/unregistered payload; 404 unknown fixture route; 503 corrupt
or missing trusted state. No input, field location, ID or exception reflection.
Inherited malformed cookie framing (duplicate/oversized cookie headers or repeated
recognized cookie names) returns fixed 400 before principal resolution. This
documented exception preserves the unchanged Phase 6B parser; it grants no access.
Inherited no-store/no-cache/no-referrer/nosniff/restrictive CSP on every response.
Fixture transport replaces the entire handled URL with a fixed fixture URL,
including authority/user-info/path/query/fragment, before HTTP client logging; body/
schema exception details are never logged. External proxy/APM/browser retention
and hostile in-process Python code are outside this never-served harness.
Catalog startup also bounds each binary read before hash/decode/schema checks,
including the overflow-detection byte and the canonical file's framing newline.

Security cases map to MA-03/04/05 (TM-07/08/09), MA-06 (authorization/consent and
revocation races), MA-07 (isolation), MA-08 (sentinel nonreflection). All registered
profiles and mutants must exercise both structural and membership gates. Passing
synthetic tests is not independent security approval or source attestation.
G-S3 still lacks actual restricted-role PostgreSQL/RLS/endpoint tests. Durable
consent/session, distributed fences, production browser/provider, legal/retention,
accountable ownership, independent security, P5-F01/P5-F02 remain unresolved.

Additional adversarial evidence: [AI assurance](PHASE6C01-AI-ASSURANCE.md) records
three OPEN defects: lossy trusted-Python unknown-field serialization, direct
catalog serializer-warning reflection and case-sensitive raw-ASGI header
rejection. Runtime behavior remains unchanged; direct-object, header rejection
and no-log guarantees must be read with those exceptions. No repair, risk
acceptance or independent approval is supplied by that evidence-only change.
