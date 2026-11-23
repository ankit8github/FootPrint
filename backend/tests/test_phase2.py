"""Strict boundary, volume, leakage and no-persistence tests for Phase 2."""

import json
import logging
from copy import deepcopy
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.phase2 import MAX_BODY, NormalizedBatch

client = TestClient(app)
URL = "/api/v1/phase2/validate"
SECRET = "SYNTHETIC_SECRET_NEVER_LOG_OR_ECHO"


def payload() -> dict[str, Any]:
    return {
        "schema_version": "phase2-normalized-v1",
        "synthetic_only": True,
        "sources": [
            {
                "source_id": str(UUID(int=1)),
                "adapter": "browser_chrome_json_v1",
                "records": [
                    {
                        "record_index": 0,
                        "disposition": "normalized",
                        "code": "OK",
                        "duplicate_of_index": None,
                        "observation": {
                            "adapter": "browser_chrome_json_v1",
                            "kind": "site_visit_observed",
                            "domain": "fictional-shop.test",
                            "occurred_at": "2026-10-17T12:00:00.000001Z",
                            "summary_code": "VISIT_RECORDED",
                            "origin": "browser_record",
                            "time_status": "valid",
                        },
                    }
                ],
            }
        ],
    }


def test_normalized_validation_is_transient_and_does_not_echo_records() -> None:
    result = client.post(URL, json=payload())
    assert result.status_code == 200
    assert result.json() == {
        "schema_version": "phase2-normalized-v1",
        "synthetic_only": True,
        "records": 1,
    }
    assert result.headers["cache-control"] == "no-store"
    assert client.get("/api/v1/demo").json()["observations"] == []
    assert client.post("/api/v1/imports", json=payload()).status_code == 404


@pytest.mark.parametrize("level", ["batch", "source", "record", "observation"])
@pytest.mark.parametrize("field", ["raw_body", "url", "sender_address", "safe_metadata", "subject"])
def test_arbitrary_raw_fields_are_rejected_without_leakage(
    level: str,
    field: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    data = payload()
    source = data["sources"][0]
    record = source["records"][0]
    target = {
        "batch": data,
        "source": source,
        "record": record,
        "observation": record["observation"],
    }[level]
    target[field] = SECRET
    caplog.set_level(logging.DEBUG)
    response = client.post(URL, json=data)
    assert response.status_code == 422
    assert response.json() == {"code": "INVALID_NORMALIZED_PAYLOAD"}
    assert SECRET not in response.text + caplog.text


@pytest.mark.parametrize(
    "value",
    [
        "https://fictional-shop.test/?token=" + SECRET,
        "sender@fictional-shop.test",
        "sub.fictional-shop.test",
        "127.0.0.1",
        "example.com",
        "localhost",
        "FOO.test",
        "foo.test/",
        "foo..test",
        "-foo.test",
    ],
)
def test_domain_is_a_canonical_synthetic_domain_only(value: str) -> None:
    data = payload()
    data["sources"][0]["records"][0]["observation"]["domain"] = value
    assert client.post(URL, json=data).status_code == 422


@pytest.mark.parametrize(
    "value",
    [
        None,
        "not-a-date",
        "2026-02-30T12:00:00Z",
        "2026-10-17T12:00:00",
        "2026-10-17T12:00:00+05:30",
        "1969-12-31T23:59:59Z",
        "2101-01-01T00:00:00Z",
        1792238400000000,
    ],
)
def test_history_requires_valid_utc_timestamp(value: Any) -> None:
    data = payload()
    data["sources"][0]["records"][0]["observation"]["occurred_at"] = value
    assert client.post(URL, json=data).status_code == 422


def test_email_invalid_date_allowed_only_as_explicit_unknown_time() -> None:
    data = payload()
    source = data["sources"][0]
    source["adapter"] = "email_eml_v1"
    record = source["records"][0]
    record["code"] = "EMAIL_UNCLASSIFIED"
    record["observation"].update(
        adapter="email_eml_v1",
        kind="unclassified_observation",
        summary_code="EMAIL_RECEIVED_UNVERIFIED",
        origin="unverified_sender",
        occurred_at=None,
        time_status="invalid",
    )
    assert client.post(URL, json=data).status_code == 200
    record["observation"]["kind"] = "registration_email_detected"
    assert client.post(URL, json=data).status_code == 422


@pytest.mark.parametrize(
    "media,body",
    [
        ("multipart/form-data; boundary=x", SECRET),
        ("text/plain", SECRET),
        ("application/json", '{"raw_body":"' + SECRET),
        ("application/json", "[" * 1000 + SECRET),
    ],
)
def test_multipart_and_malformed_json_fail_without_body_echo(media: str, body: str) -> None:
    response = client.post(URL, content=body, headers={"content-type": media})
    assert response.status_code in {415, 422}
    assert SECRET not in response.text


def test_actual_body_size_is_bounded_even_without_content_length() -> None:
    response = client.post(
        URL,
        content=iter([b" " * (MAX_BODY // 2), b" " * (MAX_BODY // 2), SECRET.encode()]),
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 413
    assert response.json() == {"code": "BODY_LIMIT"}


def test_total_record_budget_and_provenance_invariants() -> None:
    data = payload()
    original = data["sources"][0]["records"][0]
    records = [{**deepcopy(original), "record_index": i} for i in range(10_000)]
    data["sources"][0]["records"] = records
    assert NormalizedBatch.model_validate_json(json.dumps(data))
    data["sources"].append(
        {"source_id": str(UUID(int=2)), "adapter": "browser_chrome_json_v1", "records": [original]}
    )
    with pytest.raises(ValidationError):
        NormalizedBatch.model_validate_json(json.dumps(data))
    data = payload()
    data["sources"].append(deepcopy(data["sources"][0]))
    assert client.post(URL, json=data).status_code == 422
    data = payload()
    data["sources"][0]["records"][0].update(
        disposition="duplicate", observation=None, code="DUPLICATE_RECORD", duplicate_of_index=1
    )
    assert client.post(URL, json=data).status_code == 422


def test_strict_boolean_integer_and_version_contract() -> None:
    for field, value in [
        ("synthetic_only", False),
        ("synthetic_only", "true"),
        ("schema_version", "v2"),
    ]:
        data = payload()
        data[field] = value
        assert client.post(URL, json=data).status_code == 422
    data = payload()
    data["sources"][0]["records"][0]["record_index"] = True
    assert client.post(URL, json=data).status_code == 422


@pytest.mark.parametrize(
    "body",
    [
        '{"schema_version":"phase2-normalized-v1","synthetic_only":false,"synthetic_only":true,"sources":[]}',
        '{"__proto__":{}}',
        '{"constructor":{}}',
        '{"sources":[NaN]}',
        '{"sources":[Infinity]}',
    ],
)
def test_duplicate_prototype_keys_and_non_json_constants_are_rejected(body: str) -> None:
    response = client.post(URL, content=body, headers={"content-type": "application/json"})
    assert response.status_code == 422
    assert response.json() == {"code": "INVALID_NORMALIZED_PAYLOAD"}
