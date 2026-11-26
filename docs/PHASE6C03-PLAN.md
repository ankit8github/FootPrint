# Phase 6C-03 plan — isolated synthetic shared-rule experiment

Status: implementation plan; no merge, deployment or processing authorization.
Base: `2038c65554501b7f0a099976ea07b75606cb7ff7`; branch:
`experiment/phase6c03-shared-rules`. Local main, origin/main and live remote
matched that commit with a clean worktree before branch creation.

## Protected inventory and scope

All 270 base files are immutable in this experiment. This includes the 193
historical blobs, Phase 6C-01 contract, 32 canonical minimized batches / 70
profiles, 27 approved sources, 29 initial scenarios and six survivor oracles;
the Phase 6C-02 migrations, roles, 24 RLS tables, ledger and 434 DB tests;
existing CI, lockfiles, application behavior and 5000-ms browser deadline.
ADR-015 through ADR-022 remain PROPOSED. The old SQL candidate is not approved.

Read boundaries: implementation plan 6C-03; security design S6A-04/06/12;
threat model TM-07/09/10/13. No Python classification implementation, HTTP,
ORM, DB writes, raw parsing, provider connection or persistence activation.

## Rule sharing and execution boundary

Build a separate artifact from exact TypeScript AST declarations already in
`linkEvidence` and `assessDiscovery`, their pure helpers, fixed explanations
and PSL-aware `registrableDomain`. Verify normalized source hashes against the
immutable Phase 6C-01 registry before extraction. Package the locked tldts
implementation without browser parsers, approved-file readers or runtime
dependency imports. Record source, artifact, Node, TypeScript, tldts and lockfile
provenance. This reuses code; it does not translate business rules.

Only the existing strict minimized contract and independent synthetic catalog
may admit ordinary execution. Additional constructed minimized inputs are
unit/benchmark fixtures only, never catalog enrollment or application intake.
Version/reference validation precedes execution. The supervisor receives no
credentials and provides no HTTP/DB/network/raw-file interface. Publish one
complete validated result only after successful child exit; errors, cancellation,
deadline, memory, oversized output and malformed output discard everything.

Measure the proposed 5-second wall deadline, 256-MiB child memory, 8-MiB input
and 32-MiB output limits before proceeding. Record operating-system enforcement
separately from measured peak RSS; a heap flag alone is not a memory boundary.
Do not enlarge limits or optimize protected rule code to make a benchmark pass.
If a required bound fails, preserve the measured failure and stop implementation
for review. Unsupported platform enforcement must fail closed or be NOT TESTED.

## Provenance adapter

Use synthetic UUID identities assigned independently of source contents and raw
hashes, scoped explicitly by owner/collection; derived references also bind the
generation. Maintain bijective source/row/observation and result mappings.
Reject missing, extra, repeated, malformed or foreign scoped references rather
than filtering them away. Never infer equivalence from minimized value equality.

Retain every duplicate member and its own context. Survivor projection removes
only explicitly selected synthetic sources, picks a surviving primary in stable
source/row order, remaps local ordinals and domain-scoped commercial aliases,
then invokes the same pure rules. No result/assessment supplied by a browser is
accepted as authoritative. Compare full outputs and support provenance, including
conflicts, unknowns, explanations and eligible action IDs.

Map to the existing typed 6C-02 structures only where lossless. In particular,
`finding_evidence.evidence_role` has primary/corroborating/context, whereas the
engine has a duplicate role. Duplicate membership must remain in the typed
equivalence group, never be relabeled independent corroboration. Catalog prose
and action URLs are not persisted. Document every projection gap and reject any
projection requiring a schema change; do not alter the SQL.

## Validation matrix and rollback

- All 70 immutable profile discovery and assessment hashes; existing 29 + six
  oracle field comparisons, reversed source order and deterministic serialization.
- Both email/history duplicate removal orders, primary promotion, per-copy
  context, context-only source removal, coincident nonequivalent observations,
  same/different order conflicts, unpaid invoice, invalid history time,
  unresolved-only and empty input; all seven unknown claims remain unknown.
- Invalid version, identity, owner/collection/generation, duplicate/commercial
  membership, support and malformed output rejection; bijection and completeness.
- Bounded worst-case 10,000-row benchmarks, input/output edges, deadline,
  interruption, child exit and memory termination; no partial publication.
- Frozen 1061 backend / 284 frontend / nine Chromium / seven preservation cases,
  434 DB cases before and after guarded re-upgrade with ledger receipts preserved;
  lint/types/build/audits/corpus/contracts/registry and all 270 base blob checks.
- Separate additive CI only, fresh exact-head push and PR receipts, secret scan.
  Record counts actually executed and explicit NOT TESTED limitations.

Rollback is removal/disablement of these new offline artifacts; no stored data
or deletion journal is rolled back. There is no save/recompute route to enable.
Keep PR draft/open/unmerged. Any semantic mismatch requiring protected changes,
unsupported provenance, unrepresentable necessary semantics or failed resource
budget stops this phase. Production G-S3, P5-F01/P5-F02, qualified independent
human review, legal/provider/security and durable lifecycle gates remain OPEN.
