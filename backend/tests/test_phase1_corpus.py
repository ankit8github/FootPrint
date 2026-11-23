"""Tests of the authored oracle and its integrity checks, never a product pipeline."""

import json
import shutil
import socket
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_corpus import DEFAULT_ROOT, REQUIRED_COVERAGE, Manifest, metrics, validate


@pytest.fixture(scope="module")
def corpus() -> Manifest:
    return validate()


@pytest.fixture
def copy_corpus(tmp_path: Path) -> Path:
    target = tmp_path / "v1"
    shutil.copytree(DEFAULT_ROOT, target)
    return target


def read_manifest(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    return result


def save_manifest(root: Path, data: dict[str, Any]) -> None:
    (root / "manifest.json").write_text(json.dumps(data), encoding="utf-8")


def test_corpus_inventory_coverage_and_committed_metrics(corpus: Manifest) -> None:
    summary = metrics(corpus)
    assert summary["source_files"] == 27
    assert summary["source_events"] == 48
    assert summary["scenarios"] == 29
    assert summary["deletion_snapshots"] == 6
    assert set(summary["coverage"]) == REQUIRED_COVERAGE
    assert all(summary["coverage"].values())
    assert summary == json.loads((DEFAULT_ROOT / "metrics.json").read_text())
    assert summary["discovery_precision"] is summary["discovery_recall"] is None
    assert summary["sensitivity_agreement"] is None
    assert corpus.review_status == "product-owner-approved, AI-assisted baseline"
    assert corpus.approval.independent_blind_human_review is False
    assert summary["independent_review"] == "not_performed"
    assert corpus.independent_reviewer is None


@pytest.mark.parametrize(
    ("case_id", "expected"),
    [
        ("c01", [("visited", "low", "high"), ("visited", "low", "high")]),
        ("c02", [("likely_account", "medium", "medium")]),
        ("c03", [("transaction", "sensitive", "medium")]),
        (
            "c04",
            [
                ("likely_account", "medium", "medium"),
                ("transaction", "sensitive", "medium"),
                ("visited", "low", "high"),
                ("visited", "low", "high"),
            ],
        ),
        ("c05", [("likely_account", "medium", "medium")]),
        ("c06", [("visited", "low", "high")]),
        ("c07", [("transaction", "sensitive", "low")]),
        ("c08", []),
        ("c09", []),
        ("c10", []),
        ("c11", [("likely_account", "medium", "medium")]),
        ("c12", []),
        ("c13", []),
        ("c14", [("visited", "low", "high")]),
        ("c15", [("marketing", "low", "low"), ("marketing", "low", "low")]),
        ("c16", []),
        ("c17", [("likely_account", "medium", "medium")]),
        ("c18", [("likely_account", "sensitive", "medium")]),
        ("c19", []),
        ("c20", [("likely_account", "medium", "medium"), ("likely_account", "medium", "medium")]),
        ("c21", [("transaction", "medium", "medium")]),
        ("c22", []),
        ("c23", [("likely_account", "medium", "medium")]),
        (
            "c24",
            [
                ("likely_account", "medium", "medium"),
                ("transaction", "sensitive", "medium"),
                ("visited", "low", "high"),
                ("visited", "low", "high"),
            ],
        ),
        ("c25", [("likely_account", "medium", "medium")]),
        ("c26", []),
        ("c27", [("likely_account", "medium", "medium")]),
        ("c28", [("likely_account", "medium", "medium")]),
        ("c29", []),
    ],
)
def test_authored_policy_expectations_are_not_silently_promoted(
    corpus: Manifest, case_id: str, expected: list[tuple[str, str, str]]
) -> None:
    case = next(x for x in corpus.cases if x.id == case_id)
    assert [
        (x.relationship_type, x.review_priority, x.confidence) for x in case.expected.relationships
    ] == expected
    for label in case.expected.relationships:
        assert label.retention_status == label.data_sale_status == "unknown"
        assert label.evidence_state == (
            "observed" if label.relationship_type == "visited" else "inferred"
        )


def test_unresolved_is_visible_unknown_not_low(corpus: Manifest) -> None:
    cases = {x.id: x for x in corpus.cases}
    for key in ["c08", "c09", "c10", "c16", "c19", "c29"]:
        assert cases[key].expected.relationships == []
        assert cases[key].expected.unresolved
        assert all(
            x.review_priority == "unknown" and x.confidence == "insufficient"
            for x in cases[key].expected.unresolved
        )


def test_duplicates_and_browser_visits_do_not_increase_account_confidence(corpus: Manifest) -> None:
    cases = {x.id: x for x in corpus.cases}
    original = cases["c02"].expected.relationships[0]
    assert cases["c05"].expected.relationships == [original]
    assert cases["c05"].expected.duplicate_groups == [["e01", "e04"]]
    assert cases["c04"].expected.relationships[0] == original
    assert cases["c06"].expected.relationships[0].support == ["h-dup-a", "h-distinct"]


def test_deletion_oracles_remove_only_deleted_provenance(corpus: Manifest) -> None:
    cases = {x.id: x for x in corpus.cases}
    assert cases["c23"].after_delete[0].expected.relationships == []
    overlap = cases["c24"].after_delete
    assert {x.relationship_type for x in overlap[0].expected.relationships} == {"visited"}
    assert {x.relationship_type for x in overlap[1].expected.relationships} == {
        "likely_account",
        "transaction",
    }
    assert overlap[2].expected.relationships == []
    assert cases["c25"].after_delete[0].expected.relationships[0].support == ["e04"]
    assert cases["c25"].after_delete[1].expected.relationships[0].support == ["e01"]


def test_invalid_time_annotations_remain_null_and_missing_field_is_explicit(
    corpus: Manifest,
) -> None:
    events = {e.id: e for source in corpus.sources for e in source.events}
    for key in [
        "e11",
        "h-time-text",
        "h-time-null",
        "h-time-negative",
        "h-time-overflow",
        "h-time-fraction",
    ]:
        assert events[key].time_status == "invalid"
        assert events[key].expected_utc is None
    raw = json.loads((DEFAULT_ROOT / "history/malformed-times.json").read_text())
    assert [x.get("time_usec") for x in raw["Browser History"][:5]] == [
        "not-a-number",
        None,
        -1,
        9223372036854775808,
        1792238400000000.5,
    ]
    assert "time_usec" not in raw["Browser History"][5]
    assert events["h-time-missing"].disposition == "exclude"


def test_validator_does_not_open_network_connections(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Corpus validation must stay offline")

    monkeypatch.setattr(socket, "socket", forbidden)
    assert validate().synthetic_only


def test_raw_file_tampering_is_detected(copy_corpus: Path) -> None:
    path = copy_corpus / "emails/registration-shop.eml"
    path.write_bytes(path.read_bytes() + b"SYNTHETIC_TAMPER\r\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        validate(copy_corpus)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("review_priority", "high"),
        ("retention_status", "verified_retained"),
        ("data_sale_status", "verified_shared_or_sold"),
        ("evidence_state", "confirmed"),
    ],
)
def test_unsupported_label_values_are_rejected(copy_corpus: Path, field: str, value: str) -> None:
    data = read_manifest(copy_corpus)
    data["cases"][1]["expected"]["relationships"][0][field] = value
    save_manifest(copy_corpus, data)
    with pytest.raises(ValueError):
        validate(copy_corpus)


def test_stale_deleted_evidence_is_rejected(copy_corpus: Path) -> None:
    data = read_manifest(copy_corpus)
    case = next(x for x in data["cases"] if x["id"] == "c24")
    case["after_delete"][0]["expected"]["relationships"][0]["support"] = ["e01"]
    save_manifest(copy_corpus, data)
    with pytest.raises(ValueError, match="unsupported relationship citation"):
        validate(copy_corpus)


def test_coverage_gap_is_rejected(copy_corpus: Path) -> None:
    data = read_manifest(copy_corpus)
    next(x for x in data["cases"] if x["id"] == "c18")["coverage"].remove("health_context")
    save_manifest(copy_corpus, data)
    with pytest.raises(ValueError, match="coverage gap"):
        validate(copy_corpus)


@pytest.mark.parametrize("mutation", ["path", "locator", "anchor", "domain", "synthetic"])
def test_invalid_manifest_references_and_provenance_are_rejected(
    copy_corpus: Path, mutation: str
) -> None:
    data = read_manifest(copy_corpus)
    if mutation == "path":
        data["sources"][0]["path"] = "../../.env"
    elif mutation == "locator":
        next(x for x in data["sources"] if x["id"] == "h01")["events"][0]["locator"] = (
            "/Browser History/999"
        )
    elif mutation == "anchor":
        data["sources"][0]["events"][0]["anchors"].append("SYNTHETIC_MISSING_ANCHOR")
    elif mutation == "domain":
        data["cases"][1]["expected"]["relationships"][0]["domain"] = "unrelated.test"
    else:
        data["synthetic_only"] = False
    save_manifest(copy_corpus, data)
    with pytest.raises(ValueError):
        validate(copy_corpus)


def test_unlisted_raw_file_is_rejected(copy_corpus: Path) -> None:
    (copy_corpus / "emails/unlisted.eml").write_text("SYNTHETIC_ONLY", encoding="utf-8")
    with pytest.raises(ValueError, match="unlisted/missing raw fixture"):
        validate(copy_corpus)


@pytest.mark.parametrize(
    ("case_id", "index", "expected"),
    [
        ("c23", 0, []),
        (
            "c24",
            0,
            [("visited", "low", "high", ["h-shop"]), ("visited", "low", "high", ["h-news"])],
        ),
        (
            "c24",
            1,
            [
                ("likely_account", "medium", "medium", ["e01"]),
                ("transaction", "sensitive", "medium", ["e02"]),
            ],
        ),
        ("c24", 2, []),
        ("c25", 0, [("likely_account", "medium", "medium", ["e04"])]),
        ("c25", 1, [("likely_account", "medium", "medium", ["e01"])]),
    ],
)
def test_all_six_deletion_snapshot_dimensions_and_support(
    corpus: Manifest,
    case_id: str,
    index: int,
    expected: list[tuple[str, str, str, list[str]]],
) -> None:
    case = next(x for x in corpus.cases if x.id == case_id)
    snapshot = case.after_delete[index].expected
    assert [
        (x.relationship_type, x.review_priority, x.confidence, x.support)
        for x in snapshot.relationships
    ] == expected
    assert not snapshot.unresolved
    assert not snapshot.excluded
    assert not snapshot.duplicate_groups
    for label in snapshot.relationships:
        assert label.retention_status == label.data_sale_status == "unknown"


def test_c12_excludes_every_invalid_or_missing_history_timestamp(corpus: Manifest) -> None:
    source = next(x for x in corpus.sources if x.id == "h06")
    case = next(x for x in corpus.cases if x.id == "c12")
    assert len(source.events) == 6
    assert case.expected.excluded == [x.id for x in source.events]
    assert not case.expected.relationships
    assert not case.expected.unresolved
    for event in source.events:
        assert event.disposition == "exclude"
        assert event.expected_utc is event.observation_kind is event.domain_label is None


@pytest.mark.parametrize("row", range(6))
def test_invalid_history_time_cannot_be_promoted_to_eligible(copy_corpus: Path, row: int) -> None:
    data = read_manifest(copy_corpus)
    event = next(x for x in data["sources"] if x["id"] == "h06")["events"][row]
    event.update(
        disposition="eligible",
        observation_kind="site_visit_observed",
        domain_label="fictional-clock.test",
    )
    save_manifest(copy_corpus, data)
    with pytest.raises(ValueError, match="strict P0 history timestamp exclusion"):
        validate(copy_corpus)


@pytest.mark.parametrize("mutation", ["status", "reviewer", "blind_review"])
def test_baseline_cannot_claim_independent_human_review(copy_corpus: Path, mutation: str) -> None:
    data = read_manifest(copy_corpus)
    if mutation == "status":
        data["review_status"] = "independently_reviewed"
    elif mutation == "reviewer":
        data["independent_reviewer"] = "fabricated-reviewer"
    else:
        data["approval"]["independent_blind_human_review"] = True
    save_manifest(copy_corpus, data)
    with pytest.raises(ValueError):
        validate(copy_corpus)


def test_payment_claim_boundaries_are_explicit(corpus: Manifest) -> None:
    cases = {x.id: x for x in corpus.cases}
    conflict = cases["c07"].expected.relationships[0]
    assert conflict.support == ["e02", "e05"]
    assert "Contradictory payment claims" in conflict.limitations[0]
    invoice = cases["c21"].expected.relationships[0]
    assert invoice.support == ["e19"]
    assert "unpaid" in invoice.limitations[0]
    assert "No retained payment credentials are asserted" in invoice.limitations[1]


def test_original_evidence_and_deletion_history_are_preserved(corpus: Manifest) -> None:
    original = read_manifest(DEFAULT_ROOT / "archive/1.0.0")
    assert original["corpus_version"] == "1.0.0"
    assert original["review_status"] == "awaiting_independent_review"
    assert original["independent_reviewer"] is None
    previous_sources = {x["id"]: x for x in original["sources"]}
    for source in corpus.sources:
        previous = previous_sources[source.id]
        assert source.sha256 == previous["sha256"]
        assert [(x.id, x.locator, x.anchors) for x in source.events] == [
            (x["id"], x["locator"], x["anchors"]) for x in previous["events"]
        ]
    previous_cases = {x["id"]: x for x in original["cases"]}
    for case in corpus.cases:
        assert [x.model_dump() for x in case.after_delete] == previous_cases[case.id][
            "after_delete"
        ]
        if case.id not in {"c07", "c12", "c21"}:
            assert case.model_dump() == previous_cases[case.id]
