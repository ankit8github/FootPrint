# PV1 fictional corpus 1.0.0

**Phase 1 test artifacts only.** All messages, recipients, organizations, identifiers,
and browsing events were authored from scratch. No user export, mailbox, actual
purchase, diagnosis, name, street address, credential or payment card was used.
The proposed truth labels await independent human review; no classifier exists.

For independent human review, start with the blank
[HUMAN-REVIEW-WORKSHEET.md](HUMAN-REVIEW-WORKSHEET.md) and save judgments before
reading the proposed labels or annotation choices below. It includes all 29
scenarios, all six deletion snapshots and raw references. After the blind pass,
consult the [proposed taxonomy clarification](../../../../docs/PHASE1-TAXONOMY-PROPOSAL.md);
no definition change or human approval is implied by that note.

Use [CATALOG.md](CATALOG.md) to locate 27 raw files and 29 scenarios,
[manifest.json](manifest.json) for evidence anchors and explicit expected labels,
[metrics.json](metrics.json) for inventory/coverage results, and
[REVIEW.md](REVIEW.md) for the unfilled independent-review checklist.

## Raw formats and safety

- `emails/`: 20 selected-message `.eml` files, preserved as UTF-8 bytes with CRLF
  lines and an `X-PV1-Fixture: synthetic-only` marker. Includes plain text,
  HTML-only, multipart/mixed with one inert text attachment, an encoded subject,
  malformed Date and missing From. No MIME decoder is implemented here.
- `history/`: seven JSON files using `{"Browser History": [...]}`. Ordinary rows
  have `url`, numeric `time_usec` (UNIX microseconds UTC), and optional `title`.
  The authored shape and timestamp meaning follow the primary
  [Chrome history reference](https://developers.google.com/data-portability/schema-reference/chrome).
  One fixture uses its encrypted/unavailable-history string. The deliberately
  invalid-time rows are negative cases, not valid source records.
- The fixed review reference time is `2026-10-20T00:00:00Z`. Valid event dates
  are pinned; invalid dates remain null in annotations. No current clock or
  completeness claim affects labels.
- All email addresses and ordinary web domains use reserved `.test` names.
  Unsafe vectors intentionally include loopback/private IPs, localhost,
  malformed/relative URLs and `file:`, `javascript:`, `data:`, `ftp:` and
  `chrome:` schemes. They are inert text. **Do not open/fetch embedded links,
  render email HTML, execute scripts, or open the attachment.**
- Query, fragment and URL userinfo contain obvious `SYNTHETIC_...` sentinels,
  never working tokens/passwords. Their only purpose is to specify future
  minimization expectations. No raw export is sent to the API or database.
- The `.gitignore` exception permits `.eml` only in this exact corpus email
  directory; general email exports remain ignored. `.gitattributes` preserves
  raw email bytes and LF JSON so inventory hashes work on Windows and Linux.
  The scoped whitespace attribute recognizes MIME CRLF rather than treating
  every carriage return as accidental trailing whitespace.

The validator's 64 KiB per-file budget bounds these small repository fixtures.
It is not a product upload limit or a choice between the conflicting proposed
limits in documents 02 and 04. No broad inbox/large-file/fuzz benchmark is run.

## Manifest and label semantics

The manifest schema is `phase1-ground-truth-v1`; corpus version is `1.0.0`.
Each source has its path, exact checked-out SHA-256, future adapter name, tags,
and event cards. Each event has a whole-message or JSON-row locator, literal
anchors, a proposed disposition, observation kind, domain label, timestamp
annotation and reason. Literal anchors link the annotation to raw evidence;
they do not make sender/authentication headers trustworthy.

Each case lists its selected sources, coverage, human-readable rationale, and
an explicit expected snapshot. Snapshot labels separate relationship type,
observed/inferred state, confidence, and Sensitive/Medium/Low review priority.
Unresolved evidence is a separate **Unknown / insufficient** review item,
not an established relationship and not a forced Low classification.
Every relationship keeps retention and data-sale status `unknown`.

Expectations are authored data, not outputs from code. The validator checks
their vocabulary and internal references; it does not decide that a welcome
message is registration, interpret spoofing, or classify a receipt. No future
normalizer, parser, scoring service or runtime contract is approved by them.
The API still returns its Phase 0 empty lists, with unchanged OpenAPI/types.

Specific annotation choices for reviewer adjudication:

- A first-party-looking account message supports a likely account with medium
  confidence, not a confirmed/current account. Synthetic authentication headers
  are not cryptographic proof. Visits or duplicate messages do not raise that
  account/payment confidence.
- A receipt or unpaid invoice is a transaction indication and Sensitive review,
  not proof of retained payment credentials. The conflicting receipt/cancellation
  case keeps low confidence in a transaction indication and cannot assert paid
  status. The clinic case indicates context only, never a medical attribute.
- Spoofed origins, unmapped shared delivery, a generic welcome, quoted signup,
  and prompt-like instructions remain unresolved. HTML and attachment content
  are not executed and do not supply additional trusted evidence.
- Invalid time values are annotated with null event time; the missing required
  history field is an excluded record. These proposals need review before a
  Phase 2 adapter decides real validation behavior.

## Duplicates and source-deletion oracles

Every raw file is treated as a separately removable fictional source for these
scenarios. A history file can have several events. IDs are fixture references,
not real user IDs, actual message identifiers, or privacy-preserving hashes of
people. SHA-256 here protects public synthetic file integrity, not anonymization.

`duplicate_groups` list the canonical event first and exact copied event(s)
after it. The second email retains the first email's message bytes/Message-ID
but has a distinct fixture source ID. Distinct timestamps in the history file
remain separate events. They do not create multiple same-type relationships.

Each `after_delete` snapshot is hand-authored relative to the case's complete
initial source set, **not sequentially applied**. The six snapshots cover sole
support removal, email/history overlap in either direction, deleting everything,
and deleting either duplicate copy while citing only surviving evidence.
The validator checks references against the declared remaining sources. It
does not delete database rows, infer replacement claims or recompute anything.

## Run the offline checks

From `backend/` (PowerShell):

```powershell
uv run --frozen python -m scripts.validate_corpus
uv run --frozen pytest tests/test_phase1_corpus.py -q
```

The CLI emits deterministic inventory metrics and exits nonzero on an invalid
manifest, missing/changed/unlisted fixture, missing evidence anchor, invalid
label, coverage gap or stale deletion citation. It checks committed metrics for
drift. `--root <directory>` is for reviewing/testing a copied **fictional** corpus,
not a user-import interface. `--write-metrics` updates counts only; it never
repairs hashes, proposes labels, changes snapshots or fetches any URL.

`uv run --frozen pytest -q` also includes all Phase 0 tests and these new corpus
tests in the existing unchanged CI workflow. No extra dependencies are needed.
The mutation tests change only temporary copies, never the committed raw files.

## Coverage and inventory benchmark

The pinned inventory contains 20 email events and 28 history entries (48 total),
29 scenarios, six deletion snapshots and 32 required coverage categories.
The coverage map lists scenario IDs for every required category, including all
categories in the Phase 1 assignment and a few bounded MIME/source variants.
Relationship-label counts are **scenario occurrences**, not distinct people,
relationships in a live application, or discovery results. Unresolved counts
separately show Unknown/insufficient examples. Deletion snapshots are counted
separately from initial snapshot labels.

Precision, recall and sensitivity agreement are explicitly null: there is no
parser/classifier to evaluate. Passing 32 coverage categories is an artifact
coverage result, not 100% product accuracy, abuse resistance or privacy efficacy.

## Independent review and versioning

Review the source bytes first, using the source IDs and manifest anchors, without
looking at any future algorithm output. Write independent labels, confidence,
sensitivity, unknowns and deletion expectations. Then compare with the manifest,
record disagreements and adjudicate them in the PR using REVIEW.md. Raw HTML
and links remain untrusted throughout. No independent reviewer has signed off.

Do not tune truth to a future classifier's predictions. Changes to raw evidence
or settled labels require a reviewed corpus-version change and fresh hashes,
coverage metrics and tests; preserve the prior published version for comparison.
This first version remains a proposed baseline until independent adjudication.
The package covers a small fictional world, not all Gmail/Outlook encodings,
real Takeout variants, spoofing patterns, giant files or production deletion races.
