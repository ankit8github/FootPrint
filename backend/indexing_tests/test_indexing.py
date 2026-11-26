"""Bounded differential evidence; never changes immutable expected results."""

import ast
import copy
import inspect
import json
import os
import shutil
import subprocess
import sys
import time
from typing import Any

import pytest
from pydantic import ValidationError

from experiments.admission_registry import DATA, SyntheticRegistry
from experiments.indexing_validation import IndexedBatch
from experiments.minimized_contract import MinimizedBatch, canonical
from experiments.session_store import Denied
from experiments.shared_executor import DEADLINE, ROOT, _windows_job
from scripts.benchmark_shared_rules import fixture
from scripts.measure_indexing import measure

REGISTRY = json.loads((DATA / "manifest.json").read_bytes())


def test_only_reference_lookup_changed() -> None:
    def reference(model: type[MinimizedBatch]) -> ast.FunctionDef:
        definition = ast.parse(inspect.getsource(model)).body[0]
        assert isinstance(definition, ast.ClassDef)
        return next(
            node
            for node in definition.body
            if isinstance(node, ast.FunctionDef) and node.name == "references"
        )

    a, b = reference(MinimizedBatch), reference(IndexedBatch)
    index = next(
        i
        for i, node in enumerate(b.body)
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "alias_members"
    )
    assert isinstance(b.body[index + 1], ast.For)
    del b.body[index : index + 2]
    original_loop, indexed_loop = a.body[-2], b.body[-2]
    assert isinstance(original_loop, ast.For) and isinstance(indexed_loop, ast.For)
    indexed_loop.body[0] = original_loop.body[0]
    assert ast.dump(b) == ast.dump(a)


@pytest.mark.parametrize("change", ("none", "reverse_members", "foreign_domain"))
def test_ordered_alias_membership(change: str) -> None:
    value = json.loads(fixture("commercial_distinct", 20))
    for observation in value["observations"]:
        observation["order_keys"] = ["order0001"]
    value["commercial_groups"] = [
        {
            "alias": "order0001",
            "domain": "fictional-shop.test",
            "members": [o["id"] for o in value["observations"]],
        }
    ]
    if change == "reverse_members":
        value["commercial_groups"][0]["members"].reverse()
    if change == "foreign_domain":
        value["observations"][1]["domain"] = "fictional-studio.test"
    if change == "none":
        assert canonical(IndexedBatch.model_validate(value)) == canonical(
            MinimizedBatch.model_validate(value)
        )
    else:
        outcomes = []
        for model in (MinimizedBatch, IndexedBatch):
            with pytest.raises(ValidationError) as error:
                model.model_validate(copy.deepcopy(value))
            outcomes.append(error.value.errors(include_context=False, include_url=False))
        assert outcomes[0] == outcomes[1]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows kernel limits required")
@pytest.mark.parametrize("profile", REGISTRY["profiles"], ids=lambda p: p["id"])
def test_immutable_profile(profile: dict[str, Any]) -> None:
    raw = (DATA / (profile["digest"] + ".json")).read_bytes()
    original = MinimizedBatch.model_validate_json(raw)
    indexed = IndexedBatch.model_validate_json(raw)
    assert canonical(indexed) == canonical(original)
    result = measure(raw)
    assert result["status"] == "PASS"
    assert result["result_sha256"] == profile["assessment_sha256"]
    assert result["discovery_sha256"] == profile["discovery_sha256"]
    assert result["support_sha256"] is not None


MUTATIONS = (
    "version",
    "extra",
    "missing_source",
    "source_order",
    "source_duplicate",
    "source_adapter",
    "source_budget",
    "source_count",
    "missing_row",
    "duplicate_row",
    "row_id",
    "row_index",
    "foreign_source",
    "negative_index",
    "foreign_domain",
    "foreign_alias_domain",
    "alias_order",
    "alias_missing",
    "alias_extra",
    "member_missing",
    "member_duplicate",
    "member_foreign",
    "alias_duplicate",
    "feature_duplicate",
    "context_missing",
    "context_ineligible",
    "context_duplicate",
    "duplicate_missing",
    "duplicate_group_repeated",
    "timestamp",
    "timestamp_state",
    "duplicate_alias_key",
)


def invalid(name: str) -> dict[str, Any]:
    value: dict[str, Any] = json.loads(fixture("commercial_distinct", 20))
    o, group = value["observations"][0], value["commercial_groups"][0]
    if name == "version":
        value["schema_version"] = "bad"
    elif name == "extra":
        value["assessment_truth"] = []
    elif name == "missing_source":
        value["sources"].pop()
    elif name == "source_order":
        value["sources"].reverse()
    elif name == "source_duplicate":
        value["sources"][1] = copy.deepcopy(value["sources"][0])
    elif name == "source_adapter":
        value["sources"][0]["adapter"] = "browser_chrome_json_v1"
    elif name == "source_budget":
        value["sources"][0]["record_count"] = 10_000
    elif name == "source_count":
        value["sources"][0]["record_count"] = 0
    elif name == "missing_row":
        value["observations"].pop()
    elif name == "duplicate_row":
        value["observations"].append(copy.deepcopy(o))
    elif name == "row_id":
        o["id"] = "s0001:r00001"
    elif name == "row_index":
        o["record_index"] = 1
    elif name == "foreign_source":
        o["source_id"] = "s9999"
    elif name == "negative_index":
        o["record_index"] = -1
    elif name == "foreign_domain":
        o["domain"] = "example.com"
    elif name == "foreign_alias_domain":
        group["domain"] = "fictional-studio.test"
    elif name == "alias_order":
        value["commercial_groups"].reverse()
    elif name == "alias_missing":
        value["commercial_groups"].pop()
    elif name == "alias_extra":
        value["commercial_groups"].append(copy.deepcopy(group))
    elif name == "member_missing":
        group["members"] = []
    elif name == "member_duplicate":
        group["members"].append(o["id"])
    elif name == "member_foreign":
        group["members"] = ["s9999:r00000"]
    elif name == "alias_duplicate":
        value["commercial_groups"][1]["alias"] = group["alias"]
    elif name == "feature_duplicate":
        o["features"].append(o["features"][0])
    elif name.startswith("context_"):
        c = {"observation_id": o["id"], "features": ["CLINIC_APPOINTMENT_PORTAL_CONTEXT"]}
        if name == "context_missing":
            c["observation_id"] = "s9999:r00000"
        value["contexts"] = [c, copy.deepcopy(c)] if name == "context_duplicate" else [c]
    elif name == "duplicate_missing":
        o["duplicate_of"] = "s9999:r00000"
    elif name == "duplicate_group_repeated":
        value["duplicate_groups"] = [[o["id"], o["id"]]]
    elif name == "timestamp":
        o["occurred_at"] = "bad"
    elif name == "timestamp_state":
        o["time_status"] = "invalid"
    elif name == "duplicate_alias_key":
        o["order_keys"].append(o["order_keys"][0])
    else:
        raise AssertionError(name)
    return value


@pytest.mark.parametrize("name", MUTATIONS)
def test_validation_rejections(name: str) -> None:
    value = invalid(name)
    outcomes = []
    for model in (MinimizedBatch, IndexedBatch):
        with pytest.raises(ValidationError) as error:
            model.model_validate(copy.deepcopy(value))
        outcomes.append(error.value.errors(include_context=False, include_url=False))
    assert outcomes[0] == outcomes[1]


def test_catalog_boundary_not_replaced() -> None:
    # Subclass is explicitly NOT an ordinary admitted contract type.
    raw = (DATA / (REGISTRY["entries"][0]["digest"] + ".json")).read_bytes()
    with pytest.raises(Denied) as error:
        SyntheticRegistry().admit(IndexedBatch.model_validate_json(raw))
    assert error.value.status == 422


@pytest.mark.skipif(sys.platform != "win32", reason="Windows kernel limits required")
def test_pure_negative_and_multiplicity_cases() -> None:
    node = shutil.which("node")
    assert node is not None
    script = ROOT / "frontend/scripts/shared-rules/test-indexing.mjs"
    artifacts = ROOT / ".local/phase6c03-indexing-build"
    begin = time.perf_counter()
    process = subprocess.Popen(
        [
            node,
            "--no-warnings",
            "--experimental-permission",
            f"--allow-fs-read={script}",
            f"--allow-fs-read={artifacts / 'baseline/pure.mjs'}",
            f"--allow-fs-read={artifacts / 'indexed/pure.mjs'}",
            str(script),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={k: os.environ[k] for k in ("SystemRoot", "WINDIR", "PATH") if k in os.environ},
    )
    job = _windows_job(process)
    try:
        output, errors = process.communicate(
            timeout=max(0.001, DEADLINE - (time.perf_counter() - begin))
        )
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        job[0].CloseHandle(job[1])
    assert process.returncode == 0, errors.decode()
    assert len(output) < 32 * 1024 * 1024
    result = json.loads(output)
    assert result["passed"] == 44
    print(json.dumps(result))
