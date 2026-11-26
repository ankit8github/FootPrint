"""Executable startup benchmark gate; refuses to fabricate isolated capacity.

The native probe's in-memory SID does not create a profile or change policy.
Until that launch works and the complete private package runner is implemented,
no pinned-worker isolated-throughput number can be reported by this harness.
"""

import json
import subprocess
import sys
import time
from pathlib import Path


def main() -> None:
    begin = time.perf_counter()
    result = subprocess.run(
        [sys.executable, "-m", "blocker_proofs.windows_probe"],
        capture_output=True,
        timeout=12,
        check=False,
    )
    output = json.loads(result.stdout)
    report = {
        "scope": "candidate_startup_only_not_isolated_capacity",
        "startup_probe_seconds": round(time.perf_counter() - begin, 6),
        "probe": output,
        "native_probe_exit": result.returncode,
        "isolated_workloads_measured": 0,
        "limits": {
            "worker_seconds": 5,
            "aggregate_worker_commit_mib": 256,
            "input_mib": 8,
            "output_mib": 32,
        },
        "status": "STOP",
        "reason": "STARTUP_UNPROVEN"
        if result.returncode
        else "FULL_PACKAGE_RUNNER_NOT_IMPLEMENTED",
        "next_benchmark": [
            "70 profiles",
            "32 batches",
            "four 10000-row model fixtures",
            "all rejection/cleanup cases",
            "bounded decoder adversaries",
        ],
    }
    path = Path(__file__).resolve().parents[2] / ".local/phase6-blocker-resolution-20261127"
    path.mkdir(parents=True, exist_ok=True)
    target = path / f"candidate-benchmark-{time.time_ns()}.json"
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**report, "receipt": str(target)}))
    raise SystemExit(1)


if __name__ == "__main__":
    main()
