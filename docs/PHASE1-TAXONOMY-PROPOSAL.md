# Proposed Phase 1 relationship taxonomy clarification

Status: **PROPOSED, NOT APPROVED**. Prepared 2026-11-23 for PR #1, corpus 1.0.0.
This is a discussion note, not an accepted decision or a revised truth baseline.
No manifest label, fixture, test, runtime contract or schema is changed by it.

Complete and save the [independent worksheet](../tests/fixtures/pv1/v1/HUMAN-REVIEW-WORKSHEET.md)
before reading this note. Its judgments must come from raw evidence, not these
proposed definitions. Prior exposure should be disclosed in the worksheet.

## Existing vocabulary and the ambiguity requiring review

[Document 03, sections 5-6](03-evidence-data-model.md) specifies four relationship
types: `visited`, `likely_account`, `transaction`, `marketing`. Several types may
coexist for one organization/domain; these are not mutually exclusive categories
or a ladder from browsing to payment. Observation kinds such as
`transaction_email_detected` describe source evidence and are distinct from a
relationship assertion. Neither is an assurance that the sender is authentic.

Document 03 mentions receipt/order evidence but does not precisely settle whether
`transaction` includes an unpaid invoice or a cancelled order. The current
[corpus guide](../tests/fixtures/pv1/v1/README.md) uses the broader phrase
"transaction indication" for those cases. The word can be read as a completed
payment, so that interpretation must be explicitly reviewed before settling the
ground truth. Passing the validator or a proposed-label test cannot resolve it.

## Proposed interpretation for adjudication

The following is a proposal for the meaning of existing names, not a new label
assignment to any scenario. Reviewers may reject or revise it.

| Relationship type | Proposed claim boundary | Additional evidence needed for stronger claims |
| --- | --- | --- |
| `visited` | Selected browser evidence records a site interaction, subject to origin and record validity | Does not establish signup, account ownership, payment or current company retention |
| `likely_account` | Credible, sufficiently specific evidence suggests an account-related relationship | Does not establish a confirmed or currently active account; a visit or generic greeting alone is not account proof |
| `transaction` | Evidence indicates a financial/commercial interaction, potentially including an order, invoice, receipt or cancellation; the claim must state which | Does not itself mean paid, settled, completed purchase, retained card details or verified merchant identity |
| `marketing` | Evidence supports a promotional-message relationship with an attributable organization | Does not establish registration, consent, purchase, tracking or data sale |

Under the broad `transaction` proposal, distinguish the existence of
transaction-related evidence from the outcome of payment. This is a conceptual
claim distinction only: no `payment_status` field, new subtype, scoring rule or
classifier is introduced. For contradictions, describe the opposing statements
and assess the specific claim rather than mechanically selecting the latest mail.

Alternative for reviewers: reserve `transaction` for a completed-payment claim
and require another name/category for invoice/order/cancellation indications,
or keep such evidence unresolved until a vocabulary is agreed. That option
requires explicit review of affected labels and compatibility/version effects;
it cannot be enacted by silently reinterpreting an existing test or changing
this note to "accepted". Any implementation needs separate authorization.

## Keep the other dimensions independent

| Dimension | Existing vocabulary / constraint | Proposed clarification to review |
| --- | --- | --- |
| Evidence state | Corpus uses `observed` / `inferred`; document 03 also discusses claim-specific `confirmed` | A visible source statement is not confirmation of the real-world event it describes. This note does not add `confirmed` to the corpus schema |
| Evidence confidence | `high`, `medium`, `low`, `insufficient` | Strength of the named relationship claim, not a payment probability, timestamp-validity score or company safety grade; duplicates alone add no independent corroboration |
| Review priority | `sensitive`, `medium`, `low`, `unknown` | Potential impact/context, separately justified from claim confidence; ambiguity must not silently become Low |
| Unresolved evidence | Separate insufficient/unknown review items in the proposed manifest | Not a fifth relationship type; exclusion and unresolved evidence need explicit reasons |
| Event time | Raw timestamp, validity and any supported event time | Whether a record supports a relationship and whether it supports a reliable date/recency are separate questions |
| Retention / sale | Corpus and Phase 0 contracts keep both `unknown` | No relationship category, priority or receipt establishes these company-held-data claims |

These boundaries describe review questions, not deterministic detection rules.
Confidence in receiving a payment-related message may differ from confidence
that payment occurred. High-impact context does not establish a sensitive
personal attribute. Domain attribution also needs its own evidence and limits.

## Required focused adjudication

| Case | Raw evidence | Question requiring a human decision |
| --- | --- | --- |
| c07 | [e02 receipt](../tests/fixtures/pv1/v1/emails/receipt-shop.eml), [e05 correction](../tests/fixtures/pv1/v1/emails/conflicting-cancellation.eml) | What claim survives opposing statements about the same order? Is the broad transaction-indication meaning acceptable, and how should payment uncertainty affect wording and confidence separately from priority? |
| c12 | [h06 rows 0-5](../tests/fixtures/pv1/v1/history/malformed-times.json) | For each malformed or absent timestamp, should the record be usable without a date, unresolved or excluded? Distinguish a visit claim from trustworthy time/recency; do not infer that missing and invalid times have an already approved common policy |
| c21 | [e19 unpaid invoice](../tests/fixtures/pv1/v1/emails/unpaid-invoice.eml) | Does unpaid invoice evidence belong under the broad transaction-indication definition, or require different wording/vocabulary? Which precise claim and confidence are justified without asserting completed payment? |
| All six deletion snapshots | [Worksheet deletion setups](../tests/fixtures/pv1/v1/HUMAN-REVIEW-WORKSHEET.md#deletion-snapshots) | Starting independently from each original source set, which claims and dimensions are justified by the survivors alone? How are duplicate copies and unsupported claims treated after each removal? |

The proposed manifest currently distinguishes invalid history times from an
absent required timestamp. That distinction remains a proposal to adjudicate,
not a parser acceptance policy. This note assigns no replacement labels to
c07, c12, c21 or the deletion snapshots.

## Decision process and blank human decision record

Save blind judgments first, then compare the existing labels, this proposal and
the raw anchors. Record disagreements in the worksheet/PR, including objections
to the vocabulary itself. A human must explicitly choose a definition and
resolve affected cases. Until then, ADR-008 remains proposed and the manifest
remains `awaiting_independent_review` with no independent reviewer recorded.

Only reviewer-approved corrections should trigger a separately reviewable
corpus/version decision and corresponding manifest, source hash, metric or test
updates as appropriate. Preserve the original review record and version history.
No such correction is made by this documentation update. No Phase 2 work,
automatic approval or PR merge follows from preparing these materials.

| Human decision field | Entry (blank) |
| --- | --- |
| Chosen definition / alternative and exact wording | |
| Raw evidence and reasoning, including c07/c12/c21 | |
| Affected cases/snapshots and proposed corrections | |
| Outstanding disagreements | |
| Reviewer/adjudicator pseudonym and date | |
| Explicit decision and version/compatibility implications | |
