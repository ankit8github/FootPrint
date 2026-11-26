"""Bounded, constructed minimized fixtures. Not admission catalog entries."""

import json
import platform
from pathlib import Path
from typing import Any

from experiments.shared_executor import ExecutionRejected, benchmark_only


def fixture(kind: str, count: int = 10_000) -> bytes:
    sources = [
        {"source_id": f"s{i + 1:04}", "adapter": "email_eml_v1", "record_count": count // 20}
        for i in range(20)
    ]
    observations: list[dict[str, Any]] = []
    groups = []
    for i in range(count):
        source = sources[i // (count // 20)]
        identifier = f"{source['source_id']}:r{i % (count // 20):05}"
        unresolved = kind == "unresolved"
        commercial = kind == "commercial_distinct"
        observations.append(
            {
                "id": identifier,
                "source_id": source["source_id"],
                "record_index": i % (count // 20),
                "adapter": "email_eml_v1",
                "kind": "unclassified_observation"
                if unresolved
                else "transaction_email_detected"
                if commercial
                else "registration_email_detected",
                "domain": None if unresolved else "fictional-shop.test",
                "occurred_at": "2026-10-17T12:00:00.000Z",
                "time_status": "valid",
                "attribution": "unverified_sender",
                "features": ["UNTRUSTED_INSTRUCTIONS"]
                if unresolved
                else ["PAID_RECEIPT_CLAIM"]
                if commercial
                else ["ACCOUNT_REQUEST"],
                "order_keys": [f"order{i + 1:04}"] if commercial else [],
                "duplicate_of": observations[0]["id"] if kind == "duplicates" and i else None,
                "issue_code": "UNTRUSTED_INSTRUCTIONS" if unresolved else None,
            }
        )
        if commercial:
            groups.append(
                {
                    "alias": f"order{i + 1:04}",
                    "domain": "fictional-shop.test",
                    "members": [identifier],
                }
            )
    batch = {
        "schema_version": "minimized-evidence-v1",
        "parser_version": "phase2-normalized-v1",
        "feature_version": "email_features_v1",
        "fusion_version": "relationship_fusion_v1",
        "context_version": "email_context_v1",
        "assessment_version": "sensitivity_rules_v1",
        "sources": sources,
        "observations": observations,
        "excluded": [],
        "contexts": [],
        "commercial_groups": groups,
        "duplicate_groups": [[o["id"] for o in observations]] if kind == "duplicates" else [],
    }
    return json.dumps(batch, separators=(",", ":")).encode()


def main() -> None:
    results: list[dict[str, object]] = []
    output = Path(__file__).resolve().parents[2] / ".local/phase6c03-validation"
    output.mkdir(parents=True, exist_ok=True)
    for kind in ("primary_account", "commercial_distinct", "unresolved", "duplicates"):
        try:
            metrics = benchmark_only(fixture(kind))
            result: dict[str, object] = {
                "fixture": kind,
                "rows": 10_000,
                "status": "PASS",
                **metrics,
            }
        except ExecutionRejected as error:
            result = {"fixture": kind, "rows": 10_000, "status": "STOP", "reason": str(error)}
        results.append(result)
        receipt = {
            "platform": platform.platform(),
            "limits": {"seconds": 5, "memory_mib": 256, "input_mib": 8, "output_mib": 32},
            "results": results,
        }
        (output / "benchmark.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps(result), flush=True)
        if result["status"] != "PASS":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
