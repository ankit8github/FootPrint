"""Offline Phase 1 artifact checks, not an import adapter or classifier.

Reads only a versioned repository corpus: hashes, literal evidence anchors,
authored labels, coverage and reference integrity. Never derives labels from
email/URL contents, decodes MIME, normalizes URLs, or executes deletion logic.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "tests/fixtures/pv1/v1"
REQUIRED_COVERAGE = frozenset(
    {
        "registration",
        "receipt",
        "marketing",
        "visits_only",
        "email_duplicate",
        "history_duplicate",
        "conflicting_evidence",
        "spoofed_origin",
        "phishing_origin",
        "ambiguous_origin",
        "shared_delivery",
        "malformed_email_timestamp",
        "malformed_history_timestamp",
        "missing_history_timestamp",
        "unsafe_url",
        "query_fragment",
        "url_credentials",
        "deletion_sole_source",
        "deletion_overlap",
        "deletion_duplicate",
        "prompt_injection",
        "html_content",
        "attachment",
        "health_context",
        "similar_domains",
        "quoted_registration",
        "malformed_header",
        "encoded_header",
        "encrypted_history",
        "old_visit",
        "account_notification",
        "unpaid_invoice",
    }
)
ID = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_-]{1,63}$")]
Domain = Annotated[str, Field(pattern=r"^[a-z0-9.-]+\.(test|invalid)$", max_length=253)]
UTC = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")]
Kind = Literal[
    "site_visit_observed",
    "registration_email_detected",
    "transaction_email_detected",
    "marketing_email_detected",
    "account_notification_detected",
    "unclassified_observation",
]
Rationale = Literal[
    "TRANSACTION_INDICATION",
    "IDENTITY_CONTEXT",
    "HEALTH_CONTEXT",
    "ACCOUNT_RELATIONSHIP",
    "MARKETING_ONLY",
    "VISIT_ONLY",
    "AMBIGUOUS_EVIDENCE",
]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Event(Record):
    id: ID
    locator: str
    anchors: Annotated[list[str], Field(min_length=1)]
    disposition: Literal["eligible", "unresolved", "exclude"]
    observation_kind: Kind | None
    domain_label: Domain | None
    time_status: Literal["valid", "invalid", "missing", "not_applicable"]
    expected_utc: UTC | None
    reason: Annotated[str, Field(min_length=20)]


class Source(Record):
    id: ID
    path: str
    adapter: Literal["email_eml_v1", "browser_chrome_json_v1"]
    sha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    tags: Annotated[list[str], Field(min_length=1)]
    events: Annotated[list[Event], Field(min_length=1)]


class Relationship(Record):
    domain: Domain
    relationship_type: Literal["visited", "likely_account", "transaction", "marketing"]
    evidence_state: Literal["observed", "inferred"]
    confidence: Literal["high", "medium", "low", "insufficient"]
    review_priority: Literal["sensitive", "medium", "low", "unknown"]
    rationale_codes: Annotated[list[Rationale], Field(min_length=1)]
    support: Annotated[list[ID], Field(min_length=1)]
    limitations: Annotated[list[str], Field(min_length=1)]
    retention_status: Literal["unknown"]
    data_sale_status: Literal["unknown"]


class Unresolved(Record):
    support: Annotated[list[ID], Field(min_length=1)]
    confidence: Literal["insufficient"]
    review_priority: Literal["unknown"]
    rationale_codes: list[Literal["AMBIGUOUS_EVIDENCE"]]
    reason: Annotated[str, Field(min_length=20)]


class Snapshot(Record):
    relationships: list[Relationship]
    unresolved: list[Unresolved]
    excluded: list[ID]
    duplicate_groups: list[Annotated[list[ID], Field(min_length=2)]]


class Deletion(Record):
    delete_sources: Annotated[list[ID], Field(min_length=1)]
    expected: Snapshot
    reason: Annotated[str, Field(min_length=20)]


class Case(Record):
    id: ID
    title: str
    sources: Annotated[list[ID], Field(min_length=1)]
    coverage: Annotated[list[str], Field(min_length=1)]
    rationale: Annotated[str, Field(min_length=30)]
    expected: Snapshot
    after_delete: list[Deletion]


class Approval(Record):
    authority: Literal["product_owner"]
    basis: Literal["explicit_user_instruction_in_PR_1_finalization_request"]
    date: Literal["2026-11-23"]
    decision_record: Literal["docs/PHASE1-TAXONOMY-DECISION.md"]
    independent_blind_human_review: Literal[False]


class Manifest(Record):
    schema_version: Literal["phase1-ground-truth-v1"]
    corpus_version: Literal["1.1.0"]
    synthetic_only: Literal[True]
    provenance: Literal["authored_from_scratch_no_user_exports"]
    reference_time: UTC
    history_epoch: Literal["unix_microseconds_utc"]
    review_status: Literal["product-owner-approved, AI-assisted baseline"]
    approval: Approval
    independent_reviewer: None
    limitations: Annotated[list[str], Field(min_length=1)]
    sources: Annotated[list[Source], Field(min_length=1)]
    cases: Annotated[list[Case], Field(min_length=1)]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def unique(values: list[str], context: str) -> None:
    require(len(values) == len(set(values)), f"duplicate IDs/references: {context}")


def source_bytes(root: Path, source: Source) -> bytes:
    expected = (
        r"emails/[a-z0-9-]+\.eml"
        if source.adapter == "email_eml_v1"
        else r"history/[a-z0-9-]+\.json"
    )
    require(re.fullmatch(expected, source.path) is not None, f"unsafe fixture path: {source.id}")
    path = root / source.path
    require(
        not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),
        "fixture escapes corpus",
    )
    data = path.read_bytes()
    require(len(data) <= 65536, f"fixture exceeds repository corpus budget: {source.id}")
    require(hashlib.sha256(data).hexdigest() == source.sha256, f"hash mismatch: {source.id}")
    return data


def check_snapshot(snapshot: Snapshot, active: dict[str, Event], context: str) -> None:
    seen: set[str] = set()
    keys = [f"{x.domain}/{x.relationship_type}" for x in snapshot.relationships]
    unique(keys, context)
    unique(snapshot.excluded, context)
    require(
        all(x in active and active[x].disposition == "exclude" for x in snapshot.excluded),
        f"invalid exclusion: {context}",
    )
    seen.update(snapshot.excluded)
    for label in snapshot.relationships:
        unique(label.support, context)
        require(
            all(x in active and active[x].disposition == "eligible" for x in label.support),
            f"unsupported relationship citation: {context}",
        )
        require(
            all(active[x].domain_label == label.domain for x in label.support),
            f"relationship cites a different domain: {context}",
        )
        if label.relationship_type == "visited":
            require(label.evidence_state == "observed", f"visit must remain observed: {context}")
            require(
                all(active[x].observation_kind == "site_visit_observed" for x in label.support),
                f"visit cites non-visit annotation: {context}",
            )
        else:
            require(
                label.evidence_state == "inferred", f"relationship must remain inferred: {context}"
            )
        seen.update(label.support)
    for item in snapshot.unresolved:
        unique(item.support, context)
        require(item.rationale_codes == ["AMBIGUOUS_EVIDENCE"], f"unresolved rationale: {context}")
        require(
            all(x in active and active[x].disposition == "unresolved" for x in item.support),
            f"unresolved citation is invalid: {context}",
        )
        seen.update(item.support)
    duplicated: set[str] = set()
    for group in snapshot.duplicate_groups:
        unique(group, context)
        require(set(group) <= active.keys(), f"unknown duplicate member: {context}")
        require(not duplicated.intersection(group), f"overlapping duplicate groups: {context}")
        require(group[0] in seen, f"duplicate canonical event has no disposition: {context}")
        duplicated.update(group)
        seen.update(group)
    require(seen == active.keys(), f"unaccounted or stale events in snapshot: {context}")


def validate(root: Path = DEFAULT_ROOT) -> Manifest:
    """Validate declared artifacts; no interpretation or prediction from raw text."""
    manifest = Manifest.model_validate_json((root / "manifest.json").read_bytes())
    unique([s.id for s in manifest.sources], "sources")
    unique([s.path for s in manifest.sources], "paths")
    unique([c.id for c in manifest.cases], "cases")
    sources = {s.id: s for s in manifest.sources}
    events: dict[str, Event] = {}
    raw_events: dict[str, bytes] = {}
    for source in manifest.sources:
        require(set(source.tags) <= REQUIRED_COVERAGE, f"unknown source coverage tag: {source.id}")
        data = source_bytes(root, source)
        text = data.decode("utf-8")
        # Repository hygiene checks, not an imported-message parser.
        addresses = re.findall(r"[A-Za-z0-9_.+-]+@([A-Za-z0-9.-]+)", text)
        require(
            all(x.endswith((".test", ".invalid")) for x in addresses),
            f"non-fictional email domain in {source.id}",
        )
        require(
            not re.search(
                r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY|AKIA[0-9A-Z]{16}|"
                r"gh[pousr]_[A-Za-z0-9]{30,}",
                text,
            ),
            f"credential pattern in {source.id}",
        )
        rows: list[Any] | None = None
        if source.adapter == "email_eml_v1":
            require(len(source.events) == 1, f"email event count: {source.id}")
            require(
                b"X-PV1-Fixture: synthetic-only" in data, f"missing synthetic marker: {source.id}"
            )
            require(
                b"\r\n\r\n" in data and b"\n" not in data.replace(b"\r\n", b""),
                f"email must preserve CRLF bytes: {source.id}",
            )
        else:
            document = json.loads(text)
            require(
                isinstance(document, dict) and set(document) == {"Browser History"},
                f"fixture envelope mismatch: {source.id}",
            )
            rows = document["Browser History"]
            require(
                isinstance(rows, list) and len(rows) == len(source.events),
                f"history event count: {source.id}",
            )
        for index, event in enumerate(source.events):
            require(event.id not in events, f"duplicate event id: {event.id}")
            events[event.id] = event
            if rows is None:
                require(event.locator == "whole_message", f"invalid email locator: {event.id}")
                evidence = text
                raw_events[event.id] = data
            else:
                require(
                    event.locator == f"/Browser History/{index}",
                    f"invalid history locator: {event.id}",
                )
                row = rows[index]
                # Object shape is checked only for authored fixture rows. Intentionally
                # malformed field values are preserved; nothing is normalized.
                require(isinstance(row, (dict, str)), f"fixture row shape: {event.id}")
                if isinstance(row, dict):
                    require(
                        set(row) <= {"url", "title", "time_usec", "client_id", "favicon_url"}
                        and isinstance(row.get("url"), str),
                        f"fixture object fields: {event.id}",
                    )
                    require(
                        ("time_usec" not in row) == (event.time_status == "missing"),
                        f"missing timestamp annotation mismatch: {event.id}",
                    )
                    if event.time_status in {"invalid", "missing"}:
                        require(
                            event.disposition == "exclude"
                            and event.observation_kind is None
                            and event.domain_label is None,
                            f"strict P0 history timestamp exclusion required: {event.id}",
                        )
                else:
                    require(
                        row == "Your data is encrypted and cannot be exported"
                        and "encrypted_history" in source.tags
                        and event.disposition == "exclude",
                        f"unlabeled non-record history sentinel: {event.id}",
                    )
                evidence = json.dumps(row, ensure_ascii=False, sort_keys=True)
                raw_events[event.id] = evidence.encode("utf-8")
            require(
                all(anchor in evidence for anchor in event.anchors),
                f"evidence anchor missing: {event.id}",
            )
            require(
                (event.time_status == "valid") == (event.expected_utc is not None),
                f"time annotation must not fabricate dates: {event.id}",
            )
            require(
                event.disposition != "eligible" or event.domain_label is not None,
                f"eligible event lacks a labeled domain: {event.id}",
            )
    actual = {
        str(p.relative_to(root)).replace("\\", "/")
        for folder in ["emails", "history"]
        for p in (root / folder).rglob("*")
        if p.is_file()
    }
    require(actual == {s.path for s in manifest.sources}, "unlisted/missing raw fixture files")
    used: set[str] = set()
    coverage: set[str] = set()
    for case in manifest.cases:
        unique(case.sources, case.id)
        require(set(case.sources) <= sources.keys(), f"unknown case source: {case.id}")
        require(set(case.coverage) <= REQUIRED_COVERAGE, f"unknown case coverage: {case.id}")
        declared = set().union(*(set(sources[x].tags) for x in case.sources))
        # Deletion coverage belongs to the scenario; other tags require source evidence.
        require(
            set(case.coverage) - {"deletion_sole_source", "deletion_overlap", "deletion_duplicate"}
            <= declared,
            f"case coverage lacks source evidence: {case.id}",
        )
        used.update(case.sources)
        coverage.update(case.coverage)
        active = {event.id: event for key in case.sources for event in sources[key].events}
        check_snapshot(case.expected, active, case.id)
        for snapshot in [case.expected, *(x.expected for x in case.after_delete)]:
            for group in snapshot.duplicate_groups:
                require(
                    len({raw_events[x] for x in group}) == 1,
                    f"non-identical duplicate group: {case.id}",
                )
        for deletion in case.after_delete:
            unique(deletion.delete_sources, case.id)
            require(
                set(deletion.delete_sources) <= set(case.sources),
                f"unknown deletion source: {case.id}",
            )
            remaining = {
                event.id: event
                for key in case.sources
                if key not in deletion.delete_sources
                for event in sources[key].events
            }
            check_snapshot(deletion.expected, remaining, f"{case.id}/after_delete")
        require(
            not any(x.startswith("deletion_") for x in case.coverage) or bool(case.after_delete),
            f"deletion coverage lacks snapshots: {case.id}",
        )
    require(used == sources.keys(), "raw source without a scenario")
    require(coverage == REQUIRED_COVERAGE, f"coverage gap: {sorted(REQUIRED_COVERAGE - coverage)}")
    return manifest


def metrics(manifest: Manifest) -> dict[str, Any]:
    """Corpus inventory benchmark only; no algorithm or efficacy is measured."""
    labels = [label for case in manifest.cases for label in case.expected.relationships]
    return {
        "corpus_version": manifest.corpus_version,
        "measurement": "authored_corpus_structure_only",
        "source_files": len(manifest.sources),
        "files_by_adapter": dict(sorted(Counter(x.adapter for x in manifest.sources).items())),
        "source_events": sum(len(x.events) for x in manifest.sources),
        "scenarios": len(manifest.cases),
        "deletion_snapshots": sum(len(x.after_delete) for x in manifest.cases),
        "coverage": {
            tag: sorted(x.id for x in manifest.cases if tag in x.coverage)
            for tag in sorted(REQUIRED_COVERAGE)
        },
        "scenario_label_counts": {
            field: dict(sorted(Counter(getattr(x, field) for x in labels).items()))
            for field in ["relationship_type", "review_priority", "confidence"]
        },
        "unresolved_scenarios": sum(bool(x.expected.unresolved) for x in manifest.cases),
        "unresolved_label_counts": {
            "review_priority": {"unknown": sum(len(x.expected.unresolved) for x in manifest.cases)},
            "confidence": {"insufficient": sum(len(x.expected.unresolved) for x in manifest.cases)},
        },
        "coverage_categories": len(REQUIRED_COVERAGE),
        "baseline_status": manifest.review_status,
        "independent_review": "not_performed",
        "independent_reviewer": manifest.independent_reviewer,
        "event_dispositions": dict(
            sorted(Counter(e.disposition for s in manifest.sources for e in s.events).items())
        ),
        "discovery_precision": None,
        "discovery_recall": None,
        "sensitivity_agreement": None,
        "runtime_parser_or_classifier_present": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=DEFAULT_ROOT, help="Versioned test corpus directory"
    )
    parser.add_argument(
        "--write-metrics",
        action="store_true",
        help="Refresh inventory metrics only, never labels/hashes",
    )
    args = parser.parse_args()
    try:
        result = metrics(validate(args.root))
        output = json.dumps(result, indent=2, sort_keys=True) + "\n"
        target = args.root / "metrics.json"
        if args.write_metrics:
            target.write_text(output, encoding="utf-8", newline="\n")
        else:
            require(
                target.read_text(encoding="utf-8") == output,
                "stale corpus metrics; use --write-metrics",
            )
        print(output, end="")
        return 0
    except (ValueError, ValidationError, OSError, KeyError, TypeError) as exc:
        print(f"FAIL: corpus validation: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
