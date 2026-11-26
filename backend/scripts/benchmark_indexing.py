"""Fixed-size paired experiment; saves every receipt and stops on any failure."""

import argparse
import json
import platform
import sys
import uuid
from typing import Any

from experiments.admission_registry import DATA
from experiments.shared_executor import DEADLINE, MAX_OUTPUT, MEMORY, ROOT
from scripts.benchmark_shared_rules import fixture
from scripts.measure_indexing import measure


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("all", "indexed-full"), default="all")
    args = parser.parse_args()
    output = ROOT / (".local/phase6c03-indexing-" + uuid.uuid4().hex)
    output.mkdir()
    records: list[dict[str, Any]] = []
    receipt: dict[str, Any] = {
        "reviewed_head": "233620a10abbb6f53b773b853bd41900c62b8b61",
        "platform": platform.platform(),
        "python": sys.version,
        "limits": {
            "child_seconds": DEADLINE,
            "committed_memory_bytes": MEMORY,
            "input_bytes": 8 * 1024 * 1024,
            "output_bytes": MAX_OUTPUT,
        },
        "mode": args.mode,
        "runs": records,
        "artifacts": {
            v: json.loads(
                (ROOT / f".local/phase6c03-indexing-build/{v}/provenance.json").read_bytes()
            )
            for v in ("baseline", "indexed")
        },
    }
    print("Evidence:", output, flush=True)
    expected_hashes: dict[str, tuple[str, str, str]] = {}

    def run(label: str, raw: bytes, variant: str, expected: dict[str, Any] | None = None) -> None:
        row = {"label": label, **measure(raw, variant)}
        key = row["input_sha256"]
        hashes = tuple(row[k] for k in ("result_sha256", "discovery_sha256", "support_sha256"))
        if row["status"] == "PASS":
            if key in expected_hashes and hashes != expected_hashes[key]:
                row["status"] = "SEMANTIC_MISMATCH"
            if expected is not None and (
                hashes[0] != expected["assessment_sha256"]
                or hashes[1] != expected["discovery_sha256"]
            ):
                row["status"] = "SEMANTIC_MISMATCH"
            expected_hashes[key] = hashes
        records.append(row)
        (output / "measurements.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(
            json.dumps(
                {
                    k: row[k]
                    for k in (
                        "label",
                        "variant",
                        "status",
                        "validation_seconds_outside_child_budget",
                        "child_wall_seconds_including_launch_and_kill",
                        "supervisor_wall_seconds",
                        "peak_rss_kib",
                        "input_bytes",
                        "full_output_bytes",
                    )
                }
            ),
            flush=True,
        )
        if row["status"] != "PASS":
            raise SystemExit("STOP: " + row["status"])

    if args.mode == "all":
        registry = json.loads((DATA / "manifest.json").read_bytes())
        for entry in registry["entries"]:
            raw = (DATA / (entry["digest"] + ".json")).read_bytes()
            expected = next(p for p in registry["profiles"] if p["digest"] == entry["digest"])
            for variant in ("baseline", "indexed"):
                run("catalog-" + entry["digest"][:8], raw, variant, expected)
        for count in (20, 1000, 4000):
            for kind in ("primary_account", "commercial_distinct", "unresolved", "duplicates"):
                raw = fixture(kind, count)
                for repeat in range(2):
                    # Alternate order to expose, rather than conceal, startup/load noise.
                    for variant in (
                        ("baseline", "indexed") if repeat == 0 else ("indexed", "baseline")
                    ):
                        run(f"{kind}-{count}-r{repeat + 1}", raw, variant)
    # Indexed capacity is measured before the known failing baseline. A new failure
    # stops immediately. No subsequent benchmark is run after any failed child.
    for kind in ("primary_account", "unresolved", "duplicates", "commercial_distinct"):
        run(kind + "-10000", fixture(kind), "indexed")
    if args.mode == "all":
        for kind in ("primary_account", "unresolved", "duplicates", "commercial_distinct"):
            run(kind + "-10000", fixture(kind), "baseline")


if __name__ == "__main__":
    main()
