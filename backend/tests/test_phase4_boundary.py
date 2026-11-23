"""Phase 4 assessments/context stay browser-local; no new ingestion boundary."""

import logging

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
SECRET = "SYNTHETIC_PHASE4_SECRET_NEVER_UPLOAD"


@pytest.mark.parametrize(
    "field", ["assessments", "context_evidence", "review_priority", "explanation", "rationales"]
)
def test_assessment_or_context_extension_rejected_without_echo_or_log(
    field: str, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    response = client.post(
        "/api/v1/phase2/validate",
        json={
            "schema_version": "phase2-normalized-v1",
            "synthetic_only": True,
            "sources": [],
            field: SECRET,
        },
    )
    assert response.status_code == 422
    assert response.json() == {"code": "INVALID_NORMALIZED_PAYLOAD"}
    assert SECRET not in response.text + caplog.text
    assert client.get("/api/v1/demo").json()["assessments"] == []


@pytest.mark.parametrize("path", ["/api/v1/phase4", "/api/v1/assessments"])
def test_no_assessment_upload_route(path: str) -> None:
    response = client.post(path, files={"source": ("synthetic.eml", SECRET)})
    assert response.status_code == 404
    assert SECRET not in response.text
