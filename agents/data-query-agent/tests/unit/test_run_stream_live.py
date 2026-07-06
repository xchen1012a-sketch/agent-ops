"""Unit tests for the live thinking/answer streaming endpoint (STREAM-100)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from data_query_agent.api.dependencies import (
    get_identity_thread_service,
    get_llm_stream_adapter,
)
from data_query_agent.infrastructure.llm.fake_llm_adapter import FakeLlmAdapter
from data_query_agent.main import create_app


class _FakeThread:
    """Minimal stand-in; the endpoint only checks ownership, not thread fields."""

    public_id = "thread-1"


class FakeIdentityThreadService:
    """Fake identity service that owns one thread for subject ``owner``."""

    async def get_owned_thread(
        self, *, thread_public_id: str, external_subject: str
    ) -> _FakeThread | None:
        if external_subject == "owner" and thread_public_id == "thread-1":
            return _FakeThread()
        return None


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_identity_thread_service] = lambda: FakeIdentityThreadService()
    # Force the mock adapter so the live-stream test needs no DB-backed config lookup.
    app.dependency_overrides[get_llm_stream_adapter] = lambda: FakeLlmAdapter()
    return TestClient(app)


def test_stream_run_completion_emits_thinking_then_answer_contract() -> None:
    client = _client()

    response = client.post(
        "/v1/threads/thread-1/runs/stream",
        json={"question": "上月销售额是多少"},
        headers={"X-User-Subject": "owner"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert "event: run.started" in body
    assert "event: message.thinking.delta" in body
    assert "event: message.thinking.completed" in body
    assert "event: message.delta" in body
    assert "event: message.completed" in body
    # thinking must be emitted before answer body starts.
    assert body.index("message.thinking.delta") < body.index("message.delta")


def test_stream_run_completion_blocks_cross_subject_access() -> None:
    client = _client()

    response = client.post(
        "/v1/threads/thread-1/runs/stream",
        json={"question": "hi"},
        headers={"X-User-Subject": "other"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
