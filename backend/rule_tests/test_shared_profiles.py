"""Evidence for the stopped prototype, not adapter or lifecycle acceptance."""

import hashlib
import json
import sys

import pytest

from experiments.admission_registry import DATA
from experiments.minimized_contract import MAX_BODY, MinimizedBatch
from experiments.shared_executor import ExecutionRejected, _supervise, execute

REGISTRY = json.loads((DATA / "manifest.json").read_bytes())


@pytest.mark.skipif(sys.platform != "win32", reason="Kernel resource enforcement NOT TESTED here")
@pytest.mark.parametrize("profile", REGISTRY["profiles"], ids=lambda p: p["id"])
def test_exact_immutable_profile(profile: dict[str, object]) -> None:
    batch = MinimizedBatch.model_validate_json(
        (DATA / (str(profile["digest"]) + ".json")).read_bytes()
    )
    result, metrics = execute(batch)
    discovery = json.dumps(
        result["discovery"], sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()
    assert hashlib.sha256(discovery).hexdigest() == profile["discovery_sha256"]
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    assert hashlib.sha256(encoded).hexdigest() == profile["assessment_sha256"]
    for assessment in result["assessments"]:
        assert len(assessment["unknown_claims"]) == 7
        assert all(
            c["evidence_state"] == "unknown" and c["confidence"] == "insufficient"
            for c in assessment["unknown_claims"]
        )
    assert metrics["input_bytes"] <= MAX_BODY
    assert metrics["output_bytes"] <= 32 * 1024 * 1024
    assert metrics["peak_rss_kib"] <= 256 * 1024
    assert metrics["seconds"] < 5


def test_oversize_rejected_before_launch() -> None:
    with pytest.raises(ExecutionRejected, match="^INPUT_LIMIT$"):
        _supervise(b" " * (MAX_BODY + 1))
