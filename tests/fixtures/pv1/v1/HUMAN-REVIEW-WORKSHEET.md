# PV1 1.0.0 independent human review worksheet

**Unfilled review template. No independent approval is recorded.**

Scope: all 29 initial scenarios and all six source-deletion snapshots in PR #1.
Prepared against branch commit `3a2436e15e6e18686f066fc1c7358efa0562f6f7`;
raw corpus and proposed labels are unchanged. Reference clock: `2026-10-20T00:00:00Z`.

## Blind-first procedure

1. Begin here. Open only the linked raw files as text. Do not consult the
   manifest judgments, CATALOG scenario labels, metrics, tests, old REVIEW
   comparison questions or taxonomy proposal until you save your initial judgments.
   Filenames and scenario setups provide unavoidable context; record any prior exposure below.
2. Fill every initial-scenario table in your own words, citing event IDs and
   literal raw anchors. Use additional rows per relationship/event as needed.
   A source reference lists available input; it does not designate supporting evidence.
   Leave no final judgment implicit: explain no relationship, unknown or exclusion when chosen.
3. Fill each deletion snapshot from its named surviving sources. Each starts
   from the full original case, not the preceding deletion. Record changes and reasons.
4. Save a dated blind-pass copy or commit before unblinding. Record a pseudonymous
   reviewer ID, not personal contact information. An author or automated agent filling
   this template does not constitute independent human review.
5. Only then compare with manifest.json and read the proposed taxonomy note.
   Use the final comparison log for disagreements and proposed corrections.
   Do not overwrite initial judgments. Acceptance requires a human review record
   and adjudication; blank cells and passing tests are not approval.

**Raw-file safety:** never follow embedded URLs, render HTML, execute scripts,
or open attachments. The fictional inputs remain untrusted text. No import or
deletion service is being exercised. JSON row locators are zero-based;
`whole_message` means inspect every header and body line.

| Review provenance | Entry (blank) |
| --- | --- |
| Reviewer pseudonym / independence from corpus authorship | |
| Review date and reviewed branch SHA | |
| Prior exposure to proposed labels, tests or taxonomy guidance | |
| Saved blind-pass reference and date | |
| Unblinding date / comparison reference | |

## Scenario index

**Focused review:** c07 (contradictory payment), c12 (six timestamp variants),
c21 (unpaid invoice), and every deletion snapshot listed after the initial cases.

| Scenario | Neutral review context | Raw source IDs |
| --- | --- | --- |
| [c01](#c01) | Browser paths and event ages | h02 |
| [c02](#c02) | Shop welcome message | e01 |
| [c03](#c03) | Shop receipt message | e02 |
| [c04](#c04) | Shop messages and browser records | e01, e02, h01 |
| [c05](#c05) | Two welcome-message files | e01, e04 |
| [c06](#c06) | Repeated browser rows | h03 |
| [**c07**](#c07) | Contradictory payment messages | e02, e05 |
| [c08](#c08) | Display-name and sender context | e08 |
| [c09](#c09) | Sender and authentication headers | e09 |
| [c10](#c10) | Shared delivery transport | e10 |
| [c11](#c11) | Email Date field | e11 |
| [**c12**](#c12) | Malformed or absent history timestamps | h06 |
| [c13](#c13) | URL handling | h05 |
| [c14](#c14) | URL components | h04 |
| [c15](#c15) | Plain-text and HTML messages | e03, e12 |
| [c16](#c16) | Embedded instruction text | e13 |
| [c17](#c17) | Multipart message | e14 |
| [c18](#c18) | Clinic portal message | e15 |
| [c19](#c19) | Quoted message context | e18 |
| [c20](#c20) | Similar domain names | e01, e17 |
| [**c21**](#c21) | Unpaid invoice | e19 |
| [c22](#c22) | Unavailable-history record | h07 |
| [c23](#c23) | Sole-source removal setup | e01 |
| [c24](#c24) | Email/history removal setup | e01, e02, h01 |
| [c25](#c25) | Two-copy removal setup | e01, e04 |
| [c26](#c26) | Missing sender header | e16 |
| [c27](#c27) | Encoded header | e20 |
| [c28](#c28) | Account settings notification | e06 |
| [c29](#c29) | Generic welcome message | e07 |

<a id="c01"></a>

## c01 - Browser paths and event ages

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `h02` | [history/visits-only.json](history/visits-only.json) | `h-museum`: `/Browser History/0`; `h-library`: `/Browser History/1`; `h-old`: `/Browser History/2` |

What do the paths, titles and event ages establish about each domain?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c02"></a>

## c02 - Shop welcome message

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e01` | [emails/registration-shop.eml](emails/registration-shop.eml) | `e01`: `whole_message` |

What claim does the message make, and what remains unverified?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c03"></a>

## c03 - Shop receipt message

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e02` | [emails/receipt-shop.eml](emails/receipt-shop.eml) | `e02`: `whole_message` |

What does the receipt text establish, and how trustworthy is its origin?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c04"></a>

## c04 - Shop messages and browser records

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e01` | [emails/registration-shop.eml](emails/registration-shop.eml) | `e01`: `whole_message` |
| `e02` | [emails/receipt-shop.eml](emails/receipt-shop.eml) | `e02`: `whole_message` |
| `h01` | [history/core.json](history/core.json) | `h-shop`: `/Browser History/0`; `h-news`: `/Browser History/1` |

Which claims does each source independently support or fail to support?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c05"></a>

## c05 - Two welcome-message files

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e01` | [emails/registration-shop.eml](emails/registration-shop.eml) | `e01`: `whole_message` |
| `e04` | [emails/registration-shop-copy.eml](emails/registration-shop-copy.eml) | `e04`: `whole_message` |

Compare the complete bytes and identifiers of both messages. What is their evidential relationship?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c06"></a>

## c06 - Repeated browser rows

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `h03` | [history/duplicate-visits.json](history/duplicate-visits.json) | `h-dup-a`: `/Browser History/0`; `h-dup-b`: `/Browser History/1`; `h-distinct`: `/Browser History/2` |

Compare all three rows, including timestamps. How should each row contribute?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c07"></a>

## c07 - Contradictory payment messages

**Focused human review required; no proposed result is supplied here.**

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e02` | [emails/receipt-shop.eml](emails/receipt-shop.eml) | `e02`: `whole_message` |
| `e05` | [emails/conflicting-cancellation.eml](emails/conflicting-cancellation.eml) | `e05`: `whole_message` |

Compare the order identifiers, dates and opposing payment statements. What payment outcome, if any, can be established? Explain the claim behind any relationship term.

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c08"></a>

## c08 - Display-name and sender context

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e08` | [emails/phishing-display-name.eml](emails/phishing-display-name.eml) | `e08`: `whole_message` |

Compare the displayed identity, actual sender and body. What attribution is justified?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c09"></a>

## c09 - Sender and authentication headers

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e09` | [emails/spoofed-from-domain.eml](emails/spoofed-from-domain.eml) | `e09`: `whole_message` |

What do the sender and authentication headers actually establish or leave uncertain?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c10"></a>

## c10 - Shared delivery transport

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e10` | [emails/shared-delivery-provider.eml](emails/shared-delivery-provider.eml) | `e10`: `whole_message` |

How do the transport identity and named organization relate, and what can be attributed?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c11"></a>

## c11 - Email Date field

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e11` | [emails/registration-invalid-date.eml](emails/registration-invalid-date.eml) | `e11`: `whole_message` |

Assess message content separately from the Date field. What time or recency claim is supportable?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c12"></a>

## c12 - Malformed or absent history timestamps

**Focused human review required; no proposed result is supplied here.**

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `h06` | [history/malformed-times.json](history/malformed-times.json) | `h-time-text`: `/Browser History/0`; `h-time-null`: `/Browser History/1`; `h-time-negative`: `/Browser History/2`; `h-time-overflow`: `/Browser History/3`; `h-time-fraction`: `/Browser History/4`; `h-time-missing`: `/Browser History/5` |

Review each of the six rows separately. What handling is justified for string, null, negative, oversized, fractional and absent time values? Separate visit evidence, time validity, usable recency and any relationship claim.

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

Complete each row independently; the value descriptions below are raw input facts.

| Raw event | Raw time_usec value | Disposition and reason (blank) | Visit/relationship judgment (blank) | Time/recency judgment (blank) |
| --- | --- | --- | --- | --- |
| `h-time-text` at `/Browser History/0` | string `"not-a-number"` | | | |
| `h-time-null` at `/Browser History/1` | `null` | | | |
| `h-time-negative` at `/Browser History/2` | `-1` | | | |
| `h-time-overflow` at `/Browser History/3` | `9223372036854775808` | | | |
| `h-time-fraction` at `/Browser History/4` | `1792238400000000.5` | | | |
| `h-time-missing` at `/Browser History/5` | field absent | | | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c13"></a>

## c13 - URL handling

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `h05` | [history/unsafe-urls.json](history/unsafe-urls.json) | `h-file`: `/Browser History/0`; `h-js`: `/Browser History/1`; `h-data`: `/Browser History/2`; `h-ftp`: `/Browser History/3`; `h-chrome`: `/Browser History/4`; `h-relative`: `/Browser History/5`; `h-loopback`: `/Browser History/6`; `h-private`: `/Browser History/7`; `h-localhost`: `/Browser History/8`; `h-broken-url`: `/Browser History/9` |

Review every URL as inert text. What handling and domain attribution are justified per row?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c14"></a>

## c14 - URL components

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `h04` | [history/minimization.json](history/minimization.json) | `h-query`: `/Browser History/0`; `h-fragment`: `/Browser History/1`; `h-userinfo`: `/Browser History/2` |

Assess URL components and record which details are necessary for an evidence claim.

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c15"></a>

## c15 - Plain-text and HTML messages

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e03` | [emails/marketing-news.eml](emails/marketing-news.eml) | `e03`: `whole_message` |
| `e12` | [emails/html-newsletter.eml](emails/html-newsletter.eml) | `e12`: `whole_message` |

Compare message formats and content without rendering HTML. What relationship claims are justified?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c16"></a>

## c16 - Embedded instruction text

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e13` | [emails/instruction-injection.eml](emails/instruction-injection.eml) | `e13`: `whole_message` |

Identify instruction-like text and assess its role as source evidence, without following it.

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c17"></a>

## c17 - Multipart message

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e14` | [emails/registration-inert-attachment.eml](emails/registration-inert-attachment.eml) | `e14`: `whole_message` |

Inspect the MIME structure as text. Distinguish message evidence from attachment content.

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c18"></a>

## c18 - Clinic portal message

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e15` | [emails/health-context-account.eml](emails/health-context-account.eml) | `e15`: `whole_message` |

What interaction and context are supported, and what personal attributes remain unsubstantiated?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c19"></a>

## c19 - Quoted message context

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e18` | [emails/quoted-registration.eml](emails/quoted-registration.eml) | `e18`: `whole_message` |

Distinguish the current sender/message from quoted material. What attribution is justified?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c20"></a>

## c20 - Similar domain names

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e01` | [emails/registration-shop.eml](emails/registration-shop.eml) | `e01`: `whole_message` |
| `e17` | [emails/similar-name-unrelated.eml](emails/similar-name-unrelated.eml) | `e17`: `whole_message` |

What evidence connects or separates the two domain identities?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c21"></a>

## c21 - Unpaid invoice

**Focused human review required; no proposed result is supplied here.**

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e19` | [emails/unpaid-invoice.eml](emails/unpaid-invoice.eml) | `e19`: `whole_message` |

Distinguish invoice issuance, an unpaid obligation and completed payment. Does the proposed vocabulary express your conclusion without overstating it?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c22"></a>

## c22 - Unavailable-history record

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `h07` | [history/encrypted-history.json](history/encrypted-history.json) | `h-encrypted`: `/Browser History/0` |

What usable evidence is present in the history entry?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c23"></a>

## c23 - Sole-source removal setup

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e01` | [emails/registration-shop.eml](emails/registration-shop.eml) | `e01`: `whole_message` |

Record an initial judgment, then independently complete snapshot c23-d1.

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c24"></a>

## c24 - Email/history removal setup

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e01` | [emails/registration-shop.eml](emails/registration-shop.eml) | `e01`: `whole_message` |
| `e02` | [emails/receipt-shop.eml](emails/receipt-shop.eml) | `e02`: `whole_message` |
| `h01` | [history/core.json](history/core.json) | `h-shop`: `/Browser History/0`; `h-news`: `/Browser History/1` |

Record an initial judgment, then independently complete snapshots c24-d1, c24-d2 and c24-d3.

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c25"></a>

## c25 - Two-copy removal setup

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e01` | [emails/registration-shop.eml](emails/registration-shop.eml) | `e01`: `whole_message` |
| `e04` | [emails/registration-shop-copy.eml](emails/registration-shop-copy.eml) | `e04`: `whole_message` |

Record an initial judgment, then independently complete snapshots c25-d1 and c25-d2.

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c26"></a>

## c26 - Missing sender header

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e16` | [emails/missing-from-header.eml](emails/missing-from-header.eml) | `e16`: `whole_message` |

What attribution is possible from the available headers and body?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c27"></a>

## c27 - Encoded header

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e20` | [emails/encoded-subject.eml](emails/encoded-subject.eml) | `e20`: `whole_message` |

Inspect the raw encoded header and message body. Record any manual interpretation and uncertainty.

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c28"></a>

## c28 - Account settings notification

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e06` | [emails/account-notification.eml](emails/account-notification.eml) | `e06`: `whole_message` |

What does the notification establish about a past or current interaction?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="c29"></a>

## c29 - Generic welcome message

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e07` | [emails/ambiguous-welcome.eml](emails/ambiguous-welcome.eml) | `e07`: `whole_message` |

What specific relationship, if any, does the wording establish?

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Observed facts and your own literal anchors, by event ID | |
| Organization/domain attribution and origin-trust limitations | |
| Relationship type(s) and precise claim wording (or explain no supported relationship) | |
| Evidence state for each claim and reasoning | |
| Confidence for each claim and reasoning | |
| Review priority and reasoning, separately from confidence | |
| Event disposition, time validity, event date and recency, by event ID | |
| Supporting and opposing event IDs for each claim | |
| Duplicate groups and effect on evidence strength | |
| Unresolved/excluded inputs, missing evidence and reasons | |
| Retention/sale claims and other limitations or unknowns | |
| Taxonomy ambiguity or alternative wording for later discussion | |

| Blind-pass completion record | Entry (blank) |
| --- | --- |
| Reviewer pseudonym, date and saved judgment reference | |

<a id="deletion-snapshots"></a>

## All six deletion snapshots - separate focused review

**Each snapshot independently resets to its initial case source set.**
Deleted/remaining sets below are scenario setup facts, not predicted outcomes.
Do not consult deleted files to substantiate the surviving snapshot. The
initial-case review is available only to explain differences. No actual
source deletion, company deletion or recomputation is executed.

| Snapshot | Original case | Remove sources | Remaining sources |
| --- | --- | --- | --- |
| [**c23-d1**](#c23-d1) | [c23](#c23) | e01 | (empty set) |
| [**c24-d1**](#c24-d1) | [c24](#c24) | e01, e02 | h01 |
| [**c24-d2**](#c24-d2) | [c24](#c24) | h01 | e01, e02 |
| [**c24-d3**](#c24-d3) | [c24](#c24) | e01, e02, h01 | (empty set) |
| [**c25-d1**](#c25-d1) | [c25](#c25) | e01 | e04 |
| [**c25-d2**](#c25-d2) | [c25](#c25) | e04 | e01 |

<a id="c23-d1"></a>

### c23-d1 - focused deletion review

Initial case: [c23](#c23); original sources: e01.
Remove: e01. Remaining: (empty set).

Available surviving raw references:

No surviving raw source references in this snapshot setup.

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Relationships/claims after removal, domains and precise wording (or explain none) | |
| Evidence state, confidence and priority per remaining claim, with reasons | |
| Surviving supporting/opposing event IDs and your raw anchors | |
| Unresolved/excluded events, duplicate groups and temporal interpretation | |
| Claims/evidence that disappear or change relative to the initial case, and reasons | |
| Any deleted-source citation left in your proposed snapshot | |
| Retention/sale claims, unknowns and limitations | |
| Reviewer pseudonym, date and saved blind-pass reference | |

<a id="c24-d1"></a>

### c24-d1 - focused deletion review

Initial case: [c24](#c24); original sources: e01, e02, h01.
Remove: e01, e02. Remaining: h01.

Available surviving raw references:

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `h01` | [history/core.json](history/core.json) | `h-shop`: `/Browser History/0`; `h-news`: `/Browser History/1` |

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Relationships/claims after removal, domains and precise wording (or explain none) | |
| Evidence state, confidence and priority per remaining claim, with reasons | |
| Surviving supporting/opposing event IDs and your raw anchors | |
| Unresolved/excluded events, duplicate groups and temporal interpretation | |
| Claims/evidence that disappear or change relative to the initial case, and reasons | |
| Any deleted-source citation left in your proposed snapshot | |
| Retention/sale claims, unknowns and limitations | |
| Reviewer pseudonym, date and saved blind-pass reference | |

<a id="c24-d2"></a>

### c24-d2 - focused deletion review

Initial case: [c24](#c24); original sources: e01, e02, h01.
Remove: h01. Remaining: e01, e02.

Available surviving raw references:

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e01` | [emails/registration-shop.eml](emails/registration-shop.eml) | `e01`: `whole_message` |
| `e02` | [emails/receipt-shop.eml](emails/receipt-shop.eml) | `e02`: `whole_message` |

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Relationships/claims after removal, domains and precise wording (or explain none) | |
| Evidence state, confidence and priority per remaining claim, with reasons | |
| Surviving supporting/opposing event IDs and your raw anchors | |
| Unresolved/excluded events, duplicate groups and temporal interpretation | |
| Claims/evidence that disappear or change relative to the initial case, and reasons | |
| Any deleted-source citation left in your proposed snapshot | |
| Retention/sale claims, unknowns and limitations | |
| Reviewer pseudonym, date and saved blind-pass reference | |

<a id="c24-d3"></a>

### c24-d3 - focused deletion review

Initial case: [c24](#c24); original sources: e01, e02, h01.
Remove: e01, e02, h01. Remaining: (empty set).

Available surviving raw references:

No surviving raw source references in this snapshot setup.

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Relationships/claims after removal, domains and precise wording (or explain none) | |
| Evidence state, confidence and priority per remaining claim, with reasons | |
| Surviving supporting/opposing event IDs and your raw anchors | |
| Unresolved/excluded events, duplicate groups and temporal interpretation | |
| Claims/evidence that disappear or change relative to the initial case, and reasons | |
| Any deleted-source citation left in your proposed snapshot | |
| Retention/sale claims, unknowns and limitations | |
| Reviewer pseudonym, date and saved blind-pass reference | |

<a id="c25-d1"></a>

### c25-d1 - focused deletion review

Initial case: [c25](#c25); original sources: e01, e04.
Remove: e01. Remaining: e04.

Available surviving raw references:

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e04` | [emails/registration-shop-copy.eml](emails/registration-shop-copy.eml) | `e04`: `whole_message` |

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Relationships/claims after removal, domains and precise wording (or explain none) | |
| Evidence state, confidence and priority per remaining claim, with reasons | |
| Surviving supporting/opposing event IDs and your raw anchors | |
| Unresolved/excluded events, duplicate groups and temporal interpretation | |
| Claims/evidence that disappear or change relative to the initial case, and reasons | |
| Any deleted-source citation left in your proposed snapshot | |
| Retention/sale claims, unknowns and limitations | |
| Reviewer pseudonym, date and saved blind-pass reference | |

<a id="c25-d2"></a>

### c25-d2 - focused deletion review

Initial case: [c25](#c25); original sources: e01, e04.
Remove: e04. Remaining: e01.

Available surviving raw references:

| Source | Raw file (open as text) | Event ID and locator |
| --- | --- | --- |
| `e01` | [emails/registration-shop.eml](emails/registration-shop.eml) | `e01`: `whole_message` |

| Reviewer judgment | Reviewer entry (blank) |
| --- | --- |
| Relationships/claims after removal, domains and precise wording (or explain none) | |
| Evidence state, confidence and priority per remaining claim, with reasons | |
| Surviving supporting/opposing event IDs and your raw anchors | |
| Unresolved/excluded events, duplicate groups and temporal interpretation | |
| Claims/evidence that disappear or change relative to the initial case, and reasons | |
| Any deleted-source citation left in your proposed snapshot | |
| Retention/sale claims, unknowns and limitations | |
| Reviewer pseudonym, date and saved blind-pass reference | |

## Post-blind comparison and adjudication log

Open these only after saving the blind pass: [proposed manifest](manifest.json),
[taxonomy proposal](../../../../docs/PHASE1-TAXONOMY-PROPOSAL.md) and
[comparison guidance](REVIEW.md). No rows below contain prefilled human judgments.
Add a row for every case/snapshot comparison and every disagreement; distinguish
agreement with a label from approval of its definition. Preserve dissent.

| Case/snapshot | Blind judgment reference | Proposed-label difference or agreement | Raw anchors / reason | Proposed correction | Human adjudication and reviewer/date |
| --- | --- | --- | --- | --- | --- |
| c01 | | | | | |
| c02 | | | | | |
| c03 | | | | | |
| c04 | | | | | |
| c05 | | | | | |
| c06 | | | | | |
| c07 | | | | | |
| c08 | | | | | |
| c09 | | | | | |
| c10 | | | | | |
| c11 | | | | | |
| c12 | | | | | |
| c13 | | | | | |
| c14 | | | | | |
| c15 | | | | | |
| c16 | | | | | |
| c17 | | | | | |
| c18 | | | | | |
| c19 | | | | | |
| c20 | | | | | |
| c21 | | | | | |
| c22 | | | | | |
| c23 | | | | | |
| c24 | | | | | |
| c25 | | | | | |
| c26 | | | | | |
| c27 | | | | | |
| c28 | | | | | |
| c29 | | | | | |
| c23-d1 | | | | | |
| c24-d1 | | | | | |
| c24-d2 | | | | | |
| c24-d3 | | | | | |
| c25-d1 | | | | | |
| c25-d2 | | | | | |

| Final human review record | Entry (blank) |
| --- | --- |
| Coverage of all 29 cases and all six deletion snapshots | |
| Open disagreements, including c07/c12/c21 and taxonomy definition | |
| Human acceptance/rejection and reasons | |
| Adjudicator pseudonym/date and review evidence | |
| Requested corpus version/correction decision | |

This unfilled worksheet records no human approval and does not advance Phase 1.
