# PV1 — Product Requirements Document (PRD)

**Product:** Personal Digital Footprint & Privacy Intelligence  
**Version:** 0.1 (development baseline)  
**Date:** 2026-11-21  
**Status:** Draft for engineering planning; product vision locked, MVP details proposed

## 1. Product purpose

Help individuals understand their digital relationships using information they explicitly authorize, identify potential personal-data exposure, explain the evidence and uncertainty behind each finding, and guide them to relevant privacy controls.

**Working promise:** Know where your digital identity lives and take control of it.

### Problem statement

Internet users lack a single, trustworthy way to understand where they have shared personal information, which digital relationships may involve sensitive data, and what actions they can take to manage privacy exposure.

### Five PV1 pillars (locked)

1. **Discover** online accounts, websites, subscriptions, and other digital relationships from authorized evidence.
2. **Analyze** probable categories of personal information involved and the reliability of evidence.
3. **Classify** review priority as Sensitive, Medium, or Low; use Unknown when evidence is insufficient.
4. **Visualize** findings in one dashboard with reasons and sources.
5. **Control** by guiding users to verified account, permission, unsubscribe, or deletion settings when supported.

## 2. Intended users and jobs

**Initial user:** An individual who regularly uses online services, has several accounts, and wants a consolidated privacy review without changing browsers.

**Primary job:** “Show me the online relationships I may have forgotten, why they matter for my information, and what I can do next.”

**Secondary jobs:** Find noisy promotional senders; review older accounts; understand which findings need urgent attention; inspect what evidence supports a claim.

## 3. MVP boundary

### Included in the first testable release

- Responsive standalone web application.
- User-initiated import of selected supported email records/exports and browser-history data.
- Parsing, normalization and deduplication of digital relationships.
- Basic relationship types: visited site, likely account registration, purchase/transaction evidence, marketing relationship.
- Sensitivity priority (Sensitive / Medium / Low / Unknown) and a **separate** evidence-confidence field.
- Unified dashboard with filtering and a drill-down evidence explanation for each finding.
- Verified links or instructions to relevant privacy/account controls where known.
- User control of imported records and derived findings, including deletion.
- Synthetic-data automated tests and a small consent-based private user evaluation.

### Not included in the first release

- New browser, browser replacement or persistent browsing surveillance.
- Android-wide app tracking or ISP/network interception.
- Direct access to arbitrary private company databases.
- Claiming to know precisely what a company currently retains or has sold without direct evidence.
- Automatic account deletion, cookie deletion across other applications, or permission revocation without user action.
- Live OAuth integration with every mail/social platform, unrestricted cookie ingestion, or SMS-history scanning.
- Collecting raw passwords, CVVs, full card numbers, authentication cookies, or tokens as findings.

### Future PV1 candidate sources (not MVP commitments)

Gmail API, Microsoft Graph, browser extension-based imports, compatible saved-login *metadata*, social-media user exports, optional SMS export and limited cookie metadata. Each source needs a separate feasibility/security review.

## 4. Primary user journey

1. User opens the product and sees what it does, what it can infer, and what it cannot know.
2. User chooses a source and explicitly authorizes/imports records.
3. Product validates format, previews what categories will be processed, and rejects or excludes unnecessary secrets.
4. Product extracts observations, associates them with normalized organizations/domains, and merges duplicates.
5. Product produces review findings, each with evidence type, source, confidence, sensitivity and limitations.
6. User reviews Sensitive / Medium / Low / Unknown findings, opens a finding, and reads why it was flagged.
7. User follows a verified privacy-settings link or instructions, and optionally records that an action was completed.
8. User can remove an imported source and delete its associated evidence/findings.

## 5. Core functional requirements

| ID | Requirement | MVP acceptance condition |
|---|---|---|
| FR-01 | Import supported data | A user can upload a valid supported sample and get a clear validation result; invalid formats fail safely. |
| FR-02 | Extract observations | Distinguishes visited domain, account indication, transaction indication, and marketing contact in labeled fixtures. |
| FR-03 | Normalize and link | Maps supported records for the same website/organization without merging unrelated domains blindly. |
| FR-04 | Explain findings | Every finding displays supporting evidence types and what is inference versus fact. |
| FR-05 | Classify review priority | Assigns Sensitive, Medium, Low, or Unknown using documented rules and includes a rationale. |
| FR-06 | Show evidence confidence separately | Confidence in an account/interaction is not conflated with sensitivity or current retention. |
| FR-07 | Dashboard | Supports summary counts, filters, and detail view of a finding. |
| FR-08 | Support privacy actions | Provides only verified action URLs or accurate instructions and does not claim a completed deletion based on a click. |
| FR-09 | Data control | User can delete imported data and derived results; retention behavior is documented and tested. |
| FR-10 | Audit source provenance | A result can be traced to its import/source type without unnecessarily storing raw sensitive contents. |

## 6. Evidence and interpretation rules

### Evidence states

- **Observed:** Directly documented in an authorized source (e.g. a website appears in imported history, or an email with registration context exists).
- **Inferred:** Supported conclusion based on observations (e.g. likely account created).
- **Confirmed:** Supported by an authoritative direct disclosure or account record; do not use for company-held data unless that specific claim is verified.

### Sensitivity is not risk or certainty

- **Sensitive:** Indicators that financial transactions, identification, health or other high-impact personal-data categories may be relevant; warrants review, not necessarily compromise.
- **Medium:** Credible account, identity or permission relationship with some personal-data implications but no stronger sensitivity evidence.
- **Low:** Limited evidence such as a generic website visit or basic newsletter interaction.
- **Unknown:** Insufficient or ambiguous evidence; do not force a low classification.

Confidence concerns the strength of evidence. Sensitivity concerns the potential impact of the data category. Neither proves current retention, sharing, data sale, or a breach.

### Example

Registration email + order confirmation + saved-login-site metadata: strong evidence of a shopping relationship and payment activity; *not* evidence the retailer currently stores the user's card number or sold the data.

## 7. Privacy and security requirements

- Permission-based, explicit, revocable source access and user-initiated scans in the MVP.
- Prefer local pre-processing where practical; do not upload whole raw exports by default without a justified, disclosed need.
- Strip or ignore secrets; avoid logging raw email bodies, passwords, payment credentials and authentication tokens.
- Encrypt relevant stored personal information in transit and at rest; isolate users' data.
- Minimize collection and define deletion and retention semantics before any real-user beta.
- Treat imported emails/web pages as untrusted content and do not follow embedded instructions.
- Do not send private records to AI providers without an explicit, reviewed processing policy and appropriate user consent.
- User-facing explanations must never equate account evidence with proof of current storage or sale.

## 8. Proposed engineering stack (not locked)

- Frontend: React + TypeScript.
- API/backend: Python + FastAPI.
- Storage: PostgreSQL for structured relationships/findings, when persistence is required.
- Analysis: deterministic extraction/normalization first; optional model assistance only if benchmarks prove benefit.
- Testing: pytest + Playwright.
- Packaging: Docker.

## 9. First end-to-end engineering milestone

**A user imports a supported sample → the system discovers a real digital relationship → assigns an explained review priority with confidence → displays evidence → offers an appropriate privacy-action link or guidance.**

The first demonstration should use synthetic fixtures, not genuine inboxes or financial records.

## 10. Validation plan and provisional targets

Suggested test group: 15–20 consenting participants after security review, with manually reviewed ground truth.

| Metric | Provisional target | Measurement note |
|---|---|---|
| Discovery precision | ≥90% | True relationships / all relationships reported |
| Discovery recall | ≥80% | Genuine relevant relationships found / verified inventory within supported sources |
| Sensitivity agreement | ≥90% | Versus reviewed, pre-defined labels; track Unknown separately |
| Verified action links working | ≥95% | Tested supported links, not claimed account deletion |
| First useful result | <5 minutes | Record input size/device and processing time |
| Users completing meaningful review/action | ≥40% in 7 days | Includes confirmed review, not just link clicks |

These are hypotheses and internal gate targets, **not** measured outcomes, competitor benchmarks or promises.

## 11. Open decisions before implementation

1. Exact import file formats, size limits and field contracts for first email/browser data sources.
2. Whether parsing runs fully client-side or in isolated backend jobs, and how temporary files are deleted.
3. Minimum evidence schema, organization/domain resolution rules and provenance model.
4. How to populate and verify a privacy-action directory.
5. Whether the first demonstration needs user accounts or can operate in an ephemeral local session.
6. Precise rules and datasets for sensitivity labels, confidence and Unknown.
7. Threat model and privacy notice for private beta.

## 12. Next documents

- `02-source-feasibility.md`: supported source formats, permissions, restrictions and minimum available fields.
- `03-evidence-data-model.md`: entities, schemas, examples and provenance rules.
- `04-threat-model.md`: threats, trust boundaries, controls and deletion paths.
- `05-mvp-implementation-plan.md`: milestones, tests, risks and acceptance criteria.

---

**Decision log — 2026-11-21:** Proceed with a focused proof-of-value MVP while preserving the locked PV1 vision. No live integrations or production deployment approved by this PRD alone.
