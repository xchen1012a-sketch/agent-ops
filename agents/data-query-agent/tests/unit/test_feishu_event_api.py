"""Unit tests for mock Feishu event API slice."""

from __future__ import annotations

from fastapi.testclient import TestClient

from data_query_agent.api.dependencies import get_feishu_mock_event_service
from data_query_agent.infrastructure.integrations.feishu_events import (
    MOCK_FEISHU_SIGNATURE,
    FeishuMockEventService,
)
from data_query_agent.main import create_app


def _client() -> TestClient:
    app = create_app()
    service = FeishuMockEventService()
    app.dependency_overrides[get_feishu_mock_event_service] = lambda: service
    return TestClient(app)


def test_feishu_challenge_event_returns_challenge_without_real_tenant() -> None:
    client = _client()

    response = client.post(
        "/v1/integrations/feishu/events",
        headers={"X-Feishu-Signature": MOCK_FEISHU_SIGNATURE},
        json={"type": "url_verification", "challenge": "challenge-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"] == {
        "event_type": "challenge",
        "event_id": None,
        "duplicate": False,
        "challenge": "challenge-token",
    }


def test_feishu_message_event_is_deduplicated_by_event_id() -> None:
    client = _client()
    payload = {
        "type": "message",
        "header": {"event_id": "evt-1"},
        "event": {"message": {"content": "total sales"}},
    }

    first = client.post(
        "/v1/integrations/feishu/events",
        headers={"X-Feishu-Signature": MOCK_FEISHU_SIGNATURE},
        json=payload,
    )
    second = client.post(
        "/v1/integrations/feishu/events",
        headers={"X-Feishu-Signature": MOCK_FEISHU_SIGNATURE},
        json=payload,
    )

    assert first.status_code == 200
    assert first.json()["data"]["duplicate"] is False
    assert first.json()["data"]["event_id"] == "evt-1"
    assert second.status_code == 200
    assert second.json()["data"]["duplicate"] is True


def test_feishu_event_rejects_invalid_signature_and_bad_payload() -> None:
    client = _client()

    invalid_signature = client.post(
        "/v1/integrations/feishu/events",
        headers={"X-Feishu-Signature": "bad"},
        json={"type": "message", "header": {"event_id": "evt-1"}},
    )
    bad_payload = client.post(
        "/v1/integrations/feishu/events",
        headers={"X-Feishu-Signature": MOCK_FEISHU_SIGNATURE},
        json={"type": "message", "header": {}},
    )

    assert invalid_signature.status_code == 403
    assert invalid_signature.json()["error"]["code"] == "AUTH_FORBIDDEN"
    assert bad_payload.status_code == 422
    assert bad_payload.json()["error"]["code"] == "INPUT_BLOCKED"
