# Phase 6C-01 additional AI-assisted adversarial assurance

2026-11-25. Examined PR #11 head:
`40dee27ddde7208cbcce4c4a142fff98cc977066`. Base/main:
`d6b2afde058d57e23a75b903b40231dba56a2157`. Fetch and GitHub metadata confirmed
the expected head/base, synchronized clean branch, open/unmerged PR and mergeable
state before testing. No GitHub approval or review status is changed by this work.

**Outcome: three additional OPEN defects: two trusted-Python issues and one
direct-ASGI header-rejection gap. No different-owner or unregistered-batch
admission was demonstrated. This is adversarial testing by Codex,
the same implementing assistant, not an approving reviewer, independent human
assessment, exhaustive proof or certification. Qualified independent human
approval remains missing; the merge gate remains unsatisfied.**

Runtime code, policy, registry and application behavior are deliberately unchanged
as requested. The findings below are not fixed in this assurance change. Proposed
repairs require a separately authorized implementation/retest decision. The earlier
two fixed findings R6C01-01/02 remain historical; these new cases expose additional
limits of that hardening. A green CI with the explicitly recorded expected failures
must not be represented as all security expectations passing.

## Open findings and exact reproductions

### AA-01: unknown Pydantic copy fields are silently discarded

Severity: **Medium for the documented direct Python contract**, limited exposure.
Affected interfaces: `AdmissionFixture.validate` and `SyntheticRegistry.admit`;
not the strict JSON HTTP entry point. Requires trusted in-process caller access;
fixture admission additionally requires a current valid principal, action CSRF and
explicit fictional consent. Does not change owner, grant consent, accept a different
canonical batch or save anything. This is not a remote authorization bypass.

Reproduction using existing test helpers from `backend` (add `tests` to Python's
import path when running interactively):

```python
valid = AdmissionEnvelope.model_validate(envelope())
bad = valid.model_copy(update={"owner_id": "PRIVATE_OWNER_SENTINEL"})
assert "owner_id" in bad.__dict__
assert "owner_id" not in bad.model_dump()
await fixture.validate(principal, bad, fixture.csrf(principal))
# Actual: {"schema_version":"minimized-evidence-v1",
#          "mode":"fictional_batch_validation_only"}
```

`extra="forbid"` checks validation input, but `model_copy(update=...)` skips that
validation. The unknown key remains in the model's internal dictionary, while
`model_dump(warnings="error")` omits it without warning. Revalidating the serialized
projection therefore cannot detect it. The same result reproduces for envelope,
batch, source, observation, excluded row, context and commercial-group models, and
for a direct registry batch containing an extra `raw_body` field. Ordinary JSON
extras still fail with fixed 422. `model_construct` may discard extras during
construction itself; a downstream validator cannot recover discarded inputs.

Impact: violates the direct-interface promise to reject unknown fields rather
than silently drop them. It is inappropriate to treat arbitrary unvalidated model
instances as evidence that every original field was checked. The registered
projection still equals an approved complete batch; forbidden extra bytes are not
retained as admitted data or returned by the fixture.

Proposed fix, **not applied**: define a faithful direct boundary (for example,
strictly validated plain mappings) or recursively reject unexpected model state
before serialization, including nested models and Pydantic extras. Explicitly
document what can and cannot be recovered from already constructed objects. Do
not widen HTTP fields or weaken strict models. Recheck all seven object levels,
both direct entry points and HTTP rejection after any repair.

Regression evidence: eight strict expected failures in
`backend/tests/test_admission_assurance.py`, named
`test_unvalidated_extra_fields_must_not_be_silently_dropped` (seven levels) and
`test_direct_registry_must_reject_unvalidated_extra_fields`. They expect denial;
current code returns normally. `xfail(strict=True, raises=pytest.fail.Exception)`
limits the marker to the failed denial expectation; infrastructure exceptions
cannot count as reproductions. A future unexpected pass fails CI until the
finding and marker are explicitly reconciled.

### AA-02: direct catalog serialization warnings disclose supplied values

Severity: **Low**, trusted malformed-object/warning channel. Affected interface:
direct `SyntheticRegistry.admit`; not the HTTP route or the fixture's guarded
whole-envelope serialization. Reproduction:

```python
value = MinimizedBatch.model_validate(example())
value.sources[0].__dict__["record_count"] = "PRIVATE_COUNT_SENTINEL"
with warnings.catch_warnings(record=True) as emitted:
    warnings.simplefilter("always")
    registry.admit(value)  # raises fixed Denied(503)
# A serializer UserWarning contains PRIVATE_COUNT_SENTINEL.
```

The default `batch.model_dump()` warning policy in `admit` emits Pydantic's input
representation before the exception is converted to the fixed denial. With default
Python warning routing it can reach stderr; `logging.captureWarnings(True)` could
forward it to logs. The test captures warnings rather than sending a sentinel to
an actual logging service. No external log stack was tested. HTTP and fixture
serialization reject the corresponding known-field mutation without warnings.

Impact: the fixed error envelope does not by itself protect this direct warning
channel. A trusted caller injecting malformed private data could create a secondary
copy in captured stderr/logs. No production data or live logging system is involved.

Proposed fix, **not applied**: make direct serialization fail without emitting an
input-bearing warning, and normalize the resulting exception to a fixed denial.
Retest warning capture and DEBUG logs as well as response redaction; do not suppress
warnings globally or hide unrelated failures. Regression:
`test_direct_registry_must_not_emit_sensitive_serializer_warning`, one strict
expected failure restricted to its sentinel assertion.

### AA-03: mixed-case ASGI headers bypass prohibited-header screening

Severity: **Low**, authenticated fixture rejection-policy gap. Affected interface:
`AdmissionFixture.bff` raw ASGI HTTP scope, including `handle` and `streamed`.
HTTPX normalizes outbound header names, so the existing HTTPX cases hid this gap.
The [ASGI HTTP request specification](https://asgi.readthedocs.io/en/stable/specs/www.html#http-connection-scope)
permits case-preserved request header names; lowercasing cannot be assumed for all
valid ASGI producers. This is not a hypothetical change to a future public server.

With a valid A cookie/CSRF/origin/consent and a complete registered JSON envelope,
call `exchange(fixture, a, [raw], headers=[(b"content-type", b"application/json"),
(b"content-length", str(len(raw)).encode()), (b"X-User-ID", b"PRIVATE")])`.
Actual result is 200/fixed validation-only receipt/one body read. The identical
`b"x-user-id"` header returns 422/fixed error/zero reads. The same pair reproduces
for `X-Owner-ID`, `X-Tenant-ID`, `Authorization`, `X-Forwarded-Host` and
`X-HTTP-Method-Override`. `Content-Encoding` and `Transfer-Encoding` similarly
return 200 with case-preserved names versus 415 with lowercase names. Those probes
send plain JSON, not an actual compressed stream; no decompressor is introduced.

The application iterates header names without normalization for the ownership,
forwarding and method-override checks. Framework header lookup also assumes
normalized names for encoding/framing checks. Therefore it ignores the capitalized
claims instead of enforcing the explicit reject-on-presence policy. Authority
still derives from A's session; no owner substitution, different canonical batch,
actual compressed-content acceptance or persisted data was demonstrated.

Proposed fix, **not applied**: at the isolated admission ASGI boundary normalize or
fail closed on header names before any framework lookup, preserving duplicate
entries so host/cookie/CSRF/length ambiguity cannot be hidden by normalization.
Review all security-relevant header checks, not just the eight reproductions.
Do not modify the protected historical Phase 6B parsers in this evidence-only task.
Eight paired lowercase controls pass; eight capitalized strict expected failures
(`test_direct_asgi_forbidden_headers_must_be_case_insensitive`) require the same
fixed rejection and zero body reads. No HTTPX success is taken as proof about
raw ASGI scopes.

## Bounded test design, seeds and results by track

The new module adds **69 cases: 52 passing, 17 strict expected failures**. All
17 represent the three OPEN findings above, not skipped checks or accepted risks.
Four deterministic seeds **60101, 60102, 60103, 60104** each generate 256 leaf
mutation attempts (eight per canonical batch): **1,024 attempts**, not 1,024 pytest
cases or independently certified attacks. Mutations may be identity operations or
another registered batch; the property checks exact canonical catalog membership
rather than assuming every mutation must fail. No new dependency was introduced.

| Track | Executed evidence and practical limit |
| --- | --- |
| A: Pydantic boundary | Seven nested extra-field levels, direct registry extras, nine malformed known scalar values (bool, float, string, null, list, dict, negative/oversized integer), and seeded leaf/union mutations. Existing review tests still cover `model_construct` missing fields and `model_copy` consent-version/bool-int bypasses. AA-01/02 remain open. Hostile Python code is not sandboxed. |
| B: JSON/admission | Escaped duplicate/prototype names, lone/paired Unicode surrogates, control/Unicode values, 5,000-digit integers, negative extremes, underflow exponent and invalid JSON integer syntax reject with fixed envelopes. Equivalent ASCII key escaping/whitespace accepts the same registered meaning, but cannot authorize an owner key. Simulated digest collision returns 422 because canonical bytes must also match. Existing depth/array/duplicate/reference/adapter/timestamp cases rerun. No SHA-256 cryptanalysis claim. |
| C: streamed input | Valid bodies in one-byte fragments and with 64 empty frames, underdeclared/zero lengths, and all existing oversized/media/compression/framing cases rerun. Direct early disconnect raises `ClientDisconnect`; dispatch maps it to fixed 503, not 422. A blocked receive and 128 empty frames followed by a blocked receive remain pending until test cancellation: **no internal wall-time/frame-count bound demonstrated**. This was a documented residual, not a newly fixed guarantee. |
| D: identity/consent | Actual ASGI body consumption is paused between two fragments; expiry, recovery invalidation, consent epoch and revision changes then deny with 401/409 before a receipt. Unaffected B remains authorized except when the shared fake clock expires both. Eight header-case pairs expose AA-03 alongside passing lowercase controls. Existing 36 fence/cancellation cases, CSRF/origin/session/owner cases and both fictional identities rerun. No real browser/provider or distributed claim. |
| E: catalog | Changed profile selection, missing entry, altered byte count and duplicate entry cannot re-enroll the pinned manifest. Forced digest equality still requires bytes. Existing missing/corrupt/schema/canonical/oversized file cases rerun. Corrupt tests use disposable copies; no registry pin changes. |
| F: leakage | Both fictional clients receive fixed 422/no-store for sensitive feature sentinels with DEBUG and Python-warning capture. Existing entire-URL, authority/query/fragment/header and raw-field tests rerun. AA-02 exposes a separate direct warning channel. Proxy/APM/browser/OS retention is unverified. |
| G: preservation | Readonly offline generator reproduces 70 profiles/32 batches; separate Git/source/profile/engine/canonical audit verifies all 27 exact source hashes, 29 selections/six survivor selections plus reversals, engine provenance and server membership. All 193 protected historical files match base; prior ADR-015 through ADR-022 remain PROPOSED. Normal app/Phase 2/source gate/5000-ms worker deadline and default-disabled unmounted fixtures are unchanged. |

Test code blocks TCP connections, connection helpers and socket creation through
`create_connection` during test/generator work; clients use ASGI transports only.
Windows needs a loopback socketpair to initialize an asyncio wakeup pipe, so the
event loop is prepared before the connection guard and closed after each case.
This is not an OS egress sandbox or a claim of zero internal OS sockets. The first
test run blocked that wakeup pipe (35 harness failures, nine passes, nine expected
failures); the guard was corrected and expected-failure exception types tightened.
An intermediate lint/type check caught import order and a dataclass keyword-union
typing error; both were corrected in test code only. No application defect is
inferred from those harness errors.

All generated inputs are bounded: 1,024 small leaf attempts, at most 5,000 integer
digits in new parser probes, finite one-byte fragmentation, and 64/128 empty-frame
limits. Waiting probes use events, one-second outer waits and cancellation; they
do not run an infinite producer or consume unbounded memory. Test cleanup clears
in-memory fixtures. Prior historical oversized cases retain their original bounds.

## Reproduction, environment and validation evidence

From `backend`, using existing locked dependencies:

```text
uv run --frozen pytest -q tests/test_admission_assurance.py --tb=short
uv run --frozen pytest -q tests/test_admission_assurance.py --runxfail -k "unvalidated_extra_fields or direct_registry or (direct_asgi_forbidden_headers and True)" --tb=short
```

The first reports **52 passed, 17 xfailed**. The second intentionally exits 1
with **17 failed, 52 deselected**, demonstrating the unresolved assertions with
xfail disabled. It is a reproduction command, not a required green CI command.
The normal CI still runs all original cases; none was modified or marked xfail.

Local environment: Windows build 10.0.26200/AMD64; Intel64 Family 6 Model 142
Stepping 12; Python 3.11.9, uv 0.9.29, Pydantic 2.14.4, Starlette 1.10.0,
httpx2 2.16.2, pytest 9.2.0, Ruff 0.17.6, mypy 2.4.1, Node 22.15.0,
Vite 8.3.8, Vitest 5.1.1, tldts 7.5.5. These are deterministic correctness probes,
not performance or production capacity measurements.

Validation records distinguish passing regressions from open-finding expectations.
Command output/exit/timing evidence is retained locally under
`.local/phase6c01-assurance/`, including `backend.json`, `frontend.json`,
`preservation-environment.json` and `unmasked-findings-final.txt`. These ignored artifacts
are local evidence, not uploaded raw-data or CI artifacts. Reproduction commands
and tests are committed; CI independently executes the committed tests.

### Validation command inventory

All commands use frozen/locked dependencies. CWD `backend`:

```text
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy
uv run --frozen pytest -q
uv run --frozen python -m scripts.export_openapi --check
uv run --frozen python -m scripts.export_phase2 --check
uv run --frozen python -m scripts.validate_corpus
uv run --frozen python -m scripts.export_minimized --check
uv run --frozen pip-audit --cache-dir I:\FootPrint\.cache\pip-audit --progress-spinner off
```

CWD `frontend`:

```text
node scripts/admission/generate.mjs
npx.cmd tsc -p scripts/admission/tsconfig.json
npm.cmd run contracts:check
npm.cmd run lint
npm.cmd run typecheck
npm.cmd test
npm.cmd run build
npm.cmd audit --audit-level=low --cache I:\FootPrint\.cache\npm
npm.cmd run test:smoke
npm.cmd run test:performance -- --baseline
```

Frontend commands all exit 0: **284 tests, nine original Chromium scenarios,
seven original production privacy/rollback scenarios**, separate offline generator
(one Vitest case iterating all 70/32), contracts, lint/types/build and zero reported
dependency vulnerabilities. Original oversized-chunk advisory and failed proposed
performance budgets remain; P5-F01 is OPEN. No benchmark candidate is reapplied.

Final full backend run: **1,014 passed, 17 xfailed** (1,031 collected cases);
all nine backend validation commands exit 0, mypy checks 44 files and the audit
reports no known vulnerabilities. The original **962 cases all remain passing**;
new expected failures do not relabel old tests. The pre-header full run recorded
1,006 passed/nine xfailed; the final 69-case focused run recorded 52 passed/17
xfailed. The full suite was rerun after adding header cases.
No local Docker/database roundtrip is claimed. Verify the original scaffold
upgrade/constraint/downgrade/re-upgrade in final-head CI; it is not RLS coverage.
CI still requires the original production privacy/rollback step and all prior tests.
The workflow remains unchanged by this assurance work.

## Exact assurance change inventory

Four files change relative to the examined head, with two additions:

- `backend/tests/test_admission_assurance.py` (new; bounded probes and explicit open-finding expectations).
- `docs/PHASE6C01-AI-ASSURANCE.md` (new; findings, evidence, risks and ungranted exception template).
- `docs/PHASE6C01-ADMISSION-SECURITY.md` (append the new exception cross-reference).
- `docs/PHASE6C01-REVIEW.md` (append the superseding evidence cross-reference).

The complete PR has **56 files: one modified baseline workflow and 55 additions**.
No application, experimental runtime, generator, schema, canonical batch, manifest,
old test, dependency, lock, deadline or CI policy changes in this assurance commit.
Verify with `git diff --name-status 40dee27ddde7208cbcce4c4a142fff98cc977066 HEAD`.
Final assurance head and exact-head push/PR CI/GitGuardian evidence are attached to
PR #11's description and delivery record, avoiding a self-referential document
commit hash. Every recorded run must be checked against that exact final head.

## Updated unresolved risk inventory

1. **AA-01 OPEN:** lossy direct-object validation; proposed repair and eight failing
   expectations above. **AA-02 OPEN:** direct serialization warning reflection;
   proposed repair and one failing expectation above. **AA-03 OPEN:** header-case
   rejection-policy gap; eight failing expectations. No risk acceptance recorded.
2. **Resource limits:** byte ceiling does not bound stream duration, empty-frame
   count, concurrent request memory or queues. Underdeclared bodies are consumed
   up to the byte ceiling before exact-length rejection. Disconnect produces fixed
   503. Do not infer availability hardening from body-size tests or expose this
   never-served fixture as public intake. No time/concurrency policy added here.
3. **Meaning/provenance:** catalog replay is public and validation-only; it proves
   complete canonical membership, not actual file selection, genuine identity,
   events, accounts or authoritative assessments. Allowed domain/time/context
   could still be sensitive for real people. Rejected bytes can reach an ingress.
4. **Lifecycle:** trusted consent seeding must use the owner fence; validation
   retains no batch or consent receipt. No durable/distributed consent, session,
   revocation, deletion or generation guarantee. Response transport yields after
   guarded receipt construction; already created/delivered receipts confer no
   reusable authority and cannot be treated as a durable commit or recalled data.
5. **Operational boundary:** no OS/interpreter sandbox, production browser/auth,
   proxy/APM log audit, secure memory erasure or real provider integration.
   Synthetic-only tests and secret scans are not independent certification.
6. **Prior gaps:** G-S3 still lacks restricted-role PostgreSQL/RLS/endpoint tests.
   CI's original scaffold migration roundtrip does not supply tenant isolation.
   P5-F01/P5-F02, vendor/Auth0, accountable ownership, legal/retention and qualified
   independent security approval remain unresolved. Prior ADRs remain PROPOSED.

## PROPOSED product-owner exception template: not granted

This blank template records a possible request for a narrowly scoped decision.
It does not grant an exception, approve merging, waive an existing review gate or
claim a qualified reviewer exists. A product-owner choice is separate from actual
qualified independent human security approval. Any policy change would need an
explicit recorded decision; this assurance task authorizes none.

| Required field | Proposed record to complete; currently NOT PROVIDED |
| --- | --- |
| Decision identity | Named accountable product owner, role, date, issue/decision link and exact candidate head/base |
| Requested exception | Evidence-only repository decision sought, rationale, alternatives, scope and why waiting/remediation was considered |
| Open defects | Explicit AA-01, AA-02 and AA-03 decisions, affected trusted interfaces, reproduction/retest evidence, named remediation owner and due date; no implied closure |
| Missing review | **Qualified independent human approval remains missing. AI assistance and green CI are not substitutes. Existing merge gate is NOT SATISFIED.** |
| Qualification/independence | Actual human assessor identity, relevant qualifications, independence/conflicts declaration, reviewed exact head/scope, findings and dated decision; leave PENDING until actually supplied |
| Risk and safeguards | Acknowledge stream/resource, header-case, warning/log, canonical replay and all prior gaps; retain default-disabled ASGI-only/no persistence/public routes/deployment limitations |
| Duration/revocation | Explicit expiry/review trigger, conditions invalidating the exception, named monitoring/rollback responsibility; new head requires renewed evidence |
| Decision | APPROVE REQUEST / REQUEST CHANGES / DECLINE, signed and linked by the accountable person; **blank here, no authorization inferred** |

PR #11 remains open and unmerged. No approval/review submission, gate completion,
Phase 6C-02, database schema, persistence, real users/auth/provider, deployment or
beta is performed. Return this evidence for a separate product-owner decision.
