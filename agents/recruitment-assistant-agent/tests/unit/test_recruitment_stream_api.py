"""Unit tests for the recruitment live thinking/answer stream endpoint (STREAM-100)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from recruitment_assistant_agent.api.dependencies import get_recruitment_stream_adapter
from recruitment_assistant_agent.infrastructure.llm.fake_llm_adapter import FakeLlmAdapter
from recruitment_assistant_agent.main import create_app


def test_stream_run_completion_emits_thinking_then_answer_contract() -> None:
    app = create_app()
    # Force the mock adapter so the test needs no identity header or DB config lookup.
    app.dependency_overrides[get_recruitment_stream_adapter] = lambda: FakeLlmAdapter()
    client = TestClient(app)

    response = client.post(
        "/v1/recruitment-tasks/task-1/runs/stream",
        json={},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert "event: run.started" in body
    assert "event: message.thinking.delta" in body
    assert "event: message.thinking.completed" in body
    assert "event: message.delta" in body
    assert "event: message.completed" in body
    assert body.index("message.thinking.delta") < body.index("message.delta")
