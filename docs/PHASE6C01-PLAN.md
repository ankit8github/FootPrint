# Phase 6C-01 plan: isolated minimized synthetic admission

2026-11-25. Implementation authority: explicit Phase 6C-01 user instruction.
Baseline: clean synchronized main/origin/main
`d6b2afde058d57e23a75b903b40231dba56a2157`; Phase 6B-04 merge
`1e4662d9a4355232fabac10d3366297032547970` is an ancestor. Branch:
`phase6c/minimized-synthetic-admission`. No reset or unrelated changes.

Read the 6A plan 6C-01, design sections 2/4/5 and S6A-12, TM-07/08/09,
6B-03 authorization, 6B-04 completion, ADR-015 through ADR-022, immutable
manifest, parser/discovery/assessment types and engines, strict Phase 2 boundary,
normal router, session/principal/fence and test helpers. Existing contracts and
ADRs are historical authority; the new field projection and canonical profiles
below are **PROPOSED for independent review**, not approved production choices.

## Acceptance IDs and sequence (written before implementation)

| ID | Implementation and evidence |
| --- | --- |
| MA-01 | Separate minimized-evidence-v1 strict schema; explicit field/enumeration/canonicalization contract before coding |
| MA-02 | Offline existing-engine generation from exact approved bytes; 29 original selections, six survivors, and explicitly enumerated reversed selections; complete content-addressed registry and deterministic check |
| MA-03 | Independent server canonical-byte membership; no client hash/flag/path authority; reject all unregistered changes atomically |
| MA-04 | Actual streamed 8 MiB bound, depth 8, strict UTF-8/JSON, extra/duplicate/prototype/nonfinite/media/encoding/transfer denial; fixed safe errors |
| MA-05 | Typed adapter unions, six kinds, exact versions/features/context, UTC semantics, row/source/reference/alias/duplicate integrity |
| MA-06 | Reuse current issuer/subject principal, CSRF/origin and subject fence; separate explicit fictional consent epoch/revision; recheck after every suspension before receipt |
| MA-07 | Default-disabled ASGI-only fixture, no normal route/OpenAPI/engine/dependency/corpus changes, no persistence/network executor |
| MA-08 | Adversarial input, two-owner preconditions, revoked/expired/epoch races, cancellation and secret-sentinel nonreflection tests |
| MA-09 | Frozen full checks, immutable historical comparison, local command evidence, fresh push/PR CI, scaffold roundtrip and GitGuardian; unmerged PR |

1. Write this plan and the field-level contract/admission design.
2. Add offline generator using existing `assessSelectedFiles` (which calls gated
   discovery/parser and assessment engines); project evidence only. Read source
   selections/deletion lists from manifest, never expected labels as rules.
3. Check in canonical batches, provenance manifest and machine-readable schema.
   Check regeneration twice and fail rather than expand profiles if unsupported.
4. Implement strict validator and server registry equality, then isolated fixture
   using unchanged session authority/fences and test-only consent controls.
5. Add adversarial and lock-order tests. Run full frozen validation. Preserve
   original CI privacy/rollback and Docker scaffold checks; add regeneration.
6. Report exact results, limitations and review status; push and open PR #11.

No shared Node executor, persistence adapter, classifications, consent UI,
idempotent saving, real inputs, tenant migrations or later phase work. If exact
canonical admission cannot be demonstrated, leave fixture disabled and report
BLOCKED. Rollback removes only these new modules/routes/tooling, never loosens
the source gate or changes historical engine behavior. P5-F01/P5-F02 and G-S3
remain open; previous ADR statuses remain PROPOSED.
