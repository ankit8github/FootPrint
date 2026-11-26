# Independent executor acceptance — network gate failed

Recorded 2026-11-27 (Asia/Calcutta). Base:
`511dfee080d3bcd3c68aaa35ec1474700ff0cf63`, new branch
`verify/phase6-executor-safety`. **6C-03 D remains incomplete.** No runtime,
admission, package, oracle, SQL, protected hash or resource limit is changed.

The added tests call the existing private `versioned_executor._supervise` with
fixed synthetic test artifacts and real local child processes. They do not
enroll these artifacts in the package registry, bypass catalog admission in an
application, run an adapter, create a saved-data route or publish a generation.
Each test artifact waits for stdin before work, except the explicit blocked-input
cleanup case. All test-created root processes must have exited at teardown.

## Finding C03-NET-01 — no OS network denial

The child can import `node:net` and connect to a listener bound exclusively to
`127.0.0.1` on an ephemeral port under the actual unchanged Node 22.15.0 command.
The listener received `FP6_SYNTHETIC_PROBE`; the child returned `connected=true`.
The strict acceptance assertion requires `connected=false` and fails. No external
address, genuine credential, real data, DNS lookup or production endpoint is used.

This demonstrates missing enforcement for the tested process boundary. It does
not demonstrate a malicious catalog rule, a reachable production vulnerability,
external Internet reachability or cross-tenant compromise. The original pinned
worker remains trusted and has no network operation added. The design nonetheless
requires an isolated no-network executor, so this is a release-blocking security
requirement failure. Do not infer OS isolation from Node capability flags.

Remediation needs a reviewed OS isolation design, not a test waiver, changed
expected value, mocked socket error, firewall change to the user's host, larger
resource limit or relabeling this test as passed. Application adoption and
dependent persistence/deletion implementation remain stopped.

## Actual local acceptance matrix

Final functional candidate: **38 passed / one failed / zero skipped**, 20.21 s.
Raw log SHA-256:
`78f7493f21d8b84ca38764854dbe4d0ef719fa2aedfce0238e206f181fcf8d42`.
The subsequent formatting-only change does not establish a new execution result;
fresh exact-head CI must execute the committed source independently.

| Acceptance check | Executed cases | Result / scope |
| --- | ---: | --- |
| Exact fixed limits | 1 | 5 s / 256 MiB / 8 MiB input / 32 MiB output unchanged |
| Unsupported platform | 1 | Simulated Linux platform refuses before file read/launch; not actual Linux isolation proof |
| Prelaunch guards | 1 | Oversize input, pre-cancel and artifact mismatch; no child launched |
| Empty result / exact input cap | 2 | Empty result accepted at supervisor-envelope level; no claim of a valid durable generation |
| Malformed/truncated/multiple/duplicate/nonfinite JSON and types | 14 | Rejected; no successful return |
| Invalid reported memory, including bool/float | 5 | Rejected; untrusted peak reports are not OS measurements |
| Unexpected exit after complete or partial output | 2 | Nonzero exit rejected before output return |
| Deadline after complete output | 1 | Rejected; root exited; about 5.02 s supervisor wall locally |
| In-flight cancellation | 1 | Rejected; root exited; about .44 s locally |
| Exact stdout cap / cap + 1 | 2 | Exact valid envelope accepted; one byte over rejected, no truncation |
| Exact diagnostics cap / cap + 1 | 2 | 8192 accepted / 8193 rejected |
| Actual touched-buffer memory exhaustion | 1 | Child exited nonzero, no successful return; per-process Job Object limit unchanged |
| Node spawn/file/worker permissions | 3 | All return ERR_ACCESS_DENIED; not a malicious-code sandbox claim |
| No-network gate | 1 | **FAIL**; loopback transmission observed |
| Blocked stdin writer | 1 | Deadline and cleanup; about 5.06 s locally |
| Kernel descendant cleanup | 1 | Real Python root/descendant in inherited Job Object; both terminated on close |

The descendant check is separate from the supervisor's restricted Node launcher;
it does not grant Node spawn permission or claim hostile breakaway coverage.
Its Python root and inherited descendant receive only SystemRoot, WINDIR and
PATH, matching the supervisor's minimal environment rather than inheriting the
operator's arbitrary environment. No application or auth secret is supplied.
Unsupported native modules, job-assignment races, active hostile breakaway,
aggregate descendant committed-memory limits, independent parent memory/JSON
parse CPU bounds and external network denial remain unproven. The existing job
sets PROCESS_MEMORY and KILL_ON_JOB_CLOSE, not a job-wide aggregate memory cap.
No independent security certification or production portability claim follows.

First test-authoring run: 34 passed / four failed. Two tests expected the wrong
fixed rejection category for bool/float memory reports, and the filesystem probe
did not await its Promise. Correcting those new tests retained strict rejection
and made the real permission check observable; the network assertion was never
changed. Second run: 38 passed / one failed, 16.68 s. Initial lint/type/format
errors and all raw test failures remain in `.local/phase6-master-20261127`.
No original assertion, source or exception was weakened. No xfail,
continue-on-error or failure-filtering workflow is added.

## CI and rollback

An additive Windows workflow executes the entire acceptance suite, including the
failing mandatory network test, and always uploads JUnit evidence. Existing
workflows remain byte-identical. A red result is the correct current gate state;
green original workflows cannot override it. Exact-head outcomes/links are added
to the master/final reports and draft metadata after observation.

Rollback is leaving this verification-only draft unmerged. There are no new
application writes, migrations, consent changes or deletion-journal operations
to undo. PR #13 and PR #14 remain draft/open/unmerged and unchanged.
