# Phase 6 blocker resolution plan — proposed, gates remain STOP

Prepared 2026-11-27, Asia/Calcutta. This is an architecture/verification candidate
for **C03-NET-01** and **C03-LIFE-01**, not approval, an installed migration, an
adopted executor or completion of 6C-03. No 6C-04/05/6D implementation is included.

**Disposition: STOP for adoption/resumption of dependent implementation.** The
recommendations below are concrete enough for design review, but the full OS
boundary, complete PostgreSQL contract and human acceptance are not demonstrated.
Passing a building-block test or the SQLite model does not close either gate.

## 1. Exact starting state and scope

| Ref | Verified exact SHA | State |
| --- | --- | --- |
| main / origin/main / live main | `2038c65554501b7f0a099976ea07b75606cb7ff7` | Unchanged |
| PR #13 | `511dfee080d3bcd3c68aaa35ec1474700ff0cf63` | Draft/open/unmerged |
| PR #14 | `49268baa18af77f020b6dbc9d8f27e89558ed6c3` | Draft/open/unmerged |
| PR #15 / clean initial HEAD | `e269f048f6e6e5c2c2c83df32828f413139384d6` | Draft/open/unmerged |

One worktree, `I:/FootPrint`; no AGENTS.md found. Existing local shared-rules
branch was already ahead of origin at `e70447788145638fa6a4554b1b71503c8fee2c8a`
and is preserved. New branch: `design/phase6-blocker-resolution`, based exactly on
PR #15. No previous branch is reset, amended or pushed. Final commit SHA and
fresh exact-head CI are recorded in the new draft metadata/final delivery, avoiding
a self-referential SHA in this document. PR #13/#14/#15 remain untouched.
Proof-only implementation commit:
`0d8da194f455fc87cc368b049de4cf6b8fac00a8`. The subsequent plan/receipt/CI commit
does not change those probes or any application code.

Read the executor safety/final readiness/master reports, PR #14 adoption review
and complete migration SQL, 6C-02 typed schema/grants/triggers, shared/versioned
executors, package manifest, roadmap 6C-03–6D gates, security S6A-03/04/05/06/07/12
and TM-07/09/10/13–17. All historical failures and immutable oracles are retained.
The authenticated shell uses only command-local Git ownership exceptions.

## 2. Track A decision: offline Linux worker, conditional on platform acceptance

**Recommend a dedicated, offline Linux x86-64 worker environment with a
read-only pinned image, isolated namespaces, an ABI-checked default-deny seccomp
profile and cgroup v2 enforcement established before worker execution.** On this
Windows development host use an independently reviewed local offline Linux VM;
do not silently substitute WSL, Docker networking, Node flags or native Windows.
No VM, cloud resource, runtime installation or network policy is provisioned here.
SEC/OPS must accept this supported-platform choice; if native Windows execution is
mandatory, this recommendation cannot be adopted and the Windows alternative
needs its own completed proof. Windows/other platforms return
`ISOLATION_UNAVAILABLE` for this proposed profile, with no ordinary-Popen fallback.

The proposal is source-informed engineering inference, **not measured containment**.
Linux documents syscall filters as a component rather than a complete sandbox;
namespace, descriptor, filesystem, privilege and lifecycle controls below are
therefore inseparable from the proposal. [Kernel seccomp documentation](https://www.kernel.org/doc/html/latest/userspace-api/seccomp_filter.html),
[OCI Linux configuration](https://github.com/opencontainers/runtime-spec/blob/main/config-linux.md).

| Alternative | Advantages | Reason not recommended as the sole boundary |
| --- | --- | --- |
| Current Windows Job + Node permissions | Existing pinned worker runs; process memory/cleanup evidence | Sentinel transmission reproduced; attach-after-Popen start race; no aggregate job cap or bounded decode |
| Native Windows AppContainer/LPAC + creation-time Job | Windows kernel token/capabilities, explicit handles, pre-start job assignment | Profile/artifact ACL prerequisites and DNS/broker paths need proof; native launch here failed before resume; do not grant ACLs or exemptions to make a test green |
| Windows Sandbox/Hyper-V without networking | Separate kernel, useful defense in depth | Feature/edition and headless transport/startup/caps need review; network-off alone does not deny in-guest loopback |
| OCI `network=none` or a network namespace alone | Removes ordinary external routes | Loopback and inherited sockets/brokers can remain usable; insufficient alone |
| Dedicated offline Linux environment + combined controls | Direct syscall/FD restrictions, aggregate resource accounting, no Windows policy edits | Requires reviewed image/runtime/kernel pins and an actual deployed-boundary proof; not available locally yet |

Microsoft documents AppContainer creation with `SECURITY_CAPABILITIES`, an
explicit inherited handle list, and creation-time job assignment. The separate
Windows probe uses these with zero capabilities, a suspended main thread and
both process/job memory limits. It derives a random SID in memory; it does **not**
create a profile, alter an ACL, grant a loopback exemption or change firewall
policy. [Process attributes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute),
[AppContainer launch](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer),
[Job memory fields](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information).

### A1. Required process-start order and isolation policy

The reviewed implementation must perform this order; a failure at any step
destroys the candidate job and exposes no successful result:

1. Verify the original package manifest/worker/pure/source pins and a **separate**
   immutable isolation-profile manifest. Pin exact Node 22.15.0 Linux binary,
   launcher, helper, image, seccomp and approved kernel/runtime builds. No mutable
   tag, runtime download, fabricated digest or re-pin of an old package is allowed.
2. Reserve the single bounded execution slot; no unbounded queue. Create the
   cgroup and configure/read back `memory.max=268435456`, `memory.swap.max=0`,
   `memory.oom.group=1`, and proposed `pids.max=64` including threads. The worker
   must start in this cgroup through a trusted runtime/creation primitive, not run
   arbitrary code and be moved later. Cgroup membership is not writable from the
   worker. The image contains no general-purpose services, shell/toolchain or
   resolver broker. [cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html).
3. Establish fresh user, mount, PID, IPC and network namespaces inside an offline
   environment with no vNIC/routes to host/LAN/Internet. Mount only the pinned
   read-only runtime/artifact and minimal private proc/dev resources. No host
   directory, DB socket, D-Bus/nscd/resolved socket, Docker API, credential store,
   shared memory broker or writable executable is exposed. No network-capable
   host service proxies worker requests. Mount restrictions/LSM/image approval
   are mandatory; seccomp alone is insufficient filesystem isolation.
4. Close every descriptor except **three newly created anonymous pipes**; verify
   descriptor types. No inherited socket, token, pidfd, namespace/cgroup handle,
   control socket or network-namespace FD. Use an environment allowlist with no
   proxy variables, `NODE_OPTIONS`, credentials or host resolver injection.
5. Drop capabilities and supplementary groups, set `no_new_privs`, then install
   the reviewed architecture-checked **default-deny** seccomp allowlist before
   `execve` of the pinned Node binary. The filter must deny network/socket
   operations, AF_UNIX broker transports, `io_uring_*`, `bpf`, `ptrace`, namespace/
   mount escape and process-memory access. Reject alternative/x32 ABIs. Allow
   only audited thread creation: `fork`/`vfork` and non-thread `clone` denied;
   `clone3` returns ENOSYS for an explicitly tested libc fallback. Do not permit
   a clone3 pointer-based filter that cannot validate pointed-to flags.
6. Start the unchanged worker only after containment. Begin its unchanged
   **five-second wall deadline at process creation**, covering startup, input,
   computation and serialization. Supply only the existing strict minimized
   synthetic input, never owner/session/DB credentials, raw parsers or new source
   admission. Kernel/runtime setup is also independently time bounded.
7. Drain bounded pipes concurrently; require successful root exit and complete
   output. Cancel, timeout, cap hit, I/O failure or unexpected exit invokes
   `cgroup.kill`, bounded wait/reap and `cgroup.events populated=0`. A signal to
   just the root/CLI is insufficient. A cleanup failure quarantines the slot and
   blocks subsequent intake; do not report success or silently reuse the slot.

A network syscall must be rejected **before any connection/query**, independently
of destination: IPv4/IPv6 loopback, private/link-local/LAN, Internet, TCP/UDP/raw
and Unix broker sockets. DNS transport is included; no query is forwarded to a
host resolver. A literal/hosts-file answer from a name API is not DNS egress and
must not be represented as proof of a DNS query. Test actual resolver/broker and
inherited-capability bypasses in an offline lab, with observers/positive controls.

### A2. Caps, parent decode and pinned worker compatibility

`blocker_proofs/isolation-profile-proposal.json` records exact proposed values.
It is deliberately **not executable configuration**: absent image/runtime/runner/
filter digests keep it disabled. Existing limits remain **5 s / 256 MiB / 8 MiB
input / 32 MiB output**; stderr remains 8192 bytes. The proposed 256-MiB cap is
aggregate across the processing cgroup, including unexpected descendants.

Untrusted decode/model validation must leave the API process. Use one-shot
input-validator / Node / output-decoder stages **sequentially in the same bounded
processing cgroup**, each helper with proposed five-second wall bound. A native
broker has proposed 64-MiB separate cap and fixed-size I/O buffers; its small
control frames are capped at 4096 bytes. No unrestricted `json.loads` of the
32-MiB child response in the API or unsupervised broker. The decoder enforces
duplicate/prototype/nonfinite rejection, proposed depth 32 / two million tokens,
exact envelope/types/versions and complete typed output support. Oversize/OOM/
decode deadline rejects the entire candidate, not truncation or partial output.
Existing accepted fixtures, including exact-cap tests, must still be accounted
for; reject a proposed cap that fails required valid cases rather than weaken
their assertions. These new helper/controller budgets need SEC/OPS acceptance
and actual measurement; the existing worker bound is never extended. Original
Phase 5 frontend/browser deadlines are untouched.

The original indexed worker bytes remain
`f4170b61857e2ae673332e4d57cd01cab5214ede7f4c3b3abef390221258670a`, manifest
`7485ac86c2cd9502e1414d68df7a930ae531b209706d44b8161a736ec7e24055`, pure prefix
`5e980c1c1856226ef6b2ce35b9b4eb651d5860139ba6041a4ffe76ffb262d1e7`.
The new isolation manifest identifies *how* those bytes run and is separately
attributable to each live generation. An alternate OS binary/image is a new
execution profile, not semantic-rule permission or client-selected revision.
Verify parity on all 70 profiles / 32 batches, original 29 + six oracles, actions,
support order, unknowns and four 10,000-row fixtures **inside** that profile. A
cross-platform difference stops adoption; never rewrite the oracle or use Python
inference. The supervisor, not a worker-supplied hash, issues the execution nonce
and validates actual immutable file/image handles before matching the DB binding.
This is trusted local execution evidence, not remote hardware attestation.

### A3. Executable evidence and remaining required acceptance

Commands, run from `backend`, use frozen dependencies:

```powershell
uv run --frozen pytest -q -s executor_safety_tests/test_boundary.py::test_no_network_gate_with_loopback_only
uv run --frozen python -m blocker_proofs.windows_probe
uv run --frozen python -m blocker_proofs.benchmark_candidate
uv run --frozen python -m scripts.benchmark_rule_packages
# Linux x86-64 only; short-lived child's filter, no host policy edit:
python -m blocker_proofs.linux_network_probe
```

The original sentinel test is unchanged and **still fails** with connected=true /
one received sentinel. The Windows creation probe **STOPPED with winerror 2 at
CreateProcessW, before resume**; this does not diagnose a specific profile/ACL
cause. BFE/MpsSvc were running; the Node file ACL inventory did not include an
explicit AppContainer grant. No profile/ACL repair was attempted. Its startup
benchmark also STOPPED, measuring **zero isolated workloads**. Do not equate zero
packets after failed startup with network denial. The Linux building-block probe
fails closed locally with `LINUX_X86_64_REQUIRED`; its separate Linux CI result,
if executed, is recorded as **syscall-only evidence**, not Node/namespace/cgroup
or full-boundary acceptance. Its demonstration filter is not the final allowlist.

| Required acceptance ID | Test/observer requirement | Current coverage |
| --- | --- | --- |
| NET-START | Payload attempts egress as its first instruction, no stdin cooperation; containment/config read back before exec | Native creation probe stops before execution; full proposed profile NOT TESTED |
| NET-TRANSPORT | IPv4/IPv6 loopback, LAN/link-local, Internet and DNS TCP/UDP; local receivers and packet counters with permitted positive controls | Current loopback bypass reproduced; Linux probe tests address-independent socket refusal, not actual destinations |
| NET-BROKER | AF_UNIX/socketpair, resolver IPC, inherited connected sockets/namespace FDs, io_uring | Linux building-block covers socket/Unix/socketpair syscall denial + stdio-only descriptors; complete broker/async matrix NOT TESTED |
| NET-DESC | Fork/exec/thread floods, non-thread clone, clone3, exec replacement, PID namespace and no cgroup escape | Required profile/runtime proof, NOT TESTED here |
| NET-RESOURCE | Root+descendant aggregate commit just under/over 256 MiB, swap off, PID bound, CPU/wall deadline and cancellation in every phase | Old per-process evidence preserved; new aggregate/decode tests NOT TESTED |
| NET-OUTPUT | Exact/over caps, malformed/truncated/duplicate JSON, valid prefix + bad exit, depth/token bombs and decode OOM/deadline | Existing 38 passing checks retained; actual new bounded decoder NOT IMPLEMENTED |
| NET-CLEAN | Kill during startup/write/read/exit, stuck descendants, close all pipes, observe empty cgroup before release; supervisor crash/reaper | Existing Job Object evidence separate; proposed profile NOT TESTED |
| NET-PARITY/PERF | All original oracles plus 70/32 parity and unchanged 5-second/four-fixture resource matrix; cold/warm launch and decode memory/time | Current unsafe-boundary baseline measured below; isolated results UNMEASURED |

No LAN/Internet/DNS destination is contacted to fill a missing result. A future
offline test topology must be approved before those probes. Receipt output must
differentiate unavailable enforcement from a demonstrated denial and a passing
positive control. No skip/xfail/fake denial closes this gate.

## 3. Track B decision: immutable-while-live generation envelope, bounded purge

**Recommend a separately reviewed, additive fresh-synthetic `fp6_live` contract**
with package/isolation binding in the generation root, immutable for its whole
live lifetime, and narrowly authorized whole-generation erasure. Preserve the
original 6C-02 and PR #14 migrations/triggers/FKs and hashes byte-for-byte. The
old personal graph must be physically empty and remain unused. This is explicit
replacement of an unused storage contract, not a claim that the old immutable
rows became deletable. No legacy schema is dropped and no personal row is copied.

The present constraints are mutually incompatible with deleting populated PR #14
bindings unchanged: its trigger unconditionally raises 42501 on DELETE, its
reverse FK keeps generations bound, original observation DELETE is revoked, and
deletion_requests reference deletable source/collection rows. Keeping per-owner
bindings forever, relabeling duplicates, setting an `allow_delete` GUC, disabling
triggers/FKs or dropping a partition under privileged bypass are rejected.

| Alternative | Tradeoff / decision |
| --- | --- |
| Retain immutable generations forever | Reject: retains sensitive provenance/links and prevents required purge |
| Edit the existing DELETE trigger / grants / FKs in place | Reject under current instruction; changes the reviewed immutable contract and needs a separate supersession decision |
| Delete only encryption keys | At most defense in depth; not proof that tuples, WAL, backups or keys are gone; missing key deletion/coverage cannot justify completion |
| DROP/TRUNCATE partitions or privileged cascade | Reject as a bypass of deletion/owner/immutability controls |
| New empty-profile live contract + controlled purge | Recommended: explicit new lifecycle semantics and no historical backfill; larger DDL/test inventory and restricted to physically empty old storage |

If **any** old generation/binding/observation/collection/consent/control or pending
deletion/outbox/idempotency row exists, stop the fresh-profile migration. Do not
infer provenance, delete those rows or bypass old constraints. A nonempty
transition needs a new PO/SEC/DB-authorized design; this candidate does not solve
that transition by implication.

### B1. Exact proposed SQL and code changes

`blocker_proofs/lifecycle_proposal.sql` contains **unexecuted review SQL for the
kernel**, not an Alembic revision or a deployable complete migration. It makes
the root/binding and erasure-FK decisions reviewable. Remaining exact inventory
below must be completed and independently tested before registration of a new
migration. `CREATE TABLE LIKE` is not accepted as a proof of copied FKs/triggers/
RLS; compare explicit complete catalogs. [PostgreSQL CREATE TABLE](https://www.postgresql.org/docs/17/sql-createtable.html).

1. Add global `fp6_reference.isolation_profiles`: profile ID and exact non-null
   manifest/runtime/runner/filter digests, composite unique key, immutable
   UPDATE/DELETE/TRUNCATE triggers, FORCE RLS and runtime SELECT only. No seed is
   permitted until actual pins exist and are reviewed; none is invented here.
2. Add `fp6_live.controls` with owner FK, consent epoch/revision, lifecycle and
   monotonic generation high-water mark. Add `collections` with every original
   semantic/explanation-version CHECK unchanged, expiry and current pointer.
3. Add `fp6_live.generations` with owner/collection/generation PK, epoch/revision,
   server-issued execution ID and non-null exact package **and isolation** tuples.
   Immediate composite FKs reference both immutable global catalogs. There is no
   separate indelible per-owner binding table: a generation cannot exist without
   its complete binding, including zero findings. The current pointer's complete
   owner/collection/generation FK remains deferred for atomic creation/replacement.
4. Explicitly recreate the typed personal projections under `fp6_live`: consents,
   import_sources, observations, observation_features, context_evidence,
   excluded_rows, evidence_groups, evidence_equivalence, commercial_groups,
   commercial_alias_members, findings, finding_evidence, assessments,
   rationale_evidence, assessment_limitations, unknown_claims and user_actions.
   Retain all original enum/version/row/source/group/alias/domain/type/ownership
   constraints and lower-bound triggers, retargeting only reviewed new namespace
   dependencies. Duplicate support stays in equivalence membership, never a new
   corroboration role. Shared organizations/directory eligibility stays unchanged.
5. New `erasure_intents` retain typed pending targets but have **no FK back to
   deletable collections/sources/generations**. The owner/epoch/revision-scoped
   outbox references the intent, and bounded idempotency references control state.
   Exact proposed intent/outbox SQL is supplied. Final migration adds unique
   owner/epoch/idempotency key, operation + keyed request HMAC, same-input replay /
   different-input conflict, maximum one unfinished owner intent and outbox row.
   New requests coalesce safely or return bounded busy; never grow a hidden queue.
6. Runtime gets no DELETE/TRUNCATE on live immutable inputs/generations and no
   purger role membership. New NOLOGIN/NOBYPASSRLS `fp6_purger`, owned separately
   from `fp6_owner`, gets only reviewed new-table rights through its dedicated
   controller. It cannot DDL/disable triggers or touch other roles. All personal
   tables ENABLE/FORCE RLS with complete owner equality for runtime/purger. No
   footprint SECURITY DEFINER or unrestricted owner bypass is introduced.
   [PostgreSQL RLS](https://www.postgresql.org/docs/17/ddl-rowsecurity.html).
7. Generation INSERT trigger locks/checks owner context, active lifecycle or a
   current source-erasure intent for purger, exact epoch/revision and
   `generation=highwater+1`, then advances the counter transactionally. UPDATE
   always fails. DELETE requires purger role, owner equality, locked fenced state
   and matching pending intent. Source erasure cannot delete the newly current
   root. TRUNCATE always fails. The SQL supplies these core predicates.
8. Complete migration must additionally guard control/highwater and collection
   pointer updates against owner change, decreasing counters, stale consent/
   revision, unknown policy, expiry and incomplete execution/projection. Only
   the internal publisher/purger transition may advance the pointer after strict
   complete projection and kernel-execution matching; no client binding/result
   argument is authoritative. Provide active-current-generation read views and
   independent SQL/service denial tests before claiming this is enforced.
9. Auth/account cleanup needs a separately reviewed restricted auth eraser,
   session/auth-epoch fencing, and exact deletion order for identity_links,
   sessions and users. Do not widen runtime's original auth grants. Controls and
   acknowledged intents must be folded into detached minimal receipts before
   removing owner rows that still have FKs. Any old 6C-02 control row blocks this
   fresh-profile path. Actual auth/provider erasure is not implemented here.

The proposed owner GUC remains the original **trusted-server context**, not an
authentication credential. Arbitrary SQL that can choose someone else's context
is outside that assumption. New credentials, a purger/eraser trust boundary and
all role grants require SEC/DB review. Workers receive none of those credentials.

### B2. Transaction and journal ordering

| Boundary | Required state transition / failure behavior |
| --- | --- |
| T1 fence | Authenticate/authorize/CSRF; consistent owner `FOR UPDATE` lock; increment revision, increment consent epoch for withdrawal/expiry, disable account and revoke sessions for account deletion; durable intent + bounded outbox + unavailable reads commit together |
| Compute | Capture the fenced owner/epoch/revision/intent; derive survivors from active input; run accepted isolation profile and unchanged rules; failure leaves T1 fenced, pending and unreadable |
| T2 replacement | Reacquire same owner lock; recheck intent/epochs/revision/expiry/policy and execution tuple; insert bound new root and **all** typed projections, set pointer, remove every old derived/action/support row and old bound root, remove selected input/memberships, force constraints, commit atomically |
| Full scope | Collection/account/withdrawal/expiry removes all relevant generation/input/support/action rows and collection, with no empty live root retained; account auth cleanup also follows its separate reviewed inventory |
| Source becomes empty | Explicit source removal may leave one valid bound zero-finding generation and a zero-source collection; no fake finding/support/action is created |
| Acknowledgement | `live_data_removed` only after T2; independent journal receives a minimal intent event idempotently; `completed` only after durable matching sequence/coverage ack; outage never clears T1 or serves old data |
| Retry/late result | Bind operation, request HMAC, epoch/revision and immutable event; same request reuses receipt; stale epoch/revision/generation/worker nonce or different request fails; re-read committed owner control after lock, never trust cached state |

Use complete owner-scoped composite FKs throughout. Delete in dependency order:
actions/rationale links → finding evidence, limitations/unknowns/assessments →
findings → obsolete generation envelope; context/features/group memberships →
selected observations/excluded rows → sources; remove groups that cannot meet
their lower bounds. Repair stable duplicate primary and commercial memberships
from survivors before forcing deferred constraints. Never persist a half graph.
Other owners and shared reference catalogs are outside the mutation predicate.

The current generation's old payload must not remain as a history table after a
successful replacement. High-water control/restore tombstones prevent key/epoch
reuse; don't retain old findings or per-owner output hashes for that purpose.
Every writer and action mutation must lock/recheck the same owner control. Use
fresh read authorization around response release; long-lived repeatable-read
snapshots cannot be treated as post-fence authorization. Delivered bytes cannot
be recalled. [PostgreSQL row locks](https://www.postgresql.org/docs/17/explicit-locking.html).

### B3. Minimal retained receipt and retention

Propose detached, typed receipt fields only: random event ID, purpose-separated
keyed owner/target restore tokens, operation enum, consent epoch/revision/highwater,
journal sequence, key/version ID, bounded status, server time and approved expiry.
No FK to live data. No domain, timestamped source evidence, observation/finding/
action IDs, raw target UUID, input/output/content hash, package-to-owner lineage,
support, explanation prose or reconstructive payload is retained after final
control compaction. Global package/isolation catalogs may remain because they
contain build facts, not an owner join. Per-owner exact implementation lineage
ends when that generation is legitimately erased; while live it is immutable.

These keyed restore tokens are **pseudonymous**, not anonymous. They allow a
reviewed offline restore process to match covered old identities, not reconstruct
evidence. Independent journal durability, keys, backup/WAL/replica horizons and
high-water/coverage checks are design dependencies on future work, not a 6D
implementation here. No restoration may serve until reconciliation proves current
coverage and revokes restored sessions. An unreadable key, stale/missing journal
or lost outbox range means offline STOP, not best-effort resurrection.

Live tuple deletion is not secure erasure of PostgreSQL MVCC pages, WAL, old
snapshots, backups or storage media. PO/LEGAL/SEC/OPS must approve bounded cleanup
and copy/key retention, retry/escalation deadlines and legal holds. Missing policy
keeps writes disabled. Do not invent days or promise immediate physical erasure.
The narrow model's owner UUID/receipt state is explicitly a stand-in, **not this
accepted minimal receipt schema** or approved retention configuration.

### B4. Executable model and mandatory PostgreSQL proof

`uv run --frozen pytest -q blocker_tests` executes **19 ephemeral SQLite model
cases**: both source orders and an empty bound generation, four full-scope modes,
three injected rollback points, two stale-writer modes, two foreign targets, four
immutable binding-field updates, combined orphan/unbound/wrong-package rejection
and missing intent rejection. Rollback compares complete model snapshots; the
previously committed fence stays intact and other-owner rows remain unchanged.

This is neither PostgreSQL/RLS nor a complete typed adapter, auth/account eraser,
independent journal or concurrency proof. Account/withdrawal/expiry are modeled
operation labels only; actual auth and policy side effects remain untested.
The unchanged 71 + 152 original rule/package tests also passed locally (223),
including the immutable 70-profile/29 + six oracle evidence. That semantic result
is separate from model identity preservation; it does not establish a durable
duplicate/context projection.

Before acceptance require actual fresh PostgreSQL restricted-role tests:

- Every new table/column/PK/FK/CHECK/trigger/policy/grant catalog compared to the
  complete approved inventory; 434 baseline and 93 binding cases retained as
  historical/compatibility evidence, with new graph tests separately counted.
- Empty root with exact implementation/isolation tuple; NULL/foreign/mismatched
  tuples, wrong epoch/revision, reused generation, orphan support, invalid role
  and stale context fail; no generation can be published without complete binding.
- Both email/history source-removal orders with stable primary promotion, all
  duplicate alternatives and per-copy context, coincident nonduplicates,
  context-only source, commercial conflicts/unpaid, unresolved/empty results,
  action reset/eligibility, full support and seven unknowns against original oracles.
- Two real restricted logins; wrong owner/collection/generation/domain/type and
  purger attempts; missing/bogus intent, current-generation DELETE, direct UPDATE,
  TRUNCATE/CASCADE, role escalation and restore grants fail independently.
- Barrier-controlled save/delete, delete/delete, action/delete, withdrawal/save,
  expiry/retry and late-worker races in both acquisition orders, both isolation
  levels as appropriate; independent post-state and journal/outbox assertions.
- Actual backend termination before/after fence, row replacement, constraint
  checks, commit and ack; whole before/after catalog/data/ledger comparison. WAL/
  server-crash/PITR coverage remains a separate future proof, never inferred.

## 4. Migration, rollout and rollback strategy

1. First accept architecture/profile/role/retention decisions below. Keep original
   modules disabled and existing migrations unreachable from application code.
2. Build proof of the OS boundary on the approved isolated platform; freeze its
   new manifest only after all adversaries/parity/bounds pass. No worker can be
   admitted through the new path while any pin is unset.
3. Complete explicit `fp6_live` DDL and catalog guard in a new independent graph,
   on a **fresh disposable synthetic database** with recognized exact old revisions
   and a physical all-old-personal-tables-empty precondition. Owner-filtered counts
   are insufficient. Preserve old definitions and reject nonempty states atomically.
4. Run interrupted upgrade/constraint-fault tests plus old/new suites. Revoke all
   new runtime grants and remove new objects only in a verified empty disposable
   test graph. A nonempty downgrade is refused; rollback then disables new
   saves/reads, preserves fences/outbox/journal and uses reviewed forward repair.
5. Do not copy historical data, infer old execution identities, reopen old intake,
   erase journals, restore deleted generations or activate an endpoint. Production
   transition/hosting remains a separate approval and is outside this proposal.

## 5. Observed measurements and review evidence

Raw receipts are retained under `.local/phase6-blocker-resolution-20261127` and
committed hash/numeric summaries in `PHASE6-BLOCKER-RESOLUTION-RECEIPTS.json`.
The original failing sentinel assertion is unchanged. Native probe/benchmark and
unsupported-platform failures remain failures. New authoring/type/lint failures
are retained separately from final quality results; no old source was edited.

Current **network-unsafe supervisor** baseline, same original indexed worker,
four constructed 10,000-row fixtures; no new catalog admission:

| Fixture | Child s | Validation s | Total s | Reported RSS KiB | Input / output bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Account | .3660 | 1.2210 | 2.0526 | 79,960 | 3,359,465 / 4,882,129 |
| Commercial | .7371 | 1.0732 | 2.7850 | 90,776 | 4,289,466 / 5,012,331 |
| Unresolved | .7533 | .4164 | 2.5033 | 128,516 | 3,429,465 / 24,089,650 |
| Duplicates | .2810 | .8172 | 1.7596 | 74,128 | 3,609,456 / 4,702,348 |

RSS is the trusted worker's report, not a new aggregate-commit measurement.
These passing old-boundary samples cannot validate proposed isolated startup,
decode resource bounds, external egress denial or broad capacity. The isolated
candidate benchmark measured **zero workloads** after its startup STOP. Existing
historical timeout/login/native/performance failures remain open; no new passing
sample diagnoses them. Full local backend/frontend/browser/DB regression was not
rerun solely for these non-application proof additions; fresh CI is reported
separately with exact SHA and scoped failures.

## 6. Open decisions and minimal 6C-03 B–E resumption plan

| Decision | Required acceptance | Exact question / evidence still needed |
| --- | --- | --- |
| NET-PLATFORM | PO + SEC + OPS | Accept Linux offline worker as the initial supported profile, or require native Windows and a new successful native/broker/ACL design; no platform silently approved |
| NET-POLICY | SEC + OPS | Approve the complete combined isolation policy, exact image/runtime/kernel/launcher/filter pins, helper/controller budgets and cleanup/reaper design after adversarial proof |
| LIFE-CONTRACT | PO + DB + SEC | Accept the fresh-empty `fp6_live` replacement contract with immutable-while-live roots and audited purger authority; original populated PR14 transition remains explicitly unsupported |
| LIFE-BINDING | PO + DB + SEC | Accept inline generation package/isolation binding and loss of per-owner implementation linkage after legitimate erase; fixed indexed-r1 remains synthetic candidate only |
| LIFE-ROLES | SEC + DB | Approve limited new purger/auth eraser principals, trusted owner-context assumption, per-table rights and independently verified complete DDL; no implicit SECURITY DEFINER exception |
| LIFE-POLICY | PO + SEC + DB + OPS, with LEGAL | Approve minimal pseudonymous receipt/key/copy retention and expiry, deletion completion wording, retry/escalation bounds and no-write behavior when configuration is absent |

No names, approval, signatures, independent assessor or production-ready selection
are invented. Source/collection/FootPrint account deletion never implies a company
deleted its records; opening a link never verifies a privacy action.

After those decisions and their mandatory proof gates:

1. **6C-03 B1:** freeze the accepted new schema/isolation contract and executable
   pins; prove empty generations and strict execution-to-generation matching.
2. **6C-03 B2:** implement the lossless typed durable adapter in an offline test
   harness only: complete source/row/observation/duplicate/context/commercial/
   finding/evidence/assessment/rationale/limitation/unknown/action bijections,
   domain/type/version/support negatives and independent SQL projection checks.
3. **6C-03 C:** survivor projection through unchanged rules and exact oracles,
   both removal orders, primary/context/conflict/action support, atomic candidate
   publication and stale-result fencing. This establishes the 6C-03 contract;
   production deletion service/consent UI remains outside this task.
4. **6C-03 D:** complete actual supported-profile process/network/memory/decoder/
   timeout/cancellation/output/exit/cleanup matrix and benchmark all original
   fixtures under unchanged worker limits. Keep the old failing assertion until
   the actual accepted launcher passes the same denial invariant; retain the
   historical baseline receipt forever, with no expected-value reversal.
5. **6C-03 E:** investigate unresolved historical failures, run complete original
   backend/frontend/nine Chromium/DB/preservation/contracts/build/audit and new
   negative/resource/migration suites, then fresh exact-head push/PR CI and human
   acceptance. No passing limited job closes 6C-03.

**STOP. This proposal is submitted for review, with both blockers still OPEN.
Adoption, declaring either blocker resolved, 6C-03 dependent resumption,
6C-04/05/6D, real-user processing, invitations, merge and deployment remain STOP.**
