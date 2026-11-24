"""The integrated MVP adds no ingestion, deletion or action-state API."""

import logging

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
SECRET = "SYNTHETIC_PHASE5_SECRET_NEVER_UPLOAD"


@pytest.mark.parametrize("field", ["session_sources", "opened", "action_directory", "findings"])
def test_session_extensions_remain_rejected(field: str, caplog: pytest.LogCaptureFixture) -> None:
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


@pytest.mark.parametrize("path", ["/api/v1/phase5", "/api/v1/imports", "/api/v1/actions"])
def test_no_integrated_upload_or_delete_route(path: str) -> None:
    response = client.post(path, files={"source": ("synthetic.eml", SECRET)})
    assert response.status_code == 404
    assert SECRET not in response.text
    assert client.delete(path).status_code == 404
