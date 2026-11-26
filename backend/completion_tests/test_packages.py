"""Historical/indexed implementation compatibility; immutable oracles are read-only."""

import copy
import hashlib
import json
import sys

import pytest
from pydantic import ValidationError

from experiments.admission_registry import DATA, SyntheticRegistry
from experiments.indexing_validation import IndexedBatch
from experiments.minimized_contract import MinimizedBatch
from experiments.session_store import Denied
from experiments.shared_executor import ExecutionRejected
from experiments.versioned_executor import digest, execute_catalog, package
from indexing_tests.test_indexing import MUTATIONS, invalid

REGISTRY = json.loads((DATA / "manifest.json").read_bytes())


@pytest.mark.skipif(sys.platform != "win32", reason="Windows kernel boundary required")
@pytest.mark.parametrize("profile", REGISTRY["profiles"], ids=lambda p: p["id"])
def test_versioned_profile(profile: dict[str, object]) -> None:
    raw = (DATA / (str(profile["digest"]) + ".json")).read_bytes()
    old, _ = execute_catalog(raw, "historical-v1")
    new, _ = execute_catalog(raw, "indexed-r1")
    assert old["result"] == new["result"]
    assert digest(new["result"]) == profile["assessment_sha256"]
    assert digest(new["result"]["discovery"]) == profile["discovery_sha256"]
    graph = new["result"]["discovery"]
    assert digest(
        {
            k: graph[k]
            for k in (
                "relationships",
                "relationship_evidence",
                "duplicate_groups",
                "conflicts",
                "unresolved",
            )
        }
    ) == digest(
        {
            k: old["result"]["discovery"][k]
            for k in (
                "relationships",
                "relationship_evidence",
                "duplicate_groups",
                "conflicts",
                "unresolved",
            )
        }
    )
    assert len(new["eligible_actions"]) == len(new["result"]["assessments"])
    for assessment in new["result"]["assessments"]:
        assert len(assessment["unknown_claims"]) == 7
        assert all(
            c["evidence_state"] == "unknown" and c["confidence"] == "insufficient"
            for c in assessment["unknown_claims"]
        )


@pytest.mark.parametrize("name", MUTATIONS)
def test_revision_validation_rejections(name: str) -> None:
    value = invalid(name)
    failures = []
    for model in (MinimizedBatch, IndexedBatch):
        with pytest.raises(ValidationError) as error:
            model.model_validate(copy.deepcopy(value))
        failures.append(error.value.errors(include_context=False, include_url=False))
    assert failures[0] == failures[1]


@pytest.mark.parametrize(
    "revision", ["", "indexed-r2", "../historical-v1", "relationship_fusion_v1"]
)
def test_unknown_revision_rejected(revision: str) -> None:
    with pytest.raises(ExecutionRejected, match="^PACKAGE_REJECTED$"):
        package(revision)


def test_historical_artifact_identity() -> None:
    artifact, expected = package("historical-v1")
    assert expected == "69fcc47c8b0890c488900b4afe875aa7ce19faa6e257a691ad371fd53edff064"
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == expected
    assert len(REGISTRY["profiles"]) == 70 and len(REGISTRY["entries"]) == 32
    # Exact original admission remains responsible for ordinary catalog intake.
    with pytest.raises(Denied) as error:
        SyntheticRegistry().admit(
            IndexedBatch.model_validate_json(
                (DATA / (REGISTRY["entries"][0]["digest"] + ".json")).read_bytes()
            )
        )
    assert error.value.status == 422
