"""Unit tests for run creation API slice."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from data_query_agent.api.dependencies import get_identity_thread_service, get_query_run_trace_service
from data_query_agent.domain.entities.identity import MessageRole, QueryThread, ThreadMessage, ThreadStatus
from data_query_agent.domain.entities.run import QueryRun, RunStatus
from data_query_agent.main import create_app


class FakeIdentityThreadService:
    """Fake identity service for run API tests."""

    def __init__(self) -> None:
        now = _now()
        self.thread = QueryThread(
            id=10,
            public_id="thread-1",
            user_id=20,
            title="Sales",
            status=ThreadStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        self.messages: list[ThreadMessage] = []

    async def get_owned_thread(self, *, thread_public_id: str, external_subject: str) -> QueryThread | None:
        if external_subject == "owner" and thread_public_id == self.thread.public_id:
            return self.thread
        return None

    async def create_message_for_subject(
        self,
        *,
        external_subject: str,
        thread_public_id: str,
        role: MessageRole,
        content: str,
    ) -> ThreadMessage:
        message = ThreadMessage(
            id=len(self.messages) + 1,
            public_id=f"message-{len(self.messages) + 1}",
            thread_id=self.thread.id or 0,
            user_id=self.thread.user_id,
            role=role,
            content=content,
            created_at=_now(),
        )
        self.messages.append(message)
        return message


class FakeRunTraceService:
    """Fake run trace service that creates pending runs only."""

    def __init__(self) -> None:
        self.runs: list[QueryRun] = []

    async def create_run_for_thread(
        self,
        *,
        thread: QueryThread,
        question_message_id: int | None = None,
    ) -> QueryRun:
        run = QueryRun(
            id=len(self.runs) + 1,
            public_id=f"run-{len(self.runs) + 1}",
            thread_id=thread.id or 0,
            user_id=thread.user_id,
            status=RunStatus.PENDING,
            question_message_id=question_message_id,
            error_code=None,
            error_message=None,
            started_at=None,
            finished_at=None,
            created_at=_now(),
            updated_at=_now(),
        )
        self.runs.append(run)
        return run


def _client(
    identity_service: FakeIdentityThreadService,
    run_service: FakeRunTraceService,
) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_identity_thread_service] = lambda: identity_service
    app.dependency_overrides[get_query_run_trace_service] = lambda: run_service
    return TestClient(app)


def test_create_run_creates_user_message_and_pending_run_without_sql() -> None:
    identity_service = FakeIdentityThreadService()
    run_service = FakeRunTraceService()
    client = _client(identity_service, run_service)

    response = client.post(
        "/v1/threads/thread-1/runs",
        headers={"X-User-Subject": "owner"},
        json={"question": "What are total sales?", "channel": "web"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["error"] is None
    assert body["data"]["run_id"] == "run-1"
    assert body["data"]["thread_id"] == "thread-1"
    assert body["data"]["status"] == "pending"
    assert body["data"]["question"] == "What are total sales?"
    assert "sql" not in body["data"]
    assert identity_service.messages[0].role is MessageRole.USER
    assert identity_service.messages[0].content == "What are total sales?"
    assert run_service.runs[0].question_message_id == identity_service.messages[0].id


def test_create_run_blocks_cross_subject_thread() -> None:
    client = _client(FakeIdentityThreadService(), FakeRunTraceService())

    response = client.post(
        "/v1/threads/thread-1/runs",
        headers={"X-User-Subject": "other"},
        json={"question": "What are total sales?"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_create_run_validates_question_body() -> None:
    client = _client(FakeIdentityThreadService(), FakeRunTraceService())

    response = client.post(
        "/v1/threads/thread-1/runs",
        headers={"X-User-Subject": "owner"},
        json={"question": ""},
    )

    assert response.status_code == 422


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
