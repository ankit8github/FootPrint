"""Seed bijection evidence only; not durable adapter/survivor acceptance."""

import json
from dataclasses import replace
from uuid import UUID, uuid4

import pytest

from experiments.admission_registry import DATA
from experiments.provenance_adapter import ProvenanceRejected, Scope, seed_catalog, validate_seed

REGISTRY = json.loads((DATA / "manifest.json").read_bytes())


@pytest.mark.parametrize("entry", REGISTRY["entries"], ids=lambda entry: entry["digest"][:8])
def test_catalog_seed_complete(entry: dict[str, object]) -> None:
    raw = (DATA / (str(entry["digest"]) + ".json")).read_bytes()
    scope = Scope(uuid4(), uuid4(), 1)
    first, second = seed_catalog(raw, scope), seed_catalog(raw, scope)
    model = validate_seed(first, scope)
    assert json.loads(first.raw) == model.model_dump()
    assert len(first.bindings) == (
        len(model.sources)
        + len(model.observations)
        + len(model.excluded)
        + len(model.duplicate_groups)
        + len(model.commercial_groups)
    )
    assert {binding.identity for binding in first.bindings}.isdisjoint(
        binding.identity for binding in second.bindings
    )
    # The entire input, including per-copy context and every duplicate member,
    # remains available. No value-based identity equivalence is introduced.
    assert json.loads(first.raw)["contexts"] == json.loads(raw)["contexts"]
    assert json.loads(first.raw)["duplicate_groups"] == json.loads(raw)["duplicate_groups"]


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "extra",
        "repeat",
        "kind",
        "local",
        "owner",
        "collection",
        "generation",
        "nil",
        "payload",
        "digest",
    ],
)
def test_seed_reference_damage_denied(damage: str) -> None:
    scope = Scope(uuid4(), uuid4(), 1)
    raw = (DATA / (REGISTRY["entries"][0]["digest"] + ".json")).read_bytes()
    seed = seed_catalog(raw, scope)
    first = seed.bindings[0]
    if damage == "missing":
        seed = replace(seed, bindings=seed.bindings[1:])
    elif damage == "extra":
        seed = replace(seed, bindings=seed.bindings + (first,))
    elif damage == "repeat":
        seed = replace(
            seed,
            bindings=(
                first,
                replace(seed.bindings[1], identity=first.identity),
                *seed.bindings[2:],
            ),
        )
    elif damage == "kind":
        seed = replace(seed, bindings=(replace(first, kind="observation"), *seed.bindings[1:]))
    elif damage == "local":
        seed = replace(seed, bindings=(replace(first, local="foreign"), *seed.bindings[1:]))
    elif damage in {"owner", "collection", "generation"}:
        altered = {
            "owner": replace(scope, owner=uuid4()),
            "collection": replace(scope, collection=uuid4()),
            "generation": replace(scope, generation=2),
        }[damage]
        seed = replace(seed, bindings=(replace(first, scope=altered), *seed.bindings[1:]))
    elif damage == "nil":
        seed = replace(seed, bindings=(replace(first, identity=UUID(int=0)), *seed.bindings[1:]))
    elif damage == "payload":
        seed = replace(seed, raw=b"{}")
    else:
        seed = replace(seed, origin_digest="0" * 64)
    with pytest.raises(ProvenanceRejected, match="^PROVENANCE_REJECTED$"):
        validate_seed(seed, scope)


def test_wrong_expected_scope_denied() -> None:
    scope = Scope(uuid4(), uuid4(), 1)
    raw = (DATA / (REGISTRY["entries"][0]["digest"] + ".json")).read_bytes()
    seed = seed_catalog(raw, scope)
    for changed in (
        replace(scope, owner=uuid4()),
        replace(scope, collection=uuid4()),
        replace(scope, generation=2),
    ):
        with pytest.raises(ProvenanceRejected):
            validate_seed(seed, changed)
