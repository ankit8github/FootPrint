# PV1 fictional corpus 1.1.0

Status: **product-owner-approved, AI-assisted baseline** (2026-11-23).
The product owner's explicit instruction settled the taxonomy and focused cases;
the AI assistant applied it and checked all 29 cases and six deletion snapshots.
No independent blind human review was performed. `independent_reviewer` is null.
No parser or classifier exists, and no accuracy result is claimed.

Start with the [approved taxonomy decision](../../../../docs/PHASE1-TAXONOMY-DECISION.md),
[CATALOG.md](CATALOG.md), [manifest.json](manifest.json) and [metrics.json](metrics.json).
The original [REVIEW.md](REVIEW.md), [blank worksheet](HUMAN-REVIEW-WORKSHEET.md)
and [taxonomy proposal](../../../../docs/PHASE1-TAXONOMY-PROPOSAL.md) are preserved
historical review materials. Their pending/proposed wording is superseded by the
approved decision; their blank cells are not completed human review evidence.
[Archive](archive/README.md) preserves the 1.0.0 proposal and original report.

## Raw formats and boundaries

All messages, organizations, identifiers and browsing events were authored from
fictional constants. No user export, real purchase, diagnosis, working credential
or payment card was used. All ordinary domains and email addresses use reserved
`.test` names. Raw files are unchanged from 1.0.0, including their original marker.

- `emails/`: 20 selected-message UTF-8 `.eml` files with CRLF and a synthetic marker;
  includes plain/HTML content, inert attachment, encoded subject and invalid headers.
- `history/`: seven JSON files with `{"Browser History": [...]}`; ordinary rows use
  `url`, `time_usec` (UNIX microseconds UTC) and optional `title`. The bounded shape
  follows the [Chrome history reference](https://developers.google.com/data-portability/schema-reference/chrome).
  Invalid fields and the encrypted-history sentinel are negative fixtures.
- Unsafe URL, script, attachment and prompt-injection strings are inert evidence.
  Do not fetch links, render HTML, execute scripts or open attachments.
- URL query/fragment/userinfo sentinels specify minimization expectations only;
  no raw fixture goes to the API, database or external model service.
- Reference time is `2026-10-20T00:00:00Z`. Invalid times remain null; no current
  clock or import-time substitution supplies a date.
- The narrow `.gitignore` exception permits only this corpus's emails. Scoped
  Git attributes preserve byte hashes. The validator's 64 KiB fixture budget is
  not a product upload-limit decision.

## Approved label semantics

Manifest schema `phase1-ground-truth-v1`, corpus `1.1.0`, records exact source
hashes, row/message locators, literal anchors, authored dispositions and snapshots.
The four coexisting types are `visited`, `likely_account`, `transaction` and
`marketing`. Confidence and review priority describe separate aspects of a claim.
Unresolved items remain Unknown / insufficient, not forced Low relationships.
All retention and sale statuses remain unknown.

`transaction` is evidence of a financial/commercial interaction, not completed
payment. State the interaction and its limits explicitly. c07 retains Sensitive
review and Low confidence with contradictory paid/cancelled-before-payment claims.
c21 is an unpaid invoice with Medium review and Medium confidence; neither
payment nor retained credentials is asserted. c12 excludes all six browser-history
rows with invalid/missing timestamps under strict MVP P0 validation, with no visit
claim. c11's email Date remains invalid/null without losing its account indication.

Likely-account wording never proves a current account. Duplicates and visits do
not raise account/payment confidence. Spoofed/ambiguous/quoted/injected evidence
stays unresolved. Clinic context never establishes a diagnosis.

## Duplicates and deletion expectations

Each raw file is a separately removable fictional source; a history file may
contain several events. IDs are fixture references. SHA-256 protects synthetic
file integrity, not anonymity. Duplicate groups name the canonical event first;
exact copies add no corroboration, while distinct timestamped visits remain.

All six `after_delete` snapshots start from their complete initial source set,
independently. They cover sole-source removal, overlap in either direction,
removing everything and deleting either duplicate copy. Expectations are unchanged
from 1.0.0 and cite survivors only. The validator checks those references; it
never implements database deletion or recomputes a claim.

## Offline validation and inventory

From `backend/`:

```powershell
uv run --frozen python -m scripts.validate_corpus
uv run --frozen pytest -q
```

The CLI checks manifest structure, hashes, anchors, coverage, timestamp-exclusion
annotations, reference integrity and committed metrics. `--root` selects a copied
fictional corpus, not user imports. `--write-metrics` updates inventory counts only,
never labels, source hashes or snapshots. Tests prevent network use in validation.

Inventory: 27 raw files, 48 event cards, 29 cases, six deletion snapshots, 32 coverage
categories. Initial relationships: 13 likely-account, five transaction, two marketing,
eight visited; priority Sensitive 5 / Medium 13 / Low 10; confidence High 8 / Medium
17 / Low 3. Six unresolved items remain Unknown / insufficient. Counts are scenario
occurrences, not unique users or discovered relationships; deletion labels are separate.
Precision, recall and sensitivity agreement remain null. Coverage is not accuracy.

Version 1.1.0 changes annotation policy and approval provenance; schema major and
all raw evidence remain stable. Preserve prior versions and review records when
making later reviewed changes. The unchanged Phase 0 runtime returns empty lists.
Phase 2, broad parser/MIME robustness, real-user security, deployment and production
deletion remain outside this completed artifact phase.
