# PV1 — Security & Privacy Architecture

**Product:** Personal Digital Footprint & Privacy Intelligence  
**Document:** 04 | **Version:** 0.1 | **Date:** 2026-11-22  
**Status:** Proposed controls for engineering; **NOT IMPLEMENTED, AUDITED, OR APPROVED FOR REAL USER DATA**  
**Inputs:** `01-product-requirements.md`, `02-source-feasibility.md`, `03-evidence-data-model.md`, `03-pv1-schema.sql`

## 1. Decision and non-goals

PV1 helps a person **discover, analyze, classify, visualize and act on** evidence of online relationships from files the person explicitly selects. Initial adapters are `email_eml_v1` and `browser_chrome_json_v1`. `.mbox`, OAuth, social media, cookies, SMS and password-manager imports are **not** dependencies of the first MVP.

**Proposed first-release architecture:** perform initial file selection, format verification, parsing and secret stripping **in the user's browser, when feasible**. Send only validated, minimized observation records to the FastAPI backend for relationship matching, assessments and optional user persistence. A fully local single-user demonstration may precede multi-user cloud sync. No whole-inbox upload or persistent background monitoring.

Non-goals: inspecting company databases; declaring that a company currently retains or sold data based on email/history; storing raw passwords, card credentials, authentication cookies or mailbox archives; automated revocation or deletion; general-purpose browser/app surveillance.

**Security invariant:** the product must not create a more dangerous centralized copy of the sensitive material it promises to help people understand.

## 2. Threat model

### 2.1 Assets and actors

- **Assets:** selected source files in browser memory, derived observations, account/organization relationships, sensitivity assessments, evidence links, action history, session credentials, user identity and any encryption keys.
- **Trust boundaries:** user's local files → browser parser; browser → API; API → PostgreSQL; developer/admin access → operational environment; action-directory outbound link → outside websites.
- **Actors:** legitimate user, accidental file uploader, attacker with a stolen session, malicious email/URL author, malicious user uploading crafted files, compromised dependency, rogue administrator, third-party service, and a different tenant trying to access another user's records.

### 2.2 Abuse cases and required defenses

| Threat | Consequence | Required defenses | Validation |
|---|---|---|---|
| Cross-user object ID access (IDOR/BOLA) | Another person's footprint disclosed | Authenticate every request; server-derived `user_id`; ownership queries for every import, observation, assessment and action; optional PostgreSQL RLS as defense in depth | Two-user tests: all foreign IDs return no data and cannot be mutated |
| Malicious `.eml` / JSON | Parsing exploit, XSS, resource exhaustion | Size, depth, count and time limits; parser sandbox/worker; HTML treated as text, never rendered; no attachments or remote content | Fuzzing, malformed fixtures, huge JSON, HTML script injection |
| URLs holding credentials or tracking tokens | Stored secrets / logs | Parse URL, retain only normalized site domain + safe timestamp; strip query/fragment, username/password; disable automatic URL fetches | Fixtures with `?token=`, `#secret`, URL credentials |
| Prompt injection in messages | Unsafe tool actions or misleading results | Email is untrusted data; no instructions executed; no automatic browsing or external AI calls; evidence-only parsing | Malicious message saying “ignore safeguards” produces no action |
| Accidental raw upload | Sensitive source sent to server | Client-side processing by default; API accepts only allowlisted normalized fields, rejects multipart raw files on normal analysis endpoint | Browser network inspection and rejected raw-file API tests |
| Excessive collection / data retention | Privacy breach despite benign intent | Minimal schemas, no content body persistence, explicit user deletion, retention limits, backup policy | Data inventory, scanning DB/logs for secret fixtures |
| Session theft / CSRF / XSS | Unauthorized access | Short, secure sessions; HttpOnly, Secure, SameSite cookies; CSRF controls for state changes; CSP; escaping; avoid localStorage auth tokens | Auth, CSRF and browser security tests |
| Malicious action link or phishing | User redirected to impersonator | Manually verified official domain allowlist; HTTPS and canonical host verification; label external destination; no links scraped from email used as official | Unsafe/expired/redirecting link cases |
| External model leakage | Personal messages sent outside product | No external LLM in P0; later require separate data-flow and vendor review, minimization, explicit opt-in | Outbound network allowlist and egress checks |
| Logs / analytics / crash reports | Private data leak | Structured logs with IDs and error categories only; redact headers, bodies, email subjects, full URLs; no session secrets | Automated log snapshots with synthetic secrets |

Threat model requires review after any new adapter, cloud analytics, OAuth, AI vendor or automatic action is introduced.

## 3. Data inventory and handling rules

| Data | Allow in browser transiently? | Persist on server? | Notes |
|---|---|---|---|
| Raw selected `.eml` and browser JSON | Yes, solely during user-selected parsing | **No** for normal P0 flow | Do not place raw contents in analytics, error reporting, IndexedDB or service-worker caches |
| Sender address / subject / message body | Transient parsing only | **No by default** | Extract safe category code, domain, date and minimized provenance |
| Normalized domain, observation kind, approximate time | Yes | Yes, after approval | `safe_metadata` strict typed allowlist; avoid full URL/path |
| Relationship evidence and class/confidence | Yes | Yes if user opts to save analysis | Store ruleset/adapter versions and explicit uncertainty |
| Name/email used for sign-in | When needed | Minimal authenticated identity | Separate from observation records; avoid exposing in logs |
| Passwords, full card details, CVVs, auth cookies, tokens | Should be ignored immediately | **Never** | Reject full password-manager exports |
| User action state (`opened`, `user_reported_done`) | Yes | Yes with user consent | `opened` is NOT completed deletion |
| Security/audit metadata | No source payload | Minimal, short-retained | Administrative access logged, no raw contents |

Data deletion must cascade to derived claims: deleting an import removes its observations and evidence links and recomputes or retires dependent relationships/assessments. Do not claim removal from source companies.

## 4. Security architecture and data flow

```text
Explicit user consent + file selection
      |
      v
Client import worker (prefer local):
  extension/schema validation -> bounded parse -> sanitize ->
  secret stripping -> allowlisted observation contract
      |
      | HTTPS: structured observations ONLY (no source bodies)
      v
FastAPI: authenticated request + schema/volume validation + user scoping
      |
      v
Evidence service: cautious domain resolution, deduplication, ruleset
      |
      v
PostgreSQL: tenant-scoped import/observation/relationship/assessment records
      |
      v
UI: evidence type, claim-specific confidence, sensitivity and limitations
      |
      v
Verified privacy-action links (opens external official settings; no auto-action)
```

**Client parsing warning:** browser-local processing reduces bulk uploads but cannot guarantee privacy if our own JavaScript is compromised. Use dependency pinning, CSP, restricted scripts, privacy review and test egress. For large files, stop rather than silently falling back to server raw-file processing.

## 5. Authentication, authorization and tenancy

1. **Phase A (synthetic-only):** a single-user local demo can operate without public auth, but MUST NOT be exposed publicly with real information.
2. **Phase B (private multi-user):** use a maintained identity provider or a well-reviewed session implementation; do not implement password cryptography from scratch. Default to secure cookie sessions and CSRF protections.
3. **Always derive tenant identity on the server** from authenticated context. Never accept arbitrary client-supplied `user_id` as proof of ownership.
4. Query by `id` **and** owner; include ownership in updates, deletes, assessment lookups and action-state updates. Avoid leaking whether another user's ID exists.
5. Privileged production access requires MFA, separate roles, limited access, audit logs and break-glass procedures.
6. Shared `organizations` and `action_directory` are not user evidence; validate that actions belong to the relationship's canonical organization before exposing or recording them.

## 6. Import and parsing controls

**Proposed pilot limits (tunable, not product guarantees):** `.eml` 5 MiB each, browser JSON 20 MiB, 10,000 records per import, max 20 files per batch, parser deadline and nesting/field-length caps. Reject rather than attempt unsafe large-file parsing. Enforce both client and API-side record limits; never trust Content-Type or filename alone.

- Allowlist the two adapters, format versions and exact allowed fields; reject ZIP, HTML documents, `.pst`, `.mbox`, passwords CSV, attachments and unknown formats in P0.
- MIME email parser: extract safe headers and selected plain text; never fetch linked images, follow hyperlinks or execute HTML. If HTML-only, strip to bounded text safely; no HTML render.
- Browser URLs: normalize only `http:` and `https:`; derive registrable domain with maintained public-suffix logic; reject non-web schemes and strip queries/fragments/credentials before use; retain timestamp with validation.
- Defend against spoofed email sender/display names and shared mail domains. Unknown organization mappings remain unresolved.
- Normalize observations in typed schemas rather than unrestricted JSON. Enforce `safe_metadata` keys and value lengths on the API and database write path.
- No third-party URL crawling from imported content. No remote content from messages.

## 7. Storage, encryption, operational access

- TLS for any nonlocal transport; encrypted managed disks/backups for persisted data; secrets in a secret manager rather than repository or `.env` in production.
- Minimize database columns and application indexes that might expose private information. Encrypt further at application level if the final threat model requires it; key rotation must be documented.
- Database account follows least privilege; migrations run with separate credentials; restrict network access to PostgreSQL.
- No sensitive event data in monitoring/third-party telemetry. Central error reports can contain only safe status codes and trace IDs.
- Dependency updates, lockfiles, automated dependency scans and protected CI secrets. Separate dev/test/prod environments with no live user copies in tests.
- Establish incident response owner, containment process, notification decision tree and runbook before real-user pilot.

## 8. Retention, export and deletion policy

**Proposed beta data policy (requires legal/privacy review before real users):**

- Raw files: only in memory during import, discarded on completion/cancel/tab close; **not persisted** by P0 design.
- Derived records: saved only after an explicit user choice; user can delete individual imports or all saved records at any time.
- Private beta: set a clearly disclosed expiry for derived records, e.g. **30 days after last analysis unless renewed by the user**. This is a proposed configuration, **not a legal minimum or maximum**.
- Operational logs: event codes only; proposed maximum 14 days. Do not put individual findings or email domains in routine telemetry.
- Backups: encrypted, access-limited and rotate out according to documented schedule; **proposed maximum 30 days** for private beta, with exceptions/legal obligations disclosed. Deletion from live database does **not** instantly erase existing backups.
- Delete-import process: authorize ownership → identify affected relationships → remove source + linked observations → recompute remaining relationships → retire assessments unsupported by evidence → report completion for live storage.
- Account deletion: cascade through all personal tables, session invalidation, async-job cleanup, third-party processor inventory and user-facing explanation of backup expiration. Maintain non-personal canonical company action URLs if applicable.
- Test deletion with two-source overlap, re-import, concurrency and backup recovery; restored backups must reconcile deletion requests before being served.

Never claim that an opened settings page revokes permissions, or that deleting PV1 data deletes information stored by the source website.

## 9. Evidence integrity and AI guardrails

- Four review values: `sensitive`, `medium`, `low`, `unknown`; separate confidence `high`, `medium`, `low`, `insufficient`.
- Retention and data-sale status stay `unknown` in P0 unless independent claim-specific proof is introduced through a reviewed mechanism.
- Version the deterministic ruleset. Every finding lists what evidence was observed, what was inferred and limitations.
- No remote LLM in initial MVP. Future AI must meet explicit consent, minimization, model/vendor security review, hallucination-evaluation and audit requirements; no user data used for model training without separate authorization.

## 10. Schema hardening tasks for Step 5

The proposed `03-pv1-schema.sql` is a starting point only. Before real-user data:

1. Implement authenticated tenant isolation for **every** endpoint, tested with two users. Evaluate PostgreSQL RLS as defense in depth.
2. Remove the placeholder `retention_policy = 'pending_security_review'`; replace with an explicit controlled policy and expiry mechanism.
3. Validate and bound `source_label` (free-form labels may contain PII), `safe_metadata` JSON, `domain` and free-text explanation fields.
4. Prevent user action rows from referencing a directory entry for a **different** organization. Prefer composite or application-enforced verified consistency; test explicitly.
5. Define the migration strategy and schema versioning; do not deploy raw draft SQL directly without migration/review.
6. Add deletion-recompute transaction handling and ensure no stale assessments or leaked orphaned rows.
7. Use claim-specific evidence validation before assigning `confirmed`, `verified_retained`, `verified_not_retained`, or `verified_shared_or_sold`. P0 must not produce them.
8. Add upload/record-size rate limits and duplicate processing protections.

## 11. Security verification gates

| Gate | Pass criteria | Stage |
|---|---|---|
| G-S1: Secret exclusion | Synthetic passwords, payment cards, URL tokens and email body samples never appear in persisted observations or logs | Before any real imports |
| G-S2: Parser abuse resistance | Malformed/huge input, HTML and embedded malicious instructions fail safely | Before private beta |
| G-S3: Tenant isolation | 100% of cross-user read/update/delete ID tests blocked | Before multi-user beta |
| G-S4: Evidence/deletion integrity | Deletion removes or recomputes all dependent claims with no stale citations | Before private beta |
| G-S5: Secure links | No unverified domains or redirects presented as endorsed privacy controls | Before beta |
| G-S6: Operations | HTTPS, secure sessions, key management, minimal logging, encrypted backups, incident plan | Before externally hosted real-user beta |
| G-S7: External security review | Independent security assessment / penetration test commensurate with data risk and deployment scope | Before public launch |

A successful unit test is not an independent security audit. Do not advertise the product as secure, compliant or certified before independent evidence supports those statements.

## 12. Applicable references and review queue

**Engineering references (verified November 2026):**
- OWASP File Upload Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
- OWASP API Security Top 10 (2023): https://owasp.org/projects/api-security-project
- OWASP ASVS v5 logging: https://github.com/OWASP/ASVS/blob/master/5.0/en/0x25-V16-Security-Logging-and-Error-Handling.md
- NIST SSDF SP 800-218: https://csrc.nist.gov/pubs/sp/800/218/final

**Review before external launch:** India and other target-market privacy law applicability (including DPDP commencement and current rules); processor agreements, retention obligations, cross-border transfer requirements, privacy notice and consent language; email/social provider terms for any future integration. The product has **no claimed legal compliance certification** at this stage.

## 13. Sign-off and open decisions

**Design decisions for MVP planning:** client-side-first file parsing; no raw-file persistence; strictly minimized observations; explicit user authority; separate confidence/sensitivity; no automated external actions; no remote model in P0.

**Must be decided before private beta:** chosen auth approach, data residency/hosting, key custody and backup service, retention policy final values, incident response operator, accessibility standards, and external privacy/legal review scope.
