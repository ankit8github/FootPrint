# Phase 6C-01 product-owner exception decision

Prepared 2026-11-25 for [PR #11](https://github.com/ankit8github/FootPrint/pull/11).

**Owner decision: APPROVED, limited repository-only exception. Merge: authorized
only after fresh exact-head CI/security checks and unchanged-boundary verification.**
Qualified independent human security review remains **MISSING**. The normal
independent approval gate is **NOT SATISFIED**. This record documents the user's
explicit engineering-risk acceptance; it is not independent security approval
or certification.

## Purpose and accountable decision maker

The approved purpose is repository-only synthetic engineering continuation:
merging disabled fictional research code after an explicit, limited engineering
risk acceptance. The requesting user is the accountable product owner. No owner
signature, legal name, named human security reviewer, qualifications, independence
declaration or independent human security approval has been supplied or fabricated.

The original preparation request was conditional on a separately explicit owner
approval. The user subsequently supplied that approval in the conversation,
recorded below on 2026-11-25. At preparation and approval preflight, GitHub
contained no review submissions, discussion comments or inline review threads
recording an approval. Codex performed the implementation, AI-assisted review,
remediation and this verification; these activities are not qualified independent
human review. Empty reviews and successful automated checks do not satisfy that
gate.

## Exact scope and verified state

| Item | Verified value |
| --- | --- |
| PR head | `41f8aac5c9b817012162b8abb297f09ddd173cb0` |
| Base, local main and origin/main | `d6b2afde058d57e23a75b903b40231dba56a2157` |
| Verified repair code head | `91ee1a14842a2991a17ae7049b532c541b2637d2` |
| Difference from repair code head | Only `docs/PHASE6C01-AI-ASSURANCE.md`; no runtime/test changes |
| Remote PR state | OPEN, unmerged, mergeable; no submitted reviews or comments |
| Worktree before preparing this draft | Clean and synchronized with the remote feature branch |
| Existing PR inventory | 58 files: 57 additions and one additive baseline workflow change |

All 193 protected historical files match the base Git objects. The sole changed
baseline file is `.github/workflows/phase0.yml`, which adds mandatory minimized
schema/registry checks. Corpus, engines, Phase 2 contracts, prior tests, frontend,
dependencies, prior experiments and the exact 5000-ms worker deadline are
unchanged. ADR-015 through ADR-022 remain unchanged and **PROPOSED**.

The offline generator reproduces all **70 profiles / 32 canonical batches** from
the original 27 approved sources, 29 scenarios and six deletion-survivor selections
using the existing engines. Neither labels nor expected oracle results compute
admitted evidence. Registry byte equality and the following pins are preserved:

- Corpus manifest SHA-256:
  `53b4ff49c5b31e4fa5b2670c757c02058d0ffab3f6b0472fe8d198a86bdd36b1`.
- Admission manifest SHA-256:
  `333c513165273846a4645c74ba604900266d88e10fb6eda1848e0195949b0699`.

The fixture is default-disabled, explicitly activated ASGI-only test code,
unmounted from the normal app and absent from public OpenAPI. An environment flag
does not activate it. There is no serving CLI, listener or deployment path for
the fixture. Admission returns a validation-only receipt, with no batch write,
retention, session touch or revision advance. Disposable fictional session and
consent state are test controls, not real authentication or save consent.

## AI-assisted evidence and resolved defects

The [assurance record](PHASE6C01-AI-ASSURANCE.md),
[contract](PHASE6C01-MINIMIZED-CONTRACT.md),
[admission security analysis](PHASE6C01-ADMISSION-SECURITY.md) and
[review record](PHASE6C01-REVIEW.md) retain reproductions and limitations.

| Finding | Engineering disposition |
| --- | --- |
| AA-01 | RESOLVED: both direct entry points inspect faithful retained model/internal state, reject extras and malformed known fields, then strictly revalidate before serialization. No silent projection into acceptance. |
| AA-02 | RESOLVED: malformed supplied models never reach a serializer; fresh validated models use a local fail-on-warning boundary. Fixed denial without input-bearing warnings, stderr, DEBUG metadata or arbitrary repr calls. |
| AA-03 | RESOLVED: raw ASGI header names are validated case-insensitively before framework parsing, with duplicate values/order retained. All eight original mixed-case negatives deny before body reads; historical Phase 6B code is unchanged. |

All 17 original failing assertions were reproduced before repair and now pass as
ordinary regressions with no xfail markers or weakened controls. The preparation
check reran their original filter with `--runxfail`: **17 passed, 52 deselected**.
Deselection is the explicit filter, not a skipped or expected-failure test. The
default-disabled/normal-app separation test also passed (**1 passed, 350
deselected**), and readonly offline generation passed with exact catalog equality.
Four recorded seeds (60101 through 60104), 1,024 bounded mutation attempts and
both-owner consent/session/revocation race evidence remain in the assurance record.

Final-head CI was rechecked against the exact PR head above:

| Check | Evidence | Result |
| --- | --- | --- |
| Push CI | [45593296985](https://github.com/ankit8github/FootPrint/actions/runs/45593296985), job 139132764977 | SUCCESS |
| PR CI | [45593309492](https://github.com/ankit8github/FootPrint/actions/runs/45593309492), job 139132812364 | SUCCESS |
| GitGuardian | [139132802224](https://github.com/ankit8github/FootPrint/runs/139132802224) | SUCCESS; secret scanning only |

Both decoded CI logs confirm **1,061 backend tests, 284 frontend tests, nine
Chromium scenarios and seven production privacy/rollback scenarios** passing,
with zero test skips/xfails. Frozen lint/format/types, contracts, corpus/schema/
registry checks, builds and audits pass. CI also verifies the original PostgreSQL
scaffold upgrade/constraint/downgrade/re-upgrade with no personal tables. It does
not establish restricted-role, RLS or tenant endpoint security. Performance budgets
remain FAILED despite successful preservation scenarios. These full-suite results
are verified existing exact-head CI evidence; only the focused checks and readonly
generation described above were rerun while preparing this draft.

## Approved limited exception and expiration

The explicit owner approval authorizes **only merging the disabled
fictional Phase 6C-01 research code in PR #11**, plus the documentation and fresh
CI required to record and finalize that decision. The reviewed runtime, tests,
catalog and security boundaries must remain identical to the head above. Any
documentation commit changes the PR head and requires fresh exact-head push/PR CI
and GitGuardian evidence before a merge commit. A material code change requires
a new decision; this record cannot authorize it.

This is a product-owner engineering-risk exception to the merge gate,
without satisfying or reclassifying the missing independent human review. It
does not waive any production, deployment, real identity/data or persistence
gate, approve any proposed ADR, or authorize another phase.

The exception expires at the **earliest** of:

1. The next material security-sensitive change.
2. Any attempted activation or public exposure of the experiment.
3. A new review decision.

The exception applies solely to this controlled merge/finalization. Expiration
cannot authorize a new capability or further phase work.

## Residual risks and outstanding gates

- Qualified independent human security review and recorded approval remain
  MISSING; AI review, test counts and secret scanning are not certification.
- G-S3 remains OPEN: real restricted-role PostgreSQL/RLS, tenant foreign-key/pool
  behavior and endpoint proof are missing. Scaffold migrations do not close it.
- P5-F01 remains OPEN following the rejected performance candidate and failed
  budgets. P5-F02 ownership/link concerns remain OPEN.
- Vendor/Auth0, accountable ownership, legal/retention and independent security
  decisions remain unresolved. This merge exception does not approve them.
- No production browser/auth integration, distributed lock, durable session,
  revocation, consent, lifecycle or persistence guarantee exists. Fictional test
  consent is distinct from future persistence consent.
- Stream wall-time, frame-count, concurrency and queue bounds remain unverified.
  Underdeclared bodies can be consumed up to the bounded 8-MiB limit before length
  rejection; early disconnect produces a fixed 503. No production proxy/APM or
  operating-system resource-isolation claim is made.
- Registry membership permits replay of public fictional shapes; it does not
  attest source files, events, accounts, identity or assessment truth. Receipts
  mean validation-only, never saved, genuine or authoritative.
- Retained-state checks cannot reconstruct fields discarded before the boundary
  or sandbox hostile Python/interpreter changes. Secure memory erasure is not
  demonstrated. An already delivered response cannot be recalled.

## Prohibited capabilities and rollback conditions

No Phase 6C-02 or later work, tenant schema/RLS implementation, durable personal
data, real users, production authentication, provider connection, public intake,
save UI, deployment or beta enrollment is authorized. No activation shortcut,
validation relaxation, corpus/engine/oracle change or accepted-profile expansion
is authorized by this exception.

Before any future authorized merge, a changed head/base, failed mandatory check,
new blocking finding/comment, altered protected bytes or fixture exposure must
stop finalization for review. If a boundary regression is discovered afterward,
stop the affected experiment, preserve evidence, and prepare a reviewed rollback
of the Phase 6C-01 change to the verified prior state. Do not mask a failure by
weakening tests or suppressing validation. Keep the fixture disabled throughout;
rollback does not authorize deployment or production processing.

## Explicit owner decision record

| Required record | Current value |
| --- | --- |
| Accountable product owner | Requesting user; no signature or legal name supplied |
| Explicit owner approval | **APPROVED in the user's explicit follow-up message**, limited scope below |
| Approval evidence / timestamp | Conversation quotation below; recorded 2026-11-25 (not a fabricated signature or independently authenticated timestamp) |
| Qualified independent human reviewer / approval | **MISSING** |
| Normal independent approval gate | **NOT SATISFIED** |
| Exception | **GRANTED for repository-only disabled fictional research code** |
| Merge authorization / authoritative merge SHA | **CONDITIONAL ON FRESH CHECKS / NOT YET MERGED** |

The requesting product owner's actual follow-up approval is reproduced verbatim
below. This is conversation evidence of the accountable owner's decision, not a
signature, qualified independent review or GitHub review approval:

> I approve the limited repository-only Phase 6C-01 engineering-risk exception described in `docs/PHASE6C01-PRODUCT-OWNER-DECISION.md` for FootPrint PR #11 at reviewed head `41f8aac5c9b817012162b8abb297f09ddd173cb0`.
> I acknowledge that qualified independent human security approval remains missing and the normal review gate is not satisfied.
> I accept the documented residual risks, prohibited capabilities, rollback conditions and exception expiration.
> I authorize committing the decision documentation and, after fresh exact-head CI and security checks pass, merging PR #11 using a merge commit.
> This approval does not authorize Phase 6C-02, production authentication, personal-data persistence, external integrations, deployment or beta access.

Finalization may now commit only required decision/report documentation, obtain
fresh exact-head CI/security evidence, recheck preservation and use a merge commit.
The authoritative merge SHA and finalization evidence must be recorded after the
actual merge. No approving GitHub review is submitted or inferred. Historical
PENDING / NOT GRANTED and open/unmerged statements in earlier evidence describe
the state before this explicit owner decision; they are not independent approval.
