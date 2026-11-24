# Phase 5 implementation plan and acceptance checklist

Date: 2026-11-24 (Asia/Calcutta). Base: synchronized, clean main
20709ccc21fec9c49b0af7c316fdc9a0f1caee96, parent Phase 4 merge
f3dd579db4ef87d4adbbb2d771224deba6923133. No ground-truth changes authorized.

## Implementation sequence (written before coding)

1. Add /phase5 while preserving /, /phase2, /phase3, /phase4. Compose the existing
   assessSelectedFiles and constrained AssessmentDetails; no new inference rules.
2. Build a session controller owning a single list of File references outside
   React state. A fresh bounded worker invokes Phase 4 for every selection/removal.
   Drop old results immediately; terminate workers on supersession, error,
   deadline, clear, consent withdrawal, pagehide and unmount. Guard stale replies.
3. Render safe source indices, counts, priority/type/confidence filters, fixed
   explanations and primary/duplicate source-row provenance. Empty, busy, error
   and filtered-empty outcomes are accessible. Never display raw filenames.
4. Add independently reviewable static synthetic action entries, literal .test
   destinations and documented review basis; no inferred links or network checks.
   Open only by explicit click with noopener/noreferrer; record only opened in
   transient state. Retire actions/results on recomputation and clear.
5. Test the actual session removal path against all six immutable survivor
   snapshots, all 29 initial cases, order/duplicate/conflict/context cases and
   lifecycle races. Add integrated real-worker Playwright/security/UX coverage.
6. Run existing backend/frontend checks, contracts, audits, preservation checks,
   fresh checkout and GitHub CI including Docker migrations. Document observed
   results and limitations, update ADRs, open PR against main, do not merge.

## Acceptance checklist

- [ ] Integrated consent -> file selection -> findings -> details -> opened action
      -> source removal -> full recomputation -> clear works in real browser.
- [ ] Exact approved SHA-256 gate, .test restriction, MIME/JSON bounds, 20 files,
      1 MiB/email, 10 MiB/batch, 10,000 records and five-second deadline preserved.
- [ ] Priority, type and confidence counts/filters; Unknown and excluded visible;
      evidence state, fixed reasons, limitations and safe provenance explained.
- [ ] Every directory entry reviewable; unavailable links use exact fallback;
      no auto-actions, redirects, discovery or false completion claims.
- [ ] Removal uses only remaining sources, preserves duplicate alternatives and
      retires stale rationales, priorities, evidence links and action associations.
- [ ] Six survivor oracles and all 29 initial immutable scenarios pass unchanged.
- [ ] Clear, withdrawal, navigation and unmount discard sources/results/actions;
      worker deadline/error/races tested; no raw contents in React state/storage.
- [ ] Egress, WebSocket frames, secrets, console, cookies, storage and lifecycle
      checks pass; raw filenames/content never rendered or logged.
- [ ] Phase 0-4 routes/tests, APIs/contracts, migrations, corpus and locks preserved.
- [ ] Lint/types/unit/E2E/contracts/audits/build/fresh-checkout CI/Docker pass;
      Vite size advisory recorded without unrelated refactoring.
- [ ] ADRs/report include architecture, screenshots, exact tests/security evidence,
      memory limitations and exit gates; PR #5 exact head and CI links recorded.
- [ ] No merge, deployment, real data, persistence, auth, external AI or Phase 6.
