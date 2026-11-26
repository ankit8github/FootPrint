"""Four fixed model-only measurements of the stopped indexed revision."""

import json
from pathlib import Path
from uuid import uuid4

from experiments.shared_executor import ExecutionRejected
from experiments.versioned_executor import benchmark_only
from scripts.benchmark_shared_rules import fixture


def main() -> None:
    output = (
        Path(__file__).resolve().parents[2]
        / ".local"
        / ("phase6c03-package-benchmark-" + uuid4().hex)
    )
    output.mkdir()
    rows: list[dict[str, object]] = []
    for kind in ("primary_account", "commercial_distinct", "unresolved", "duplicates"):
        try:
            row: dict[str, object] = {
                "fixture": kind,
                "rows": 10_000,
                "status": "PASS",
                **benchmark_only(fixture(kind)),
            }
        except ExecutionRejected as error:
            row = {"fixture": kind, "rows": 10_000, "status": "STOP", "reason": str(error)}
        rows.append(row)
        (output / "measurements.json").write_text(
            json.dumps(
                {
                    "implementation": "indexed-r1",
                    "phase_status": "STOPPED at C03-COMP-01; no adoption approval",
                    "model_only_not_catalog": True,
                    "limits": {
                        "child_seconds": 5,
                        "commit_mib": 256,
                        "input_mib": 8,
                        "output_mib": 32,
                    },
                    "rows": rows,
                },
                indent=2,
            )
            + "\n"
        )
        print(json.dumps(row), flush=True)
        if row["status"] != "PASS":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
