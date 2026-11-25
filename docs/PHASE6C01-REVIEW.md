# Phase 6C-01 engineering review and unresolved independent review gate

2026-11-25. Requested/reviewed head:
`227232a63621f66422a72f5c46d00d84e46a3856`, PR #11, base/main
`d6b2afde058d57e23a75b903b40231dba56a2157`. Fetch confirmed clean synchronized
feature branch and unchanged main. Review fixes stay in the same open PR.

**Reviewer: Codex, AI-assisted engineering review by the same assistant that
implemented this experiment. This is not independent human review.** No qualified
human reviewer, qualifications, independence declaration or recorded approval was
provided or found in GitHub review submissions. Independent reviewer conclusions:
**none recorded; independent human review NOT COMPLETE; merge gate NOT SATISFIED**.
Neither passing tests, this document nor empty GitHub reviews is approval.

## Findings and fixes

| Finding | Impact, reproduction and disposition |
| --- | --- |
| R6C01-01 — Medium, direct Python contract integrity | At the requested head, `valid.model_copy(update={"consent_version":"unsupported", "consent_epoch":True, "expected_revision":True})` received the validation-only receipt through `fixture.validate` with an otherwise valid principal/CSRF/consent. Pydantic copying skipped validation, type-only checking missed it, and Python bool/int equality satisfied epoch comparisons. **HTTP already rejected these values; this is not an anonymous/foreign-owner or HTTP registry bypass.** Fixed: authenticate/check CSRF and explicit consent before data work, then copy/strictly revalidate every envelope field. Seven unvalidated/missing-field cases now reject with fixed 422; two additional tests prove principal/consent denial precedes serialization. No data was saved before or after the fix. |
| R6C01-02 — Low, corrupt trusted artifact resource bound | Catalog loading used `Path.read_bytes()` before checking 8 MiB. A disposable oversized manifest caused **8389632 bytes** to be read before rejection. A larger corrupt local file could allocate unbounded startup memory. Paths/catalog are trusted and pinned; an HTTP caller cannot choose these files. Fixed: bounded binary reads before hashing/decoding, with one overflow byte; canonical files separately allow their trailing newline. Two reader-spy tests enforce positive bounded read sizes for oversized manifest and batch files and fixed 503 rejection. |

The 11 added regression cases exercise these findings, not duplicate historical
classifier rules. Both fixes are in the experimental fixture/catalog only. No
registered content, profile, source gate, field vocabulary, engine, dependency,
normal endpoint, database schema or persistence behavior is widened.

## Registry and provenance verification

Readonly `node scripts/admission/generate.mjs` reproduced **all 70 profiles and
32 distinct complete batches** using unchanged `assessSelectedFiles`, which
invokes the original gated parser/discovery/context/assessment pipeline. An
additional separate Python audit compared the 70 `(profile ID, ordered source
selection)` pairs against the exact manifest's 29 scenarios/six deletion lists
and their explicit reversals; every source ID/path/adapter/raw digest matched.
It verified all 27 selected approved source files, every LF-normalized engine
digest, every canonical file's exact serialized bytes/digest, source/row/reference
invariants and server registry membership. All six kinds occur; the 32 distinct
batches contain 49 observation instances (not an accuracy or independence metric).

| Immutable evidence | Verified SHA-256 |
| --- | --- |
| Original corpus manifest | `53b4ff49c5b31e4fa5b2670c757c02058d0ffab3f6b0472fe8d198a86bdd36b1` |
| Admission registry manifest | `333c513165273846a4645c74ba604900266d88e10fb6eda1848e0195949b0699` |

Engine/generator/lock hashes normalize CRLF to LF only; corpus hashes use exact
bytes. Expected oracle labels never compute generated evidence. Generator graph
and assessment digests are reproduced from engines, not treated as runtime input.
Registry membership is independent of browser hashes/flags/path assertions. It
does not authenticate actual source selection or event truth. Source ordering,
duplicates, deletion survivors and reversals are enumerated complete profiles;
arbitrary subsets, permutations or forged aliases do not authorize admission.

## Field allowlist audit: S6A-01/04/12 and TM-07/08/09

The [complete proposed contract](PHASE6C01-MINIMIZED-CONTRACT.md) remains separate
from Phase 2; exported schema stays offline. Reviewed accepted objects:

| Field family | Audit conclusion |
| --- | --- |
| Envelope and versions | Exact six batch version literals plus fictional consent-version/epoch/revision preconditions; strict integers and bounded arrays; no owner/tenant/user/hash/fixture assertion or client authority |
| Sources | Only ordinal source ID, adapter and row count; no filename, path, address, raw digest, display name or prose |
| Observations | Only batch-local IDs/row references, typed adapter/kind, one of 13 registered domains or unresolved null, UTC/time status, attribution and finite feature/issue codes, local order aliases and duplicate reference |
| History/email union | History requires visit feature, valid UTC/domain and browser attribution; email stays unverified sender, invalid/missing email times remain null; invalid history rows are excluded; no promotion to verified event/account |
| Excluded/context | Exclusion is code plus source/row reference; context is exactly the clinic portal context code on eligible account-support observations; no diagnosis/subject/recipient/attachment or other prose |
| Duplicate/commercial groups | Direct primary/member references, no missing member/cycle/chain; complete duplicate membership; commercial aliases/members match email observations in one domain/collection; no raw order/invoice identity or cross-domain equality |
| Outputs forbidden in intake | Relationships, assessments, confidence, explanations, certainty, retention/sale/breach status, human-readable labels and authenticated/verified claims are absent; unknown/nested fields reject rather than drop |

No raw identifier, email address, full URL, message ID, source content, arbitrary
prose or client-authoritative relationship/assessment is in any accepted canonical
batch. A scan of all canonical bytes for address/URL/raw-order/invoice/message-ID
sentinels agrees with the field-by-field audit; pattern scanning alone is not
the assurance. Deterministic engine kinds/features remain unverified evidence,
not authenticated account/payment/health assertions. No independent Python
classifier or shared Node executor is implemented.

Explicit scoped exceptions/proposals requiring human review:

- Future S6A-04 save-idempotency UUID is absent because this endpoint validates
  only and retains nothing; replay is allowed under current state. It never
  supplies an idempotent save guarantee or advance/clear operation.
- Ordinal source ID supplies the safe label; no separate label is transmitted.
  Observation/excluded partition and issue code carry disposition, rather than
  accepting a separate caller disposition or derived relationship output.
- Exact empty survivor batch is registered; validation of it does not clear data.
  Only enumerated source-order/duplicate/survivor profiles are permitted.
- Malformed cookie framing retains the inherited fixed **400** exception, before
  principal resolution; invalid/missing canonical session authority yields 401.
  A direct ASGI duplicate-cookie probe returned the fixed envelope with zero body
  reads. The Phase 6B cookie parser is unchanged; no identity/existence is exposed.
- Pydantic structural validity is **not sufficient admission**. Some possible
  issue/kind/feature combinations, timestamps and source row counts fit the model
  but are unregistered; exact whole-batch equality is mandatory. The broad existing
  issue vocabulary is not a Python implementation of engine/classifier semantics.
- Raw fictional source paths/digests and generated-output hashes exist in offline
  provenance only. They are forbidden in intake and absent from receipts. Engine
  hash/version/canonical/profile changes still require explicit review/re-pinning;
  nothing auto-enrolls caller content.

These exceptions do not approve future persistence, broader real input, executor,
canonical profile or architecture decisions. Prior ADR statuses stay PROPOSED.

## Structural, stream, logging and race audit

Strict extra-forbidden models and complete registry equality compose rather than
relying on a `.test` domain or a flag. Source/row completeness and uniqueness,
same-collection references, adapter-specific fields, context eligibility,
duplicate membership and same-domain commercial grouping were inspected against
the original engine outputs. Scalar/time/version/unknown-field mutations and
unregistered-but-structurally-valid inputs are exercised in the existing matrix.

POST authenticates current session/owner, exact origin, CSRF and explicit fictional
consent before consuming input where possible. It rejects unsupported media,
multipart, content/transfer encoding and missing/duplicate/malformed lengths;
requires actual streamed bytes <=8 MiB and exact length; checks depth 8, duplicate/
prototype JSON keys, nonfinite/floats, malformed encodings, bounds and no truncation.
Fragmented ASGI bodies with a valid length remain bounded; HTTP chunked transfer
is denied. Catalog files are now bounded before decoding as well. No new socket,
network listener, write adapter or production ingress policy was introduced.

Failures use fixed nonreflecting envelopes/statuses and safe inherited headers;
Pydantic inputs/errors are not serialized or logged. Entire handled transport URL
is replaced before HTTPX logging, including user-info, foreign host, path/query
and fragment. Existing DEBUG sentinel tests cover the fix. No raw fields or
submitted identifiers appear in receipts/errors/logged metadata in those tests.
This is not an assertion about a real proxy/APM/browser logging stack.

PrincipalAuthority still derives owner only from the pinned fictional issuer and
subject, not shared email or browser owner IDs. Consent is explicit trusted-test
state, separate from local processing/persistence consent, bound to owner/auth
epoch and revision. Revalidation occurs after owner-fence acquisition and the
barrier, and immediately before the fixed receipt without a later await in that
guarded section. Existing 36 barrier cases cover both lock orders for logout/all,
recovery/MFA reset, consent/revision, corruption and cancellation including swallowed
cancellation. Rejected requests retain no admitted batches or unrelated owner data.
Direct-call strict envelope validation is now checked too. Already delivered
receipts cannot be recalled. No distributed or durable guarantee is established.

## Preservation and residual risks

Git object comparison of all **194 baseline files** at the requested head found
exactly one modification, the additive CI workflow check. All **193 protected
historical Git contents** are unchanged, including normal app/frontend/Phase 2,
27 source files, 29 scenarios, six survivor snapshots, prior engines/tests/oracles,
dependencies/locks, migrations, source gate, exact 5000-ms deadline, previous Phase
6B fixtures and ADR-015 through ADR-022 (still PROPOSED). Review fixes alter only
files introduced by this PR plus the two new review/test files. The original
Docker scaffold and mandatory production privacy/rollback CI checks remain.

Residual risks/limits requiring qualified review remain:

- Public fictional catalog replay and exact membership cannot prove event truth,
  source selection, genuine identity/account or authoritative assessment.
- Allowed domains/context/times could be sensitive in a real product. Malicious
  callers can send forbidden bytes to an ingress; rejection cannot prove those
  bytes never arrived. Wire whitespace/object-key order is canonicalized, not
  registered literal wire syntax. No raw body persistence/logging is implemented.
- Test consent/control seeding and failure hooks are privileged Python facilities;
  callers must advance consent/revision under the shared fence. They are not a
  public consent/admin API or sandbox against hostile interpreter/OS control.
- Stream time/chunk-count/concurrency, production proxy/APM retention, OS network
  isolation, real browser login/consent/cookie integration, distributed locks,
  durable state/consent/revocation and secure memory erasure are unverified.
- **G-S3 missing**: no actual tenant schema, restricted-role/RLS/FK/pool/endpoint
  proof. Scaffold migrations do not fill this gap. P5-F01/P5-F02, vendor/Auth0,
  accountable ownership, legal/retention and independent security remain open.
- Synthetic test counts, reproducibility and secret scans are regression evidence;
  none are independent security certification or real-world accuracy measures.

## Review change inventory

Seven review-scoped files changed since the requested head:

- `backend/experiments/admission_fixture.py`
- `backend/experiments/admission_registry.py`
- `backend/tests/test_admission_review.py`
- `docs/PHASE6C01-ADMISSION-SECURITY.md`
- `docs/PHASE6C01-MINIMIZED-CONTRACT.md`
- `docs/PHASE6C01-REPORT.md`
- `docs/PHASE6C01-REVIEW.md`

The complete PR now has **54 files: one modified baseline workflow and 53
additions**. All 193 other baseline files remain untouched. Exact full inventory:

- `.github/workflows/phase0.yml`
- `backend/experiments/admission_data/.gitattributes`
- `backend/experiments/admission_data/01f4c8a43940a73d6e7af3bfd9ba51418adc0818d2bfae972e8e1bf90e965a0c.json`
- `backend/experiments/admission_data/05182012358675a48b3be7c68744881d660f0fb51806a4263805ac32dce23392.json`
- `backend/experiments/admission_data/0ca258725596ec07425a2363a2c484eafd8b3e45a1f8fadfbeb36d6a48e66b56.json`
- `backend/experiments/admission_data/1614358fb5f1ab2fa8a5166b00e30f24d18aed20d943b5cce691fbb3e2d2bc81.json`
- `backend/experiments/admission_data/1a92ac0d24e82ba64ebee247f3080d5cd855e418abb8b2d90ea9755f9069b061.json`
- `backend/experiments/admission_data/1d02ff6382508cf4233a63786745852c6edaa5c8544dd071c7cc2a4a8dc50795.json`
- `backend/experiments/admission_data/223f7880a7817fcc50af9f807916ce8aadec161e69d7182688f79586aa044048.json`
- `backend/experiments/admission_data/226ab03c713df9c314a5f92ed451b1d115d9a819fa406523e6568eca132894ec.json`
- `backend/experiments/admission_data/4207718c394467667704cabfcca2045706b30c974202b96307675e7c77d875e9.json`
- `backend/experiments/admission_data/505841681119045c99270e10ab7f21cce0f27a2f6ffc1bb3770104d2fe00e045.json`
- `backend/experiments/admission_data/55ac32eed45703e9cf9a5b51746f3ae1306a57371656417199ed09c4861a8031.json`
- `backend/experiments/admission_data/584428b34c383eeaa4f65df0f0be60a435cc0d0b4187243055eadf9a1b6a3638.json`
- `backend/experiments/admission_data/623d29db22dbe5c6906a3e2aa968ccd1bd15b97ba12aa6c1ab05f4dd8454dc1f.json`
- `backend/experiments/admission_data/6a1cf3f5ce9d3bb5df5657f1221fb83cbc2f958adbc436077f51fd384a6c33ac.json`
- `backend/experiments/admission_data/74c3b68542d5fd572b9dbec73365dc4b96a9d18218fe9cecfd14e8d4d37e35da.json`
- `backend/experiments/admission_data/783a7e890e949738f275ab13765787f8ff61cccace2dbd38faddaceb76a86ee2.json`
- `backend/experiments/admission_data/89ad7c7483352f83b3d46f01a11f1b38b51fb4ba2c6afeea7bb0de96e867c31f.json`
- `backend/experiments/admission_data/8bcb3c906f22ac4eb89d54e64352f56af3c0e067ab3172beb3aea5c39419167f.json`
- `backend/experiments/admission_data/8f751d10709895dc5225a12105c202ea9756b60bbeab68f63799dffd54dc95cc.json`
- `backend/experiments/admission_data/962558641febdaffdb369aa5f8525ac10cfc9db74a51089a8c5b1e5b19c9212a.json`
- `backend/experiments/admission_data/977b30d97b5d3b8c3753e101ee36937268275a5a946aa1dc20096c7654095262.json`
- `backend/experiments/admission_data/985a0c172de3acb01b06db79b20cb52b42e29eb9dad48484722087c80c5f2bfc.json`
- `backend/experiments/admission_data/ab72da64eb3618b2fd176a1af7c4f5a3486f3770fe6106a1418c5dc42f02539f.json`
- `backend/experiments/admission_data/b9ce2ed07aab8ab7228c77b5b841b1a2c9de845017e840bc12bf84801c06cd07.json`
- `backend/experiments/admission_data/c7189b4b53254af4f7df295ca57c9d7efcd798aa747e79dd572fe736ff5898ae.json`
- `backend/experiments/admission_data/d30911944817063ed7d8749559a46bc403202cda320f1a4b0f603da6b5ca6bb1.json`
- `backend/experiments/admission_data/d5f74ae049040ea3459294a23dd6f9a7675c8844016c73bbb16ac72fb4fd855a.json`
- `backend/experiments/admission_data/da720c83a26b946e3c47bf7a0dc006b0bd3c609a61ef36059a95d865857598f4.json`
- `backend/experiments/admission_data/dc5585a576f37436b9678e54e5584285621555caeedbfb0a192ce2de7d60b14d.json`
- `backend/experiments/admission_data/dd5a5ce54d4bd6ad428700ffb8ddefd25690fb43ff689889f083eaf57c512ae0.json`
- `backend/experiments/admission_data/ebbd3cc397e8557256cf940331b5e5991f1b65649188248eb048cc45f8ef822b.json`
- `backend/experiments/admission_data/f3e9a7c2cdcc8cb6511913071c5d2d9af3c3e9b9a41c4ae3fe27acce70fd4344.json`
- `backend/experiments/admission_data/manifest.json`
- `backend/experiments/admission_data/minimized-evidence-v1.schema.json`
- `backend/experiments/admission_fixture.py`
- `backend/experiments/admission_registry.py`
- `backend/experiments/minimized_contract.py`
- `backend/scripts/export_minimized.py`
- `backend/tests/admission_test_support.py`
- `backend/tests/test_admission_races.py`
- `backend/tests/test_admission_review.py`
- `backend/tests/test_minimized_admission.py`
- `docs/PHASE6C01-ADMISSION-SECURITY.md`
- `docs/PHASE6C01-MINIMIZED-CONTRACT.md`
- `docs/PHASE6C01-PLAN.md`
- `docs/PHASE6C01-REPORT.md`
- `docs/PHASE6C01-REVIEW.md`
- `frontend/scripts/admission/README.md`
- `frontend/scripts/admission/generate.mjs`
- `frontend/scripts/admission/generate.test.ts`
- `frontend/scripts/admission/tsconfig.json`
- `frontend/scripts/admission/vitest.config.ts`

## Validation and delivery

Focused new review regressions: **11 passed**. Full results: **962 backend cases**
(564 historical + 398 Phase 6C-01 cases, including the 11 review additions),
**284 frontend cases**, **nine Chromium scenarios**, **seven production privacy/
rollback scenarios**, and the separate one-case offline generator reproduction.
Mypy checks 43 files. Both audits, original/new schema exports, contracts and
corpus checks pass. No old test, fixture gate, budget or deadline was changed.
Full output/exit/timing records are captured under `.local/phase6c01-review/`
(`backend.json`, `frontend.json`, `audit-expected-head.json`).
Fresh final-head push CI, PR CI and GitGuardian are required before delivery and
recorded with their outcomes in the PR description and final response, avoiding
a self-referential documentation commit hash. Docker scaffold
roundtrip is verified in those CI logs; no local tenant/RLS claim is made.


### Exact executed validation commands

| CWD | Command | Result |
| --- | --- | --- |
| backend | `uv run --frozen ruff check .` | PASS |
| backend | `uv run --frozen ruff format --check .` | PASS |
| backend | `uv run --frozen mypy` | PASS |
| backend | `uv run --frozen pytest -q` | PASS |
| backend | `uv run --frozen python -m scripts.export_openapi --check` | PASS |
| backend | `uv run --frozen python -m scripts.export_phase2 --check` | PASS |
| backend | `uv run --frozen python -m scripts.validate_corpus` | PASS |
| backend | `uv run --frozen python -m scripts.export_minimized --check` | PASS |
| backend | `uv run --frozen pip-audit --cache-dir I:\FootPrint\.cache\pip-audit --progress-spinner off` | PASS |
| frontend | `node scripts/admission/generate.mjs` | PASS |
| frontend | `npx.cmd tsc -p scripts/admission/tsconfig.json` | PASS |
| frontend | `npm.cmd run contracts:check` | PASS |
| frontend | `npm.cmd run lint` | PASS |
| frontend | `npm.cmd run typecheck` | PASS |
| frontend | `npm.cmd test` | PASS |
| frontend | `npm.cmd run build` | PASS |
| frontend | `npm.cmd audit --audit-level=low --cache I:\FootPrint\.cache\npm` | PASS |
| frontend | `npm.cmd run test:smoke` | PASS |
| frontend | `npm.cmd run test:performance -- --baseline` | PASS |

Additional review checks: readonly generator reproduction before fixes, the
separate manifest/source/engine/canonical/Git-object audit, the direct unvalidated
Pydantic reproduction, disposable oversized catalog-read probe, duplicate-cookie
ASGI probe (fixed 400/zero reads), and `uv run --frozen pytest -q
tests/test_admission_review.py --tb=short` (11 passed). Ruff format/check and mypy
also ran on the focused fixes before full groups. No validation command failed.
Migrations are intentionally checked only in CI using the original scaffold.

## Required independent reviewer record: pending

| Required record | Status |
| --- | --- |
| Qualified human reviewer name/role and relevant qualifications | NOT PROVIDED |
| Independence from implementation/conflict declaration | NOT PROVIDED |
| Exact final head and reviewed scope, including all 70/32 profiles | PENDING |
| Decisions on the findings, field/profile proposals and explicit exceptions | PENDING |
| Test evidence, limitations and residual-risk disposition | PENDING |
| Dated recorded approval/request changes and product-owner gate decision | PENDING |

Engineering fixes and automated evidence do not satisfy this table. Keep PR #11
**OPEN and UNMERGED** until actual qualified review and approval are recorded.
No Phase 6C-02, schema/persistence, production auth/data/provider, deployment or beta.
