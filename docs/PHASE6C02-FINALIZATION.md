# Phase 6C-02 controlled repository finalization

Recorded 2026-11-26. Authority: the user's explicit limited approval quoted in
[the product-owner decision](PHASE6C02-PRODUCT-OWNER-DECISION.md).

Reviewed code head: `fa6748ea2b45cd1d10015421edc129259525c593`.
Unchanged reviewed base: `110b3c6353d155943bbf53798f5ec2b623dd3dd0`.
PR: [#12](https://github.com/ankit8github/FootPrint/pull/12).

## Scope and state when this documentation was committed

The owner granted a one-time repository-only engineering-risk exception and
conditionally authorized a merge commit. This documentation records that grant
before execution; it does not assert that fresh final-head CI or a merge has
already occurred. PR #12 was draft, open, unmerged and mergeable at preflight.
No reviews, inline threads or discussion comments were present at that check.

Only `PHASE6C02-PRODUCT-OWNER-DECISION.md` and this finalization document may
change relative to the reviewed code head. Every runtime, test, migration, role,
RLS, credential helper, runner and workflow byte must remain identical. The
original 252 baseline files, 193 historical blobs and Phase 6C-01 source/oracle/
catalog/registry invariants remain protected. The original NOT TESTED table and
all 24 credential-case entries are preserved in the decision record.

The F01 fixture fix remains bounded synthetic evidence: four independent
credentials, explicit role-specific selection, no shared fallback, four own-input
connections and 12 cross-role authentication rejections. The trusted test
controller remains privileged. No new security test or capability is introduced
by finalization.

## Required before the authorized merge

1. Commit/push only these documentation additions. Keep the PR draft until all
   following checks succeed for that new exact head and the reviewed base.
2. Verify fresh push and PR tenant workflows: 434 cases before downgrade and 434
   after guarded re-upgrade in each job, with unchanged committed ledger tuples.
   Verify fresh push and PR regression workflows: 1,061 backend, 284 frontend,
   nine Chromium, seven preservation, original scaffold roundtrip and frozen
   lint/format/type/contracts/corpus/registry/build/audit gates. Inspect all steps
   and decoded log evidence; require successful GitGuardian for the same SHA.
3. Recheck clean/synchronized Git state, live head/base, protected files and exact
   equality of every non-documentation byte to the reviewed code head. Recheck
   new review submissions/comments for blocking changes; do not infer independent
   human approval from an empty review list or the owner's exception.
4. If these checks pass within the accepted expiry, mark ready only as necessary
   for the authorized merge. Request method `merge` with the exact expected head;
   do not squash/rebase, bypass branch protections or force through a failure.
5. Verify GitHub's authoritative merge SHA and its two parents: unchanged base
   and verified documentation head. Verify its tree equals that head. Preserve
   receipts and publish exact-head CI links, merge result and remaining gates in
   PR metadata/delivery evidence. A local main fast-forward may then synchronize
   to that verified merge; no deployment or schema activation follows.

Any moved head/base, changed non-documentation bytes, failed/missing check,
blocking review/finding, credential exposure, RLS/context/cross-tenant failure or
expiry stops finalization. Preserve evidence and use reviewed repository rollback
or forward repair; never erase a ledger or downgrade user data. No approval is
requested again for actions already explicitly authorized, but changed scope is
not covered by this grant.

## Receipts and standing limitations

The pre-documentation exact-head runs are retained as historical receipts in the
decision/assurance records. They cannot substitute for new documentation-head
checks. The final head and run identifiers will be recorded in PR metadata and
the local finalization delivery manifest after verification. The authoritative
merge event is independently visible in PR #12; completion consumes this one-time
authorization even though this document was committed before that event.

Qualified independent human security approval and the normal gate remain
MISSING / NOT SATISFIED. Production G-S3, DB-backed endpoint authorization,
durable deletion/restore and performance remain OPEN; proposed performance
budgets remain FAILED. All explicitly NOT TESTED scenarios remain unchanged.
ADR statuses remain PROPOSED. No Phase 6C-03/04/05, real users/data, production
auth, persistence activation, external integration, public access, deployment or
beta is authorized. This is repository-only finalization of disabled synthetic
artifacts, with no continuing exception after the controlled merge is consumed.
