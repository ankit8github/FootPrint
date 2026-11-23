# Phase 1 taxonomy decision and baseline 1.1.0

Date: 2026-11-23 (Asia/Calcutta). PR: [#1](https://github.com/ankit8github/FootPrint/pull/1).
Status: **product-owner-approved, AI-assisted baseline**.

Authority is the product owner's explicit finalization instruction in this task.
The AI assistant applied the supplied decisions and checked the fictional source
text, all 29 cases and six deletion setups. This is not independent blind human
review. `independent_reviewer` remains null; no reviewer identity is invented.
The blank worksheet and original review checklist remain unfilled and unchanged.

## Approved meaning and focused resolutions

`transaction` means evidence of a financial/commercial interaction, such as an
order, invoice, receipt or cancellation. The specific interaction must be named.
It does not establish completed payment, settled purchase, retained payment
credentials, merchant authenticity, company retention or data sale.
`visited`, `likely_account`, `transaction` and `marketing` may coexist; confidence,
evidence state and review priority remain separate dimensions.

| Decision | Before (proposal 1.0.0) | Approved baseline 1.1.0 and source basis |
| --- | --- | --- |
| c07 | Transaction, Sensitive / Low | Retain those dimensions. e02 says the order was paid; e05 says it was cancelled before payment. Explicitly describe these contradictory payment claims. Neither message resolves payment outcome. |
| c12 | Five invalid-time rows supported a Low / Low visit; missing-time row excluded | Exclude all six h06 rows under strict MVP P0 browser-history validation: string, null, negative, overflow, fractional and missing timestamp. No relationship or unresolved claim survives; all event times stay null. |
| c21 | Transaction, Sensitive / Medium | Unpaid invoice, transaction, Medium review / Medium confidence, supported only by e19. The source explicitly says unpaid and contains no payment credentials. Assert neither payment nor retained credentials. |
| Remaining 26 cases | Proposed authored expectations | Retain the existing expectations under the approved transaction boundary. AI-assisted inspection found no additional correction needed. This does not attest to a blind human judgment for each case. |

The strict history-time rule takes precedence over the general null-time
annotation guidance in document 03 for invalid/missing browser-history rows.
It does not change c11's malformed email Date expectation. This is a ground-truth
policy decision; no Phase 2 parser or ingestion feature is implemented.

## Six deletion snapshots checked independently of one another

Each starts from the original complete case source set, not a prior deletion.
All six original snapshots are retained byte-for-byte within their case data.

| Snapshot | Deleted sources | Surviving claims and support |
| --- | --- | --- |
| c23-d1 | e01 | None; no sources remain |
| c24-d1 | e01, e02 | Observed visits only: h-shop and h-news; Low / High |
| c24-d2 | h01 | Likely account from e01, Medium / Medium; transaction indication from receipt e02, Sensitive / Medium |
| c24-d3 | e01, e02, h01 | None; no sources remain |
| c25-d1 | e01 | Likely account from e04 only, Medium / Medium |
| c25-d2 | e04 | Likely account from e01 only, Medium / Medium |

No removed event is cited. Duplicate removal does not inflate confidence, and
empty snapshots have no remaining relationships, unresolved items or duplicates.
Retention and sale stay unknown in every surviving claim. These are authored
oracles and reference checks, not execution of a deletion/recomputation engine.

## Version and provenance

Corpus 1.1.0 supersedes 1.0.0 within the `v1` major-schema directory. The schema
name stays `phase1-ground-truth-v1`; the new required approval metadata and exact
review status are checked by the offline validator. Its current version pin is
1.1.0. Original tooling remains available in Git history for reproducing 1.0.0.
All 27 raw source files, source hashes, event IDs and literal anchors are unchanged.
The `corpus=1.0.0` marker in original email bytes records raw-fixture provenance;
it is intentionally not rewritten when annotation policy changes.

[Archive index](../tests/fixtures/pv1/v1/archive/README.md) preserves the original
manifest, metrics, catalog, guide and report. Original REVIEW.md,
HUMAN-REVIEW-WORKSHEET.md and PHASE1-TAXONOMY-PROPOSAL.md remain unchanged at their
original paths. Commit `8afdacdb9b3a3011eb4944c743bd5a1e3e923cc5` preserves the full
pre-decision state. No commits are rewritten or squashed.

The product owner authorized finalization and merging PR #1 after all checks
pass. This closes Phase 1 using the stated approval basis; it does not fulfill
an independent blind human review or authorize Phase 2, deployment or real data.
