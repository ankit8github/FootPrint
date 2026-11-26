# Architecture probes, not application code

See `docs/PHASE6-BLOCKER-RESOLUTION-PLAN.md` for the proposed contracts and gates.
No module here is imported by the application or an existing migration/executor.
All inputs/identities are synthetic. Original assertions/oracles remain unchanged.

From `backend`:

- `uv run --frozen pytest -q blocker_tests`: 19 ephemeral SQLite model cases;
  no PostgreSQL/RLS, real account erasure or independent journal proof.
- `python -m blocker_proofs.windows_probe`: actual creation-time AppContainer /
  Job Object probe with a loopback-only receiver. No profile/ACL/firewall changes.
  A failed launch returns failure, never a passing no-network claim.
- `python -m blocker_proofs.linux_network_probe`: x86-64 Linux-only, per-child
  syscall-filter building block with a local positive control and eight socket
  refusal cases. No full Node sandbox, namespace, cgroup or capacity claim.
- `uv run --frozen python -m blocker_proofs.benchmark_candidate`: currently stops
  if native startup is unavailable and reports zero isolated capacity samples.
  Even a passing native probe does not supply the absent full package runner.
- `uv run --frozen python -m scripts.benchmark_rule_packages`: unchanged current
  network-unsafe baseline, four model fixtures, not an isolated-candidate result.

`lifecycle_proposal.sql` is incomplete, unexecuted kernel review text, outside all
migration discovery. No privileges, schema or runtime policy are installed.
`isolation-profile-proposal.json` has null, unapproved pins and is disabled review
data; it must never be loaded as an executable production policy.
