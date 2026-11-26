"""Counterexample to claiming durable package provenance in the current schema."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_generation_does_not_store_implementation_identity() -> None:
    sql = (ROOT / "backend/tenant_migrations/versions/6c02_0001.sql").read_text()
    definition = re.search(r"CREATE TABLE fp6_data.generations \((.*?)\n\);", sql, re.S)
    assert definition is not None
    body = definition.group(1)
    assert "owner_id uuid NOT NULL, collection_id uuid NOT NULL" in body
    assert "generation integer NOT NULL" in body
    assert not any(
        name in body for name in ("implementation", "artifact", "package", "json", "metadata")
    )
    collection = re.search(r"CREATE TABLE fp6_data.collections \((.*?)\n\);", sql, re.S)
    assert collection is not None
    assert "fusion_version = 'relationship_fusion_v1'" in collection.group(1)
    assert "assessment_version = 'sensitivity_rules_v1'" in collection.group(1)
    manifest = json.loads((ROOT / "backend/experiments/rule_packages/manifest.json").read_bytes())
    old, new = (manifest["packages"][key] for key in ("historical-v1", "indexed-r1"))
    assert old["worker_sha256"] != new["worker_sha256"]
    assert new["equivalent_to"] == "historical-v1"

    # Both select the same semantic wire versions. Projecting either execution
    # into the existing collection/generation columns yields identical rows,
    # even though its implementation identity differs. Empty generations have
    # no derived finding UUID in which that missing metadata could be hidden.
    def existing_rows(revision: str) -> tuple[object, ...]:
        assert revision in manifest["packages"]
        return (
            "synthetic-owner",
            "synthetic-collection",
            1,
            tuple(sorted(manifest["semantic_versions"].items())),
        )

    assert existing_rows("historical-v1") == existing_rows("indexed-r1")
    decision = json.loads(
        (ROOT / "backend/experiments/rule_packages/storage-compatibility.json").read_bytes()
    )
    assert decision["status"] == "STOP"
    assert decision["lossless_existing_typed_target"] is None
    assert decision["durable_projection_enabled"] is False
