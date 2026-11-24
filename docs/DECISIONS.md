# Phase 0 decisions

Date: 2026-11-22. Scope: local scaffold only. These are implementation decisions,
not independent security approval or permission to process personal information.

## ADR-001 — Phase 0 overrides broader MVP P0 priorities

Accepted. Documents 02–05 use P0 for source/feature priorities; document 06 uses
Phase 0 for repository and contracts only. Follow the explicit handoff: no
parsers, fixture corpus/ground truth, discovery, classifier, account integration,
action directory, deletion service, auth implementation, deployment, or real data.
The five pillars remain visibly planned in the shell. Phase 1 has not begun.

## ADR-002 — Review candidate schema without installing personal-data tables

Accepted for the scaffold. `03-pv1-schema.sql` remains unchanged as design input.
The reviewed executable migration `backend/migrations/versions/0001_scaffold.py`
creates only an empty `scaffold_metadata` table, with a primary key and a CHECK
restricting its phase value to `phase0`. Alembic creates its revision table.
Downgrade drops only scaffold metadata. No seeds, extension privileges, users,
observations, or findings are needed to demonstrate migration mechanics.

Review of the candidate DDL:

- Composite owner foreign keys are useful, but do not implement authorization.
- Free text and unrestricted JSON can admit sensitive material; postpone them.
- Placeholder retention is not an enforceable expiry/deletion policy.
- `user_actions.action_id` does not enforce the relationship's organization.
- Cascade deletion alone does not recompute surviving assessments.
- Verified retention/sale/confirmation states need claim-specific evidence gates.
- Migration/app role separation, tenant tests, backup reconciliation, and possible
  RLS remain required before real-user persistence.

Installing the entire candidate now would add unused, insufficiently reviewed
storage. Personal tables require a later explicit schema review and migration.
The local developer DB role owns only this disposable scaffold; the API has no
database driver calls or credentials. It is not a beta application role design.

## ADR-003 — Read-only, versioned, empty contracts

Accepted. `/api/v1/health` reports process liveness, not DB readiness.
`/api/v1/demo` returns API version, synthetic mode, and three empty collections.
Future output types describe minimal observations, evidence links, and separate
assessment dimensions. Collection lengths are constrained to zero in Phase 0.
No request model, raw-file endpoint, metadata bag, user identity field, or
operational processing service is exposed. Retention/sale remain `unknown`;
`confirmed` is excluded. Vocabulary is provisional until later fixture review.
Domain fields are bounded placeholders, not a domain-normalization implementation.

Pydantic generates committed OpenAPI, and openapi-typescript generates client
types. CI checks both for drift. One empty synthetic JSON response is shared by
unit tests; it is not a Phase 1 evidence corpus.

## ADR-004 — Local transport and disposable database

Accepted. Client, API, and PostgreSQL commands bind to loopback. The Vite proxy
forwards `/api` to the local API, avoiding a broad CORS policy. No third-party
scripts, fonts, telemetry, or external model calls are included. CSP allows Vite
development HMR locally. A fresh per-process nonce permits Vite's inline React
refresh preamble; the browser smoke test caught the initial missing nonce.
This is not a production serving configuration or a production nonce policy.
API access logging is disabled in documented start/smoke commands.

`.env.example` has an empty password; README generates a new disposable local
password into ignored `.env`. Only migration tooling reads it. PostgreSQL image
is minor-version pinned; Docker pull/start and image scanning require Docker.
Patch upgrades and dependency audit databases must be rechecked over time.

## ADR-005 — Defer unresolved baseline choices

Document 02 proposes 1 MB/100 email files and 10 MB/50,000 history records;
document 04 proposes 5 MiB/20 files and 20 MiB/10,000 records. Neither is a locked
product requirement. No limit is selected because no parser or ingestion exists.
Resolve with synthetic stress tests before Phase 2, with approval for material
scope/security choices. Exact Chrome nesting, retention values, authentication,
hosting, encryption/backup operations, action ownership and verification remain
open. PRD's `04-threat-model.md` reference points conceptually to the supplied
`04-security-privacy-architecture.md`; no required document is missing.

## ADR-006 — Tooling and verification boundaries

Accepted. Lock direct npm/Python dependencies exactly and commit transitive npm
and uv locks. Use Python 3.11, Node 22, npm 10, and uv 0.9.29 for this baseline.
Normalize the original directory spelling `Docs` to `docs` for Linux CI paths.
At the initial handoff Git had no commit or remote. During Phase 0 validation,
the user supplied `https://github.com/ankit8github/FootPrint.git` for the reviewed
scaffold push and remote CI. See the report for executed commands and outcomes.
No deployment workflow exists.
The first remote run showed that ubuntu-latest now selects Ubuntu 26.04, which
has no setup-python build for the pinned Python 3.11.9. Pin CI to Ubuntu 22.04,
verified in actions/python-versions' manifest, and guard DB cleanup on `.env`
existence when setup fails before database initialization. These are Phase 0
validation fixes, with no product behavior or dependency changes.
The Phase 0 report distinguishes observed local results, native PostgreSQL
fallback checks, local Docker Engine absence, the failed initial CI run, and
the successful Docker-enabled clean-checkout run on Ubuntu 22.04.

Reference checks: [Vite prerequisites](https://vite.dev/guide/),
[FastAPI output contracts](https://fastapi.tiangolo.com/tutorial/response-model/),
[PostgreSQL 17.12 release](https://www.postgresql.org/docs/release/17.12/).
These inform tooling choices; they do not replace local validation.

## ADR-007 — Explicitly authorized Phase 1 artifacts only

The user's subsequent Phase 1 request supersedes the historical Phase 0-only
working scope for this corpus work. Runtime behavior and Phase 0 contracts,
tests, lockfiles, migrations, and CI remain unchanged. The new corpus is under
`tests/fixtures/pv1/v1/`; the only executable addition is offline artifact
validation and its tests, discovered through existing pytest configuration.
The scripts package marker gives mypy a single stable module name for the new
test-helper import. There is no import adapter, parser, normalizer, classifier,
deletion engine, external model call or new API endpoint.

Ground-truth labels are hand-authored proposals with source-byte hashes, literal
evidence anchors, reasons and explicit before/after-deletion snapshots. The
validator checks integrity and references, not the semantic truth of a label.
Independent human adjudication remains pending in the review PR; no fictional
reviewer approval or accuracy metric is invented. Timestamp/sensitivity/source
handling expectations are corpus proposals, not implementation of Phase 2+
policy. Invalid times are annotated null; missing required history time is an
explicit excluded-record case. Existing unresolved parser limits stay open.

The Chrome wrapper and UNIX-microsecond timestamp meaning were checked against
the official source linked in the corpus README. The fixed reference clock
and reserved fictional domains make review reproducible. General `.eml`
ignoring stays in force, with one narrow corpus-directory exception. Scoped
Git attributes preserve fixture hashes across Windows/Linux. Corpus inventory
metrics do not measure product precision/recall or deletion correctness.

## ADR-008 - Relationship taxonomy clarification (PROPOSED, NOT APPROVED)

The [Phase 1 taxonomy proposal](PHASE1-TAXONOMY-PROPOSAL.md) makes the four
existing, coexisting relationship types and their independent evidence/priority
dimensions explicit for review. It calls out the ambiguous meaning of
`transaction` for contradictory payment evidence (c07) and an unpaid invoice
(c21), plus the separate record-validity/time questions in c12. The broad
transaction-indication interpretation and a narrower alternative require human
adjudication; neither is silently adopted as a new settled definition here.

The [blank human worksheet](../tests/fixtures/pv1/v1/HUMAN-REVIEW-WORKSHEET.md)
provides raw references for all 29 cases and six independent deletion setups.
Reviewers save blind judgments before comparing the proposed manifest or this
note. Existing source bytes, manifest labels, metrics, tests, contracts and CI
remain unchanged. No independent approval, corpus-version change, merge or
Phase 2 authorization is recorded by preparing these review materials.


## ADR-009 - Product-owner-approved Phase 1 baseline (ACCEPTED)

Date: 2026-11-23. Status: **product-owner-approved, AI-assisted baseline**.
The explicit product-owner finalization instruction supersedes ADR-007/ADR-008's
pending decisions and the historical proposal's common timestamp/sensitivity
choices. See [the accepted taxonomy record](PHASE1-TAXONOMY-DECISION.md).

Transaction means financial/commercial interaction evidence, not completed
payment. c07 retains Sensitive/Low with contradictory payment claims. Strict MVP
P0 excludes all six invalid/missing browser-history timestamps in c12. c21 is an
unpaid invoice with Medium/Medium, asserting neither payment nor retained credentials.
Corpus 1.1.0 records this approval basis; independent_reviewer remains null and
independent blind human review was not performed. No human reviewer is fabricated.

All 29 cases and six deletion snapshots are validated as authored artifacts;
no parser/classifier/deletion engine accuracy is measured. Original 1.0.0 materials
are archived, original blind worksheet/checklist/proposal remain unchanged, and
Git history is retained. The v1 schema-major directory now holds baseline 1.1.0.
The owner authorized merging existing PR #1 into main only after checks pass,
then stopping. No Phase 2, deployment or real-user processing is authorized.


## ADR-010 - Phase 2 browser-local synthetic import boundary (ACCEPTED)

Date: 2026-11-23. Authority: the user's explicit Phase 2-only implementation and
limit-reconciliation instruction. This supersedes the historical Phase 0/1-only
working scope for these changes, not their recorded results or approved taxonomy.
Base is main at `f0d7974e620e5d11b5fa923669a47a6afa97e5e3`; work is on
`phase2/local-synthetic-import`, with a review PR and no merge/deployment authority.

Browser `/phase2` is a separate transient import lab. `/` remains the Phase 0 empty
shell, `/api/v1/demo` stays empty, and all Phase 1 artifacts remain unchanged.
Only exact SHA-256 bytes from the approved corpus 1.1.0 may reach the UI adapters.
A checkbox, filename or synthetic header alone is insufficient: the browser worker
checks the bundled source-hash registry before decoding/parsing. Hash comparison
necessarily reads a selected file locally; rejected bytes never reach an adapter.
This bounded allowlist intentionally prevents importing newly authored or real
exports through this demo. Pure adapter functions are exercised with generated
fictional stress inputs in tests, without weakening the UI gate. Registry hashes
are public synthetic integrity values, never personal identifiers or anonymization.

### Reconcile documents 02 and 04 (supersedes ADR-005's deferred limits)

| Control | Document 02 proposal | Document 04 proposal | Phase 2 enforced choice |
| --- | --- | --- | --- |
| Email size | 1 MB | 5 MiB | 1 MiB = 1,048,576 bytes per email |
| History / combined size | 10 MB per batch | 20 MiB history | 10 MiB = 10,485,760 bytes total across all files, also maximum history file size |
| Files | 100 | 20 | 20 per batch |
| Records | 50,000 | 10,000 | 10,000 across all selected sources, including duplicate/excluded/unresolved rows |

Use the smaller proposed capacities and explicitly resolve MB's ambiguous units
as binary MiB. Reject before file reads when metadata exceeds a budget; never
truncate or silently fall back to raw server processing. Whole-file reads are
bounded; parsing runs in a module worker terminated after five seconds or on
cancel/consent withdrawal/unmount. No silent continuation in the main thread.
Synthetic tests cover 10,000 vs 10,001 rows, 1 MiB vs +1 byte, 20 vs 21 files,
10 MiB vs +1 byte metadata/huge JSON, MIME floods, nesting and malformed inputs.
These are development bounds, not a supported real-user performance guarantee.

Additional independent structural bounds: JSON nesting eight, strings 16,384
characters, lexical scan budget two million non-skipped characters, URL 4096
characters; MIME headers 16,384 characters (UTF-8 messages still bounded by bytes),
physical header lines 998 characters, 16 total MIME entities, four nested multipart
levels below root. Hitting any bound fails with a fixed code. A file under its byte
budget may still fail a structural budget. API: 8 MiB actual streamed request body,
20 sources and 10,000 aggregate normalized/issue records; duplicate source IDs,
record indices and invalid duplicate references are rejected.

### Safe extraction and deliberate limits

`tldts` 7.5.5 supplies bundled public-suffix ICANN and PRIVATE normalization; see
[its primary documentation](https://github.com/remusao/tldts/tree/master/packages/tldts).
No runtime suffix download or DNS lookup. Normalization tests separate
`example.co.uk` and private-suffix tenants; adapters emit only reserved `.test`
domains. Malformed/local/private/IP/non-web URLs fail closed. All URL paths,
queries, fragments, userinfo and ports are discarded from output.
Chrome requires a safe integer UNIX-microsecond timestamp in 1970-2100 inclusive;
submillisecond precision is retained in UTC. All six c12 invalid/missing times
are excluded, never replaced by import time. Email's strict RFC2822 numeric-offset
Date subset may yield explicit invalid/missing null time, consistent with c11.

MIME is a deliberately narrow, bounded subset, not a general mail client. It
supports CRLF headers/folding, plain UTF-8/ASCII text, multipart mixed/alternative,
and validated base64/quoted-printable text (including encoded ISO-8859-1). Raw
message bytes must be UTF-8. Duplicate/malformed headers, unsupported encodings,
message/rfc822 and malformed multipart fail closed. Subjects/display names,
Message-ID, body text and decoded text are never output. HTML is ignored entirely;
HTML-only evidence is unresolved, rather than rendered or converted into a claim.
Attachment headers identify ignored parts before payload decoding; no attachment
payload processing occurs. No embedded URL, image, script or instruction is used
for a network call, UI link or tool action.

All email observations are `unclassified_observation` / `EMAIL_RECEIVED_UNVERIFIED`.
They report claimed sender domain only, with unverified origin. Contradictory
transport/authentication headers become unresolved; a claimed authentication pass
never establishes trust. This is syntax/minimization, not discovery, account
inference, merchant attribution or sensitivity classification. Accordingly Phase 1
relationship labels are preserved, not used as parser-prediction targets.

Deduplication is limited to exact raw history rows within one selected source.
Distinct paths/times stay separate after minimization. Identical selected emails
and separate copies retain different random source IDs. No cross-source fusion,
confidence increase or stable raw-content fingerprint is emitted. Duplicate rows
cite an earlier normalized row index in the same source. Such transient references
are not a source-deletion/recomputation engine.

### Strict boundary without a data pipeline

`POST /api/v1/phase2/validate` is an independently mounted validation-only FastAPI
app. It rejects multipart/non-JSON before body parsing, bounds actual body bytes,
rejects duplicate/prototype JSON keys and non-JSON constants, and applies frozen,
strict Pydantic models forbidding extras at every level. No raw bodies, addresses,
subjects, URLs, arbitrary metadata, filenames or excerpts are allowed. Only
canonical `.test` domains, versioned codes, UTC dates and safe provenance survive.
Validation failures return static codes without Pydantic input/error details or
logs; successful replies contain a count only. It has its own generated OpenAPI
and TypeScript contract; the original Phase 0 contract stays unchanged.

The UI never calls this boundary: no raw or minimized import record is uploaded.
The endpoint is a future-boundary validation exercise, not persistence or an
analysis service. It cannot prove that an arbitrary API caller's claimed
synthetic-only data really originated in the corpus; it strictly restricts shape
and `.test` vocabulary. It remains loopback-only, unauthenticated synthetic demo
infrastructure, not safe multi-user hosting. No PostgreSQL connection, schema
change, auth, OAuth, external model, discovery/fusion, rules, action directory,
live link or deletion engine is introduced. Results and selected bytes exist only
transiently; workers terminate on completion, results clear on explicit clear or
page lifecycle, and no browser/server storage, telemetry or raw-content logs are
used. Production guarantees and independent security review remain future gates.

## ADR-011 — Phase 3 transient synthetic evidence features and linking

Date: 2026-11-23. Status: accepted for the explicitly authorized Phase 3 scope;
implementation submitted for PR review. Builds on ADR-009/010 and corpus 1.1.0,
whose status remains **product-owner-approved, AI-assisted baseline**. No
independent blind review or reviewer is claimed.

### Evidence gap and smallest extraction layer

Phase 2 emails deliberately carry unclassified, unverified sender observations.
A sender domain cannot establish an account, transaction or marketing relationship.
Keep `/phase2` output unchanged. Add an optional safe-plain-text visitor to the
bounded MIME reader and a separate `email_features_v1` extractor, used only by
Phase 3. The shared exact-byte SHA-256/adapter allowlist runs before decoding.
It still rejects arbitrary fictional examples as well as personal exports.
Pure functions accept generated synthetic adversarial inputs only in tests.

Recognize a narrow explicit vocabulary: account requested, account notification
preferences changed, paid-order claim, cancelled-before-payment claim, unpaid
invoice claim, and newsletter cue. No fixture IDs, case labels or manifest
expectations are imported by runtime code. An unencoded ASCII subject newsletter
cue can support Low-confidence marketing (c15); this uses no HTML evidence.
HTML/attachments remain ignored, encoded subjects remain inert. Only decoded
plain MIME parts enter feature matching, bounded to 16,384 aggregate characters
in addition to ADR-010 bounds. Quoted/markup lines and inline quotes are removed;
explicit example/forwarded context and instruction-injection markers suppress
relationship inference. These conservative patterns support the approved corpus,
not general language understanding or comprehensive spoofing detection.

Transport-header contradictions retain `ORIGIN_CONFLICT`; claimed authentication
passes never upgrade trust. Missing/unsafe sender domains remain excluded or
unknown. Embedded URLs supply no attribution or claims, and are never fetched.
PSL normalization, reserved `.test` domains and strict URL/time controls are
inherited. All six invalid/missing c12 Chrome times remain excluded. Invalid
email time stays explicitly null/invalid, without replacing it with import time.

### Deterministic linking and provenance

`phase3-discovery-v1` / `relationship_fusion_v1` runs wholly in a separate worker.
Source IDs follow selected-file order (`s0001`); event IDs contain source and
zero-based adapter row. Given the same ordered bytes, graph IDs/order/output are
reproducible. Reordering or removing sources renumbers batch-local IDs; no stable
personal identifier, raw-content fingerprint, filename or Message-ID is emitted.
The inspector shows the minimized typed graph as inert React text only.

Email deduplication requires exact approved byte copies, not same Message-ID,
sender/domain, time or extracted features. History deduplication requires exact
raw rows within a source, or the same row of an exact selected file copy. Distinct
paths/times or separate nonidentical files are not collapsed after minimization.
Copies retain separate source/event identities and duplicate-role support links;
primary support references one canonical copy. Deduplication never raises confidence.
Unresolved copies remain independently visible instead of being silently dropped.

Group eligible evidence by exact canonical domain and claim type, with no fuzzy
brand matching, delivery-provider ownership assertion or email/browser account
corroboration. Visits describe observed source records at High confidence, not
ownership or current accounts. Accounts are inferred/Medium, transactions
inferred/Medium and marketing inferred/Low. These are claim-specific rule tiers,
not calibrated probabilities. Additional copies/visits never promote them.
Every email relationship explicitly retains unverified sender attribution.

Transaction means evidence of financial/commercial interaction, not proof of
completed payment. Exact same-domain, case-sensitive order references are mapped
to opaque sequential aliases in a transient worker-local map. Plaintext references
and raw digests never leave the worker. No durable hash is substituted for a
potentially identifying commercial reference. Aliases are reproducible only for
the same ordered batch. Different references/domains cannot create a conflict;
multiple references in one message are unresolved. Both same-order paid and
cancelled-before-payment claims are preserved; c07 stays inferred/Low with an
explicit conflict, never last-message-wins. c21 stays an inferred/Medium unpaid
invoice interaction. Payment completion and retained credentials remain unknown.

Each relationship separates its own state/confidence from relevant unknown claims
(sender authenticity, current account, payment completion, retained credentials,
company retention, sale), whose state is unknown/confidence insufficient. No
sensitivity/review-priority classification runs; c07 Sensitive and c21 Medium
priority remain solely in the unchanged Phase 1 oracle for future Phase 4 work.
Unsupported, ambiguous, quoted and injected inputs produce explicit unknowns
with static codes and source-row support, not optimistic default relationships.

### Local boundary, evaluation and deferred work

No new API, database schema, personal-data migration or persistence is necessary.
The existing strict API deliberately rejects Phase 3 graph/features and arbitrary
metadata, raw fields, addresses, URLs and multipart uploads. Neither browser lab
calls it. No source content or graph is saved; termination discards worker-local
bytes/maps, and clear/unmount/consent withdrawal drops results. These are transient
lifetime controls, not secure memory erasure or a source-deletion engine.

All 29 cases and six deletion snapshots are read-only oracles. Survivor tests
independently analyze remaining input files; they implement no deletion API/UI or
mutable recomputation engine. Compare domain/type/state/confidence, canonical
support, unresolved support, exclusions and duplicate groups. Sensitivity and
review priority are explicitly unassessed. `PHASE3-METRICS.json` defines per-snapshot
domain/type TP/FP/FN and separately reports initial/survivor denominators. This
known, reused, overlapping synthetic development corpus is not a holdout set or
evidence of product accuracy. Original Phase 1 metrics/history stay unchanged.

Deferred: Phase 4 sensitivity; Phase 5 dashboard/actions/deletion; real-user input,
auth, persistence, external AI, live services and deployment. The draft personal
schema in document 06 remains a proposal and is not installed. See
[PHASE3-REPORT.md](PHASE3-REPORT.md) for exact checks, limits and review gates.

## ADR-012 — Phase 4 local contextual assessment and constrained explanation

Date: 2026-11-23. Status: accepted for the explicitly authorized synthetic Phase 4
implementation; PR review pending. This does not authorize Phase 5 or real users.

### Evidence gap and minimal context

The Phase 3 graph retains account, paid/cancelled order, unpaid invoice, newsletter
and valid visit features. It intentionally lacks c18's appointment-portal context.
A clinic-looking sender domain, display name or generic account claim cannot
justify health-context review. Keep all Phase 2/3 outputs/versions unchanged.
Add exactly one separate `email_context_v1` feature:
`CLINIC_APPOINTMENT_PORTAL_CONTEXT`, linked to its observation ID.

Require both a plain ASCII subject containing the narrow clinic-portal-account
cue and an unquoted plain-text appointment-portal account-request statement.
Subject is at most 256 characters; aggregate decoded plain text remains at most
16,384 characters. The existing bounded MIME/header/file/record/worker limits
apply. Encoded subjects, HTML, attachments, quoted/forwarded/negated/injected
context and origin contradictions cannot supply this feature. No domain/name
lookup or fixture/case ID is used to infer context. No diagnosis, treatment,
health condition or other sensitive personal-attribute value is extracted.

`assessSelectedFiles` obtains the unchanged Phase 3 graph through an optional
context sink on discovery. Only eligible account emails supply this single code,
derived from the exact same SHA-256/adapter-gated bytes used for discovery. The
sink receives observation IDs and enumerated codes, never raw MIME callbacks or
text. Source files are read once, avoiding a second-read source-integrity gap.
The ordinary Phase 3 call omits the sink and its output remains identical. All
work stays within the same five-second worker lifetime; no main-thread/server fallback.
Raw text and temporary buffers/maps die with the worker. No body/subject,
address, identifier, raw digest, URL or free metadata is emitted by this layer.
This is transient lifetime control, not a secure-memory-erasure guarantee.

### Assessment rules and separate dimensions

`phase4-assessment-v1` envelopes the unchanged graph, separately versioned context
and `sensitivity_rules_v1` assessments. Every relationship and explicit unresolved
item receives its own assessment; excluded rows and empty survivor sets receive
none. Review priority is independent of the original evidence state and ordinal
claim confidence. No domain-wide strongest-priority aggregation or risk score.

| Supported evidence | Priority | Rationale | Guardrail |
| --- | --- | --- | --- |
| Explicit likely-account feature | Medium | ACCOUNT_RELATIONSHIP | No current account activity claim |
| Account plus linked clinic appointment-portal context | Sensitive | ACCOUNT_RELATIONSHIP, HEALTH_CONTEXT | Contextual setting only; no diagnosis/person attribute |
| Same-domain/order paid and cancelled-before-payment claims | Sensitive | TRANSACTION_INDICATION | Preserve conflict; original Low confidence remains Low |
| Paid-order claim | Sensitive | TRANSACTION_INDICATION | Message claim, not established payment completion |
| Explicit unpaid-invoice-only evidence | Medium | TRANSACTION_INDICATION | Commercial interaction, not completed purchase/payment |
| Valid visit-only relationship | Low | VISIT_ONLY | Never becomes an account or payment claim |
| Explicit newsletter relationship | Low | MARKETING_ONLY | Never establishes retention/sharing/sale |
| Unresolved, invalid support or unsupported category context | Unknown | AMBIGUOUS_EVIDENCE | Never default missing evidence to Low |

Approved c07 and c21 taxonomy governs these rules. Other combinations outside the
corpus remain conservatively narrow: cancellation-only category priority is
Unknown even if the Phase 3 commercial relationship remains inferred/Medium.
Priority is not derived from confidence. Missing clinic context leaves a supported
ordinary account Medium rather than guessing health context from its domain.

Every rationale links only its supporting canonical observations; HEALTH_CONTEXT
links only observations carrying that context code. Primary source/domain/type
links are checked; missing/mismatched/stale/duplicate-primary support yields an
Unknown assessment without fabricated provenance. Duplicate copies retain the
Phase 3 alternate links and never raise priority/confidence. Removing contextual
or commercial evidence in a fresh subset cannot leave its rationale behind.
Deterministic source IDs still depend on input order: semantic labels/explanations
and source membership, rather than literal batch IDs, are compared across order
changes. No deletion/recomputation engine or stable personal identity is added.

Unknown claims explicitly cover sender authenticity, current account activity,
payment completion, retained payment credentials, company retention, data sale
and breach status, each unknown/insufficient. These never become verified or
confirmed. Context remains unverified sender content, not authenticated fact.

### Explainability, privacy and evaluation

Explanations and contextual limitations come only from finite reviewed text maps.
No raw excerpt, URL, personal identifier or source-derived interpolation is used.
The separate `/phase4` development inspector displays priority, state, confidence,
rationale support and limitations. It independently maps codes to fixed text,
ignores supplied prose, rejects unsafe display domains/IDs and renders escaped
React text. No filters, action links, source manager or Phase 5 dashboard workflow.

No API/model/schema/migration expansion: existing strict FastAPI/Pydantic boundary
rejects assessment/context/prose fields and multipart uploads, without echo/logs.
The browser sends neither raw nor minimized findings to it. No storage, telemetry,
auth, external model or network fetching is added. New tests cover context abuse,
prose/HTML injection, prototype keys, source support, Unknown, conflicts, duplicates,
semantic order/subset stability, worker lifecycle, egress, logs and browser storage.

Corpus 1.1.0 remains **product-owner-approved, AI-assisted baseline**; no independent
blind review is claimed. All 29 cases and six deletion survivor snapshots are
immutable test oracles, not runtime lookup tables. Original Phase 1–3 metrics and
reports remain historical and unchanged. New assessment agreement uses keyed
items, counts missing/unexpected outcomes as disagreements, reports Unknown and
excluded/empty snapshots separately, and is development-set only. Overlapping
authored examples do not establish real-world accuracy or beta readiness.
See [PHASE4-REPORT.md](PHASE4-REPORT.md) for exact results, limits and exit gates.

## ADR-013 — Phase 5 transient integration and source recomputation

Date: 2026-11-24 (Asia/Calcutta). Accepted for this explicitly authorized local
synthetic MVP implementation; product-owner/architecture PR review pending.
Earlier phase-only exclusions describe their historical handoffs. No real-user,
persistence, deployment or Phase 6 authority is implied.

`/phase5` composes the unchanged Phase 4 `assessSelectedFiles` entry point in a
fresh module worker and reuses `AssessmentDetails` fixed vocabulary rendering.
Phase 2–4 versions, exact approved SHA-256/adapter gate, reserved `.test` output,
MIME/JSON/resource limits and five-second deadline remain unchanged. No new
classification rule, API, contract, migration or personal schema is introduced.
Root and `/phase2`–`/phase4` behavior and tests remain intact.

A single `LocalSession` owns selected File references outside React state. It
retains those references until removal/clear/withdrawal/navigation/unmount to
support exact-byte recomputation; it does not read, concatenate or copy raw bytes
on the main thread. React receives safe source ordinals, minimized assessments,
static status text and opened action IDs only. File input is reset immediately.
Workers receive bounded structured-cloned File handles, read via the existing
gate, then terminate on completion. Temporary decoded text, buffers, feature and
commercial-reference maps die with the worker. Browser backing-store copies,
GC timing and OS memory/swap are not controlled; no secure-erasure claim exists.

Every removal immediately retires the entire previous graph, assessments,
priorities, rationales, provenance and opened state, then calls the same engine
from only the remaining File references. No partial graph mutation or business
rule duplication. Duplicate alternatives are rediscovered/promoted correctly;
confidence never rises from copies. Source labels remain selection ordinals,
while engine IDs renumber within the current ordered batch; provenance explicitly
maps these two identities. Unsupported relationships/action associations disappear.
Action state resets conservatively even for surviving relationships.

A worker identity guard rejects obsolete replies. Completion, timeout, worker
error/messageerror, constructor/post failure, supersession, clear, withdrawal,
pagehide and unmount terminate work and clear timers. Failures drop all source
references and require reselection; there is no main-thread or server fallback.
`pagehide` also withdraws consent, including potential back/forward-cache restores.
No persistent storage, logs, telemetry or raw/minimized upload occurs.

Dashboard counts remain per claim rather than per company. Priority, type and
confidence filter independently; unresolved evidence stays Unknown, excluded rows
are counted without assessment. Native disclosure details show observed records,
inferred claims, fixed reasons/limitations and primary/duplicate provenance.
Results paginate at 50 with complete counts; provenance and excluded indices show
up to 200 entries with explicit totals. The five-second budget governs worker
processing, not browser rendering or hardware-specific latency.

Source removal/clear concerns this local session, never external company records,
original disk files, persistent backups or verified deletion. No persistence or
backup system is implemented. Existing Vite chunk-size advisory remains a tracked
nonblocking performance concern; no unrelated bundling refactor or threshold change.

## ADR-014 — Literal reviewed synthetic actions; opened means opening requested

Date: 2026-11-24. Accepted for synthetic demonstration only; review pending.
Two literal HTTPS `.test` destinations have separate source-review records in
[PHASE5-ACTION-REVIEWS.md](PHASE5-ACTION-REVIEWS.md). Verification basis is the
reviewed synthetic design allowlist, not live endpoint validation, independent
human review, real ownership or a working privacy/deletion control. Each entry
is exact-domain plus explicitly supported relationship-type scoped. Neither a
claimed sender nor an inferred organization supplies or generates an official URL.

Links activate only on a user's explicit native link click, in a new tab with
`noopener noreferrer`. No automatic unsubscribe, revoke, delete, network discovery,
redirect following, embedded URL fetching or external-response interpretation.
`opened` means the opening request was activated; popup delivery or external
success cannot be verified. `.test` normally does not resolve. E2E locally
intercepts the exact destination rather than contacting it. Other findings show
**No verified direct link available** and cautious manual guidance.

Only `not started` and `opened` are implemented, transiently. No user-reported
completion or verified-external-response state is exposed. Every recomputation,
clear/withdrawal/navigation/unmount retires opened associations. No URL/state
endpoint or database row is added. Real-world directory operations, live URL
verification and automated actions require separate future review.

## ADR-015 — Proposed Phase 6 minimized transmission boundary

Date: 2026-11-24. Status: **PROPOSED for Phase 6A review, not implemented**.
The user's architecture-only instruction authorizes these specifications, not
auth, persistence, real inputs or deployment. Earlier ADRs and corpus labels are
unchanged. Full requirements: S6A-01/04/12/14 in
[PHASE6A-SECURITY-DESIGN.md](PHASE6A-SECURITY-DESIGN.md).

Recommend preserving browser-only raw parsing and exact synthetic SHA-256/adapter
gate, then a separate explicit opt-in to a strictly minimized new contract. Do
not widen the Phase 2 validation endpoint or treat its `.test`/boolean shape as
source attestation. Proposed later synthetic server admission checks independently
reviewed exact minimized batch profiles; client hash claims never authorize writes.
All intake remains disabled in 6A. Server recomputation needs typed feature/context,
duplicate-equivalence and collection/domain-local commercial aliases; it must not
retain raw hashes, references or assume minimized domain/time equality means copies.

Reject raw-server upload and client-supplied authoritative classifications. Reuse
the same pure TypeScript rules through a proposed bounded offline executor, with
versioned ID/provenance adapter and all 29/six oracle comparisons. This package,
executor and new transport do not exist yet. Review trigger: new fields/adapter,
admission scope, rules version, performance failure or any real-input proposal.

## ADR-016 — Proposed managed identity with opaque server sessions

Date: 2026-11-24. Status: **PROPOSED, conditional on independent review**.
Requirements S6A-02/03/08/11. Recommend Auth0 hosted OIDC and a same-origin FastAPI
BFF, with reviewed stable protocol client, PKCE/state/nonce, HttpOnly/Secure/Lax
host cookie containing only an opaque handle, digest-only server sessions,
synchronizer CSRF/origin checks, rotation, timeout and per-user auth epochs.
Provider plan/region/recovery-MFA invalidation support and costs remain unverified.
No IdP is installed, provisioned or contacted by the app in 6A.

Compared alternative: maintained Django authentication/server sessions as a
first-party identity service; it has greater recovery/MFA/email/operations burden
and stack complexity for this FastAPI repository. No custom password cryptosystem
or signed-cookie-only substitute. No provider/refresh tokens in the browser;
login-only design validates then discards ID token and requests minimal scopes.
Local logout revokes access independently of upstream logout; all sessions expire
or revoke server-side. Recovery/MFA reset must invalidate local epochs through
verified events before live release. Reviewer must prove behavior, not accept SDK
demo defaults. Review trigger: provider capability/residency mismatch, sharing,
recovery bypass, token retention or changed session/CSRF policy.

## ADR-017 — Proposed ownership, RLS and revised logical schema

Date: 2026-11-24. Status: **PROPOSED, no DDL executed**. S6A-03/04/12.
One user is one tenant. Session-derived internal UUID owns every personal query,
join, count and mutation; composite owner/collection/generation FKs prevent
cross-tenant evidence/action associations. Recommend explicit predicates plus
forced RLS, transaction-local tenant context and nonowner/NOBYPASSRLS runtime
roles. Auth session lookup is an isolated bootstrap role with no footprint access;
it cannot be treated as an already-established tenant context.

Candidate `03-pv1-schema.sql` remains unchanged and uninstalled. The proposed
revision replaces unrestricted metadata/prose with exact typed codes, preserves
duplicate/context members, models relationship and unresolved finding roots,
pins rules/explanation versions and matches actions by directory/domain/type/realm.
It permits no confirmed/verified retention/sale claims. RLS does not defeat a
compromised app setting its own context or a privileged DBA; roles, parameterized
SQL, safe errors and two-user negatives remain necessary. Test actual restricted
roles and pool reuse, not superuser-only migrations. Review trigger: new personal
table/metadata field, tenancy/sharing, privileged worker, schema or pool change.

## ADR-018 — Proposed consent epochs, deletion fences and restore journal

Date: 2026-11-24. Status: **PROPOSED; retention/legal decisions pending**.
S6A-05/06/07. Separate local-processing consent from explicit save/renewal.
Monotonic consent epoch/revision and owner locks reject stale writers/retries.
Durable deletion intent fences reads/writes; a bounded transaction fully rebuilds
survivor findings and removes selected data atomically. Failure leaves pending
unavailability, never the old graph. Completion requires deletion-journal outbox
acknowledgement; backups/processor completion are separately disclosed.

Use an independently durable minimal journal to reconcile older backups offline;
invalidate restored sessions and prove deletion/expiry/tenant isolation before
serving. No stale snapshot rollback that resurrects records. The journal is
pseudonymous personal control data with separately reviewed retention/key access.
The old 30-day derived-data, 14-day log and 30-day backup periods remain proposals,
not final schedules; passive activity must not silently renew persistence.
Source removal, withdrawal and logout do not gain an extra MFA barrier. Review
trigger: retention/expiry/hold change, concurrency design, journal coverage or
restore/replication/provider change. No saving/deletion service is added in 6A.

## ADR-019 — Proposed operations and genuine action verification

Date: 2026-11-24. Status: **PROPOSED, no hosting/integration enabled**.
S6A-08/09/13. Require separate runtime/auth/migration/restore identities, managed
secret/KMS custody, private DB/backups, reviewed production TLS/CSP, safe event
allowlists, MFA/JIT audited operator access and synthetic incident/restore drills.
No source domains/IDs/tokens or request bodies in ordinary logs/telemetry.
Current loopback headers and encrypted-backup intentions are not operational proof.

Keep existing `.test` actions explicitly synthetic-reviewed. A genuine verified
realm needs independent official ownership/URL evidence, two review roles,
version/expiry/revocation and a named revalidation custodian; no source-derived
URLs or automatic redirects/actions. Any future network checker is separately
isolated, authorized and protected against SSRF/DNS rebinding. Reviewed destination
drift remains a residual risk; `opened` is never successful deletion. P5-F02 stays
open. Review trigger: vendor/region/key/log changes, privileged access, real links,
network verification or new processor.

## ADR-020 — Proposed phased implementation, performance and approval gates

Date: 2026-11-24. Status: **PROPOSED; architecture review only**.
S6A-10/11/14. Use the PR-sized 6B–6D tasks and exact gates in
[PHASE6A-IMPLEMENTATION-PLAN.md](PHASE6A-IMPLEMENTATION-PLAN.md), the full
[threat tests](PHASE6A-THREAT-MODEL.md) and G-S1–G-S7 matrix in the design.
No passing paper specification or synthetic demo is a beta/security/compliance
approval. Real data, live identity/mail/social/action integrations, hosting and
invites each remain separately prohibited until explicit review and authority.

P5-F01's Vite advisory remains open; propose a separate measured route/chunk
remediation PR with initial/total/worker transfer and cold synthetic performance
budgets, never threshold suppression or unrelated 6A refactoring. Independent
legal assessment must resolve jurisdiction, staged legal commencement, processor/
hosting/transfer questions and proposed retention conflicts, including potential
CERT-In log requirements. No compliance claim or appointed reviewer is fabricated.
Review trigger: release scope, gate owner, legal applicability or new performance
budget. This ADR and 6A artifacts are proposals pending product-owner review.
