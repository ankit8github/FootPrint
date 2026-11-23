"""Phase 3 stays local: no graph ingestion, schema expansion, upload or echo."""

import logging

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
SECRET = "SYNTHETIC_PHASE3_SECRET_NEVER_UPLOAD"


@pytest.mark.parametrize(
    "field", ["observations", "features", "relationships", "raw_body", "metadata"]
)
def test_existing_boundary_rejects_graph_and_raw_extensions_without_logging(
    field: str, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    result = client.post(
        "/api/v1/phase2/validate",
        json={
            "schema_version": "phase2-normalized-v1",
            "synthetic_only": True,
            "sources": [],
            field: SECRET,
        },
    )
    assert result.status_code == 422
    assert result.json() == {"code": "INVALID_NORMALIZED_PAYLOAD"}
    assert SECRET not in result.text + caplog.text
    assert client.get("/api/v1/demo").json()["observations"] == []


@pytest.mark.parametrize("path", ["/api/v1/phase3", "/api/v1/phase3/validate", "/api/v1/discovery"])
def test_no_phase3_ingestion_route_or_multipart_upload(path: str) -> None:
    response = client.post(path, files={"source": ("synthetic.eml", SECRET)})
    assert response.status_code == 404
    assert SECRET not in response.text
