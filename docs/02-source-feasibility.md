# PV1 — Source Feasibility & Integration Matrix

**Product:** Personal Digital Footprint & Privacy Intelligence  
**Document:** 02  
**Version:** 0.1  
**Date:** 2026-11-22  
**Status:** Engineering research baseline; not a claim that live connectors are built
**Depends on:** `01-product-requirements.md` (PRD v0.1, 2026-11-21)

## 1. Decision summary

The first MVP uses **user-initiated, local-first imports**, not permanent access to mailboxes, browsers or social accounts. The core demo must correlate evidence from **(1) an email source and (2) a browser-history source** and produce explainable relationships, independently of live third-party APIs.

**Pilot input formats (ordered):**
1. `.eml` (one or several selected messages; Gmail/Outlook and other compatible email clients): **P0**.
2. Chrome-compatible browsing-history JSON with `url`, `title`, `time_usec` (Google data portability/Takeout-style records): **P0**.
3. Gmail Takeout `.mbox` from explicitly selected labels: **P1**, after testing large-file handling, labels, attachments and duplicates.
4. Outlook `.pst`: **P2**, due to binary parsing complexity and potentially broad data exposure; selected `.eml` remains the first Outlook path.
5. Browser saved-login *domain-only* input: **P2**. **Do not accept full password-manager CSV files at all** in the MVP: they contain plaintext passwords.

**Not MVP dependencies:** Gmail OAuth, Microsoft Graph OAuth, cookie API, SMS history, Meta/Instagram data export, background surveillance, auto-unsubscribe, automated revocation, data broker scans.

**Critical boundaries:** an email or visit is evidence of a relationship, **not proof** that a company currently retains, sells, shares or exposes specific information. Do not label transactions as stored card credentials. A "last seven days" filter applies only to records actually available and imported, and cannot make a historical scan complete.

## 2. Feasibility matrix

| Source | Access path | Evidence exposed | Permission/friction | Main constraints | Decision |
|---|---|---|---|---|---|
| Gmail selected emails | User downloads/exports `.eml` messages if supported by their client, or supplies selected samples | Sender domain, subject, date, content if deliberately provided; can identify welcome, receipt, newsletter | Explicit file selection, no OAuth | Content contains secrets/third-party data; exported messages vary | **P0** selected `.eml` |
| Gmail Takeout | Google Takeout archive with `.mbox` for mail | Many messages with headers, subjects, bodies, label metadata where included | User selects Gmail data, requested labels and downloads archive | Potentially huge; may include attachments/Spam/Trash depending selection; risky ZIPs | **P1** `.mbox` |
| Gmail API | OAuth `gmail.metadata` or `gmail.readonly` | Metadata/headers or full messages according to scope | **Restricted** scopes and verification; third-party-server access may trigger annual security assessment | High permission and compliance burden; tokens require careful handling | **Later**, after product value is shown |
| Outlook selected emails | Export/download `.eml` or `.msg` from client | Message headers/body where present | User-initiated per-message download | `.msg` is proprietary and different from `.eml`; keep format handling separate | **P0 `.eml`**; `.msg` later |
| Outlook bulk mailbox | `.pst` export | Mail, potentially attachments and other personal records | User export; varies between classic/new Outlook | Binary file parsing, size, attachment exposure | **P2** |
| Microsoft Graph | Delegated `Mail.ReadBasic` or `Mail.Read` | Basic email fields without body vs. full body | OAuth consent; possible organization policy restrictions | No universal organization-level access; required consent and secure token management | **Later** |
| Chrome history | Google export JSON or specially prepared matching JSON | Visited URL, title, timestamp | User selects file | Visits do not establish signup or disclosure; URLs can contain sensitive query strings | **P0** |
| Chrome extension | `history` permission (and optional host access) | History URLs and visit metadata | Extension installation + prominent browser warning | Cannot be read by unrelated standalone website; permissions broad | **Later** |
| Brave history | Verify per-version export or compatible extension pathway | Similar browsing relationship evidence | Browser-specific user authorization | Do not assume Google Takeout describes Brave output | **Later**, use tested adapters |
| Safari/Firefox history | Browser-specific interfaces/exports/extensions | Visited URLs, timestamps if provided | Platform-specific | Formats and extension APIs differ | **Later** |
| Cookies | Chromium extension `cookies` + host permissions | Cookie metadata **and possibly authentication secrets** | Highly sensitive permissions | Cookie existence != company data retention; never ingest raw session cookie values | **Exclude MVP** |
| Password-manager CSV | User export with `url,username,password` | Saved website identifiers, plus highly sensitive credentials | High-risk plaintext file created on disk | Product must not acquire actual passwords | **Reject raw CSV**; design domain-only safer import later |
| Meta (Facebook/Instagram) | User-controlled export through Accounts Center | Selected account/activity records, variable formats | User requests and downloads export | No blanket API for all off-Meta advertising relationships; needs schema verification | **P2 research** |
| SMS records | User-initiated export where available | Registration, payment and promotional signals | Highly sensitive and device-specific | Google Play SMS permissions restricted; broad collection not justified | **Exclude MVP** |

## 3. Feasibility ratings and minimum data contract

### 3.1 Selected `.eml` message (P0)
- **Feasibility:** High for syntactic parsing, medium for reliable relationship detection.
- **Required fields:** `source_type=email`, `sender_address` or sender domain, `subject`, `message_date`, and a stable generated evidence ID; body is **optional** and minimized.
- **May support:** account registration signal; order or transaction evidence; marketing relationship; unsubscribe-hint detection.
- **Cannot prove:** account still active, present retention, any data sale, delivery of full card number, legitimacy of sender.
- **Security:** Disallow external images/network loads; sanitize HTML; never open attachments; parse headers and safe text under resource limits; treat embedded instructions as untrusted.

### 3.2 Chrome history JSON (P0)
- **Feasibility:** High if the supplied file matches a versioned schema.
- **Required fields:** `url` and `time_usec`; `title` optional; convert microseconds safely to UTC.
- **Normalize:** Keep hostname/registrable domain and timestamp, strip URL query parameters/fragments and credentials **before persistence**; do not retain complete URL by default.
- **May support:** visited-domain relationship and time range; corroborates other evidence.
- **Cannot prove:** login, checkout, account creation, personal data entered, cookies retained, financial data held.
- **Safety:** Reject `file:`, `javascript:`, `data:`; prohibit file path traversal; protect against malicious or huge JSON; do not crawl visited URLs automatically.

### 3.3 Gmail Takeout `.mbox` (P1)
- **Feasibility:** Technically feasible using streaming mailbox parser; operational burden moderate.
- **Input:** Selected Takeout mail archive extracted/selected by user; support standalone `.mbox` before any ZIP upload.
- **Risk:** Very large files, attachments, duplicate forwarded messages, malformed headers, mixed character sets, Spam/Trash content.
- **Gate:** Demonstrate streaming parse limits and provenance on synthetic 100/1,000/10,000-message fixtures without retaining bodies.

### 3.4 Outlook `.pst` (P2)
- **Feasibility:** Possible with specialized parsers, but not necessary for pilot.
- **Gate:** Confirm the export shape across Windows Outlook versions; test independently in sandbox; avoid user data as first fixtures.

### 3.5 OAuth integrations (later)
- **Gmail:** `gmail.metadata` and `gmail.readonly` both restricted; broad metadata isn't a compliance shortcut. Public production needs review; accessing restricted user data through third-party servers may require recurring security assessment.
- **Microsoft Graph:** Use delegated `Mail.ReadBasic` to obtain basic message properties without body when sufficient; `Mail.Read` only if content is necessary. Test personal Microsoft accounts separately from organizational accounts.
- **Principle:** Request minimum rights; use short-lived tokens and explicit disconnect; do not assume user can consent to work-account policies.

### 3.6 Meta exports (P2 research)
- Meta Accounts Center supports Download Your Information for Facebook/Instagram; Activity Off-Meta Technologies lets users examine businesses sharing activity with Meta. This **does not** give PV1 blanket access to the data these businesses hold or prove data sales.
- Require a documented current sample schema, field-level security review and capability-based justification before creating an adapter.

## 4. Feature-to-source evidence mapping

| Claim displayed to user | Minimum supporting evidence | Prohibited leap |
|---|---|---|
| “You visited example.com” | Browser history observation | “You created an account there” |
| “You likely registered” | Recognized welcome/verification mail or permitted saved-login metadata | “Your account is still active” |
| “This sender frequently markets to you” | Multiple tagged promotional messages | “The sender sold your data” |
| “You likely purchased here” | Order confirmation or appropriate transactional email | “The merchant retains your card number” |
| “May involve sensitive information” | Evidence category such as purchase, medical, government ID context | “Your information is leaked / stolen” |
| “Company stores this specific field” | Actual current company-provided record/disclosure for that field | Inference from a receipt or visit |
| “You can manage your settings” | Reviewed official account/privacy action link | “Data has been deleted” merely from opening link |

**Separate data columns:** `relationship_type`, `evidence_state` (observed/inferred/confirmed), `evidence_confidence`, `review_priority` (sensitive/medium/low/unknown), `retention_status` (unknown unless substantiated), and `action_status` (not_started/opened/user_reported_done/verified_external_response).

## 5. Data-handling rules for integrations

1. The user owns the imported inputs, chooses what to include and can remove each source and its derived records.
2. Default to client-side preprocessing for real exports where feasible. Until that boundary is implemented and reviewed, use **synthetic fixtures only**.
3. Never persist plaintext passwords, cookie values, payment authentication data, private OAuth tokens in finding records, or full message bodies by default.
4. Strip query strings, fragments and URL-embedded credentials; do not blindly log incoming files or parsed content.
5. Validate file extension, actual format, encoding, MIME, sizes, total records, malicious archive members and decompression limits.
6. Do not make automatic outbound requests to URLs found in user content; imported documents can contain adversarial instructions and malicious links.
7. Define exact source deletion semantics and prove no orphaned derived findings remain.
8. Show provenance without disclosing more source content than necessary.
9. Unknown is a valid label. Low sensitivity is not the fallback for missing evidence.

## 6. Recommended MVP adapters & validation cases

| Adapter ID | First format | Synthetic fixtures | Tests before pilot |
|---|---|---|---|
| `email_eml_v1` | `.eml` RFC822/MIME | Welcome, receipt, invoice, newsletter, spam, false registration, spoofed sender, malformed header | Sender extraction; dedup; attachments excluded; safe HTML handling; evidence provenance |
| `browser_chrome_json_v1` | Chrome History JSON | Recent visit, old visit, duplicate URL, tracking query URL, credential-bearing URL, invalid scheme, invalid timestamp | Domain/time parsing; strips secrets; correct 7-day filter; no signup claim from visits |
| `relationship_fusion_v1` | normalized observations | One domain in both sources, unrelated brands, shared email delivery infrastructure, redirect URLs | Does not merge unrelated organizations; confidence and evidence type stay separate |
| `sensitivity_rules_v1` | relationship records | Newsletter, registered account, checkout receipt, medical reference, no evidence | Sensitive/Medium/Low/Unknown labels with explicit reasons; never asserts retention or sale |
| `action_directory_v1` | curated verified URL list | Official privacy settings, official unsubscribe, unavailable page, redirect | Safe links; no auto-action; outcomes marked pending until verified |

**Test window:** make 7/30/all-history a *user filter*, not an implied guarantee that those periods are fully represented in an export.

### Suggested initial resource controls (engineering proposals, not agreed product constraints)
- P0 `.eml`: 1 MB per file, 100 files per batch.
- P0 Chrome JSON: 10 MB per batch, 50,000 records.
- Reject archive uploads and attachments during P0.
- Every limit must be re-evaluated with synthetic stress testing.

## 7. Phase gates

**Gate A — Ready to design the evidence schema**
- [x] P0 sources selected: `.eml` and Chrome history JSON.
- [x] Main platform documentation identified.
- [x] Evidence claims and prohibited inferences recorded.
- [ ] Obtain or generate exact synthetic example payloads for each parser.

**Gate B — Ready for private user imports**
- [ ] Implement safe client-side/local-first preprocessing, or approve a documented secure alternative.
- [ ] Complete threat model, retention/deletion implementation, logging review.
- [ ] Fuzz malformed inputs and test file/record limits.
- [ ] Verify privacy-action URLs and user-facing wording.

**Gate C — Ready for live integrations (not in initial MVP)**
- [ ] Determine consent screen/scopes, Google verification eligibility and security assessment requirement.
- [ ] Test Microsoft Graph personal and organizational account constraints.
- [ ] Conduct separate Meta/extension/SMS source reviews.

## 8. Decisions, assumptions, unresolved items

**Decision D-02-A:** Use uploads/exports before live OAuth to test core value with lower permission complexity.  
**Decision D-02-B:** No raw password manager CSV or browser cookies during MVP.  
**Decision D-02-C:** An imported browser visit never suffices to claim signup or retention.  
**Decision D-02-D:** P0 supports `.eml` and Chrome-schema JSON; `.mbox` is next candidate after parser robustness tests.  
**Assumption A-02-A:** Enough consented users can supply a small sample of `.eml` and history data for private beta; this is untested.  
**Assumption A-02-B:** The increase in relationship confidence from correlating both sources has not yet been measured.  
**Open O-02-A:** Browser JSON exact container nesting, version variants and source instructions need fixture verification.  
**Open O-02-B:** Whether pilot runs fully local with no server persistence, or uses ephemeral authenticated accounts.  
**Open O-02-C:** Baseline sensitivity taxonomy, domain normalization, and action directory update policy belong in Step 3.

## 9. Primary public references checked on 2026-11-22

Official documentation / provider statements:

- Google Takeout overview: https://support.google.com/accounts/answer/3024190
- Google Chrome history export schema: https://developers.google.com/data-portability/schema-reference/chrome
- Chrome history extension API: https://developer.chrome.com/docs/extensions/reference/api/history
- Chrome cookies extension API: https://developer.chrome.com/docs/extensions/reference/api/cookies
- Gmail restricted scopes: https://developers.google.com/workspace/gmail/api/auth/scopes
- Google restricted scope review/assessment: https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification
- Outlook download individual messages: https://support.microsoft.com/en-us/outlook/mail/save-an-outlook-message-as-a-eml-file-a-pdf-file-or-as-a-draft
- Outlook PST export: https://support.microsoft.com/en-gb/outlook/export-emails-contacts-and-calendar-items-to-outlook-using-a-pst-file
- Microsoft Graph email permissions: https://learn.microsoft.com/en-us/graph/permissions-reference
- Microsoft Graph list messages: https://learn.microsoft.com/en-us/graph/api/user-list-messages?view=graph-rest-1.0
- Google Password Manager CSV export warning: https://support.google.com/chrome/answer/13068232
- Meta Accounts Center and off-Meta activity: https://about.fb.com/news/2023/10/manage-your-information-across-apps/

For Gmail Takeout `.mbox` specifically, Google's general help describes exports, while Google community product experts confirm `.mbox` packaging. Treat the precise export structure as **requiring fixture confirmation**, not a stable API schema.

---

**Next document:** `03-evidence-data-model.md` — define entities, field contracts, example evidence objects, confidence semantics, sensitivity rules and provenance/deletion relationships.
