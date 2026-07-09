"""Unit tests for legal workflow run control preview API contracts."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from legal_consulting_agent.api.error_handlers import register_error_handlers
from legal_consulting_agent.api.v1.router import router as v1_router


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(v1_router, prefix="/v1")
    register_error_handlers(app)
    return TestClient(app)


def base_payload() -> dict[str, object]:
    return {
        "state": {
            "thread_id": "session-public-id",
            "user_id": 1,
            "question": "Can my employer change my role unilaterally?",
            "prompt_version": "legal_generation:v1",
            "workflow_version": "legal_workflow:v1",
            "error_code": "DB_UNAVAILABLE",
            "message_id": 99,
            "node_trace": ["input_safety", "persist"],
            "category": "civil_labor",
            "high_risk": False,
        }
    }


def test_cancel_preview_marks_state_canceled_without_database_dependency() -> None:
    client = build_client()

    response = client.post(
        "/v1/workflow-runs/cancel-preview",
        headers={"x-user-public-id": "user-public-id"},
        json=base_payload(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["operation"] == "cancel_preview"
    assert body["data"]["state"]["error_code"] == "CANCELED"
    assert body["data"]["state"]["message_id"] == 99
    assert body["data"]["state"]["node_trace"] == ["input_safety", "persist"]


def test_retry_preview_clears_failed_state_fields() -> None:
    client = build_client()

    response = client.post(
        "/v1/workflow-runs/retry-preview",
        headers={"x-user-public-id": "user-public-id"},
        json=base_payload(),
    )

    assert response.status_code == 200
    body = response.json()
    state = body["data"]["state"]
    assert body["error"] is None
    assert body["data"]["operation"] == "retry_preview"
    assert "error_code" not in state
    assert "message_id" not in state
    assert state["node_trace"] == []
    assert state["thread_id"] == "session-public-id"
    assert state["category"] == "civil_labor"


def test_run_control_preview_requires_user_identity_header() -> None:
    client = build_client()

    response = client.post(
        "/v1/workflow-runs/cancel-preview",
        json=base_payload(),
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"
