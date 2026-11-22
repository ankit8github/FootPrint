import json
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.contracts import Assessment, DemoSnapshot, Observation
from app.main import app

client = TestClient(app)
root = Path(__file__).resolve().parents[2]


def test_health_and_empty_demo_match_shared_fixture() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"api_version": "v1", "status": "ok", "mode": "synthetic_demo"}
    assert response.headers["cache-control"] == "no-store"
    expected = json.loads((root / "tests/fixtures/phase0-empty.json").read_text())
    assert client.get("/api/v1/demo").json() == expected


@pytest.mark.parametrize("path", ["/api/v1/imports", "/api/v1/demo", "/api/v1/health"])
def test_no_ingestion_routes_or_reflected_payload(path: str) -> None:
    response = client.post(path, files={"file": ("fictional.eml", b"SYNTHETIC_UNTRUSTED_BODY")})
    assert response.status_code in {404, 405}
    assert "SYNTHETIC_UNTRUSTED_BODY" not in response.text


def test_contracts_forbid_unknown_fields_and_populated_snapshot() -> None:
    with pytest.raises(ValidationError):
        DemoSnapshot.model_validate({"raw_email_body": "SYNTHETIC_ONLY"})
    with pytest.raises(ValidationError):
        DemoSnapshot.model_validate({"observations": [{}]})


def test_future_observation_rejects_raw_metadata_and_naive_dates() -> None:
    data: dict[str, Any] = {
        "observation_id": UUID(int=1),
        "batch_id": UUID(int=2),
        "adapter": "browser_chrome_json_v1",
        "kind": "site_visit_observed",
        "domain": "fictional.test",
        "occurred_at": None,
        "summary_code": "VISIT_RECORDED",
    }
    assert Observation.model_validate(data).domain == "fictional.test"
    with pytest.raises(ValidationError):
        Observation.model_validate({**data, "safe_metadata": {"body": "SYNTHETIC_ONLY"}})
    with pytest.raises(ValidationError):
        Observation.model_validate_json(
            json.dumps(
                {
                    **data,
                    "observation_id": str(UUID(int=1)),
                    "batch_id": str(UUID(int=2)),
                    "occurred_at": "2026-11-22T12:00:00",
                }
            )
        )


def test_future_assessment_keeps_independent_dimensions_and_unknown_claims() -> None:
    data: dict[str, Any] = {
        "relationship_id": UUID(int=1),
        "evidence_state": "inferred",
        "confidence": "insufficient",
        "review_priority": "sensitive",
        "rationale_codes": ["TRANSACTION_INDICATION"],
    }
    assessment = Assessment.model_validate(data)
    assert assessment.confidence == "insufficient"
    assert assessment.review_priority == "sensitive"
    assert assessment.retention_status == assessment.data_sale_status == "unknown"
    for field, value in [
        ("retention_status", "verified_retained"),
        ("data_sale_status", "verified_shared_or_sold"),
        ("evidence_state", "confirmed"),
        ("review_priority", "high"),
    ]:
        with pytest.raises(ValidationError):
            Assessment.model_validate({**data, field: value})


def test_only_readonly_routes_are_registered() -> None:
    schema = app.openapi()
    assert set(schema["paths"]) == {"/api/v1/health", "/api/v1/demo"}
    for methods in schema["paths"].values():
        assert set(methods) == {"get"}
        assert "requestBody" not in methods["get"]


def test_unexpected_host_is_rejected() -> None:
    assert client.get("/api/v1/health", headers={"host": "untrusted.test"}).status_code == 400
