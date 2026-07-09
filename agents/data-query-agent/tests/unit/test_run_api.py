"""Unit tests for run creation API slice."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from data_query_agent.api.dependencies import (
    get_identity_thread_service,
    get_query_run_trace_service,
)
from data_query_agent.domain.entities.identity import (
    MessageRole,
    QueryThread,
    ThreadMessage,
    ThreadStatus,
    UserMirror,
    UserRole,
)
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

    async def get_user_for_subject(self, *, external_subject: str) -> UserMirror | None:
        if external_subject != "owner":
            return None

        return UserMirror(
            id=self.thread.user_id,
            public_id="user-20",
            external_subject=external_subject,
            role=UserRole.USER,
            display_name=None,
            created_at=_now(),
            updated_at=_now(),
            last_seen_at=_now(),
        )

    async def get_owned_thread(
        self, *, thread_public_id: str, external_subject: str
    ) -> QueryThread | None:
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

    async def get_run_for_user(self, *, run_public_id: str, user_id: int) -> QueryRun | None:
        for run in self.runs:
            if run.public_id == run_public_id and run.user_id == user_id:
                return run
        return None

    async def cancel_run(self, *, run_id: int) -> QueryRun:
        existing = self.runs[run_id - 1]
        canceled = _replace_run(existing, status=RunStatus.CANCELED, finished_at=_now())
        self.runs[run_id - 1] = canceled
        return canceled

    async def retry_run(self, *, run_id: int) -> QueryRun:
        existing = self.runs[run_id - 1]
        retried = _replace_run(
            existing,
            status=RunStatus.RETRYING,
            error_code=None,
            error_message=None,
            started_at=None,
            finished_at=None,
        )
        self.runs[run_id - 1] = retried
        return retried

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


def test_create_local_demo_run_returns_fixture_sql_result_and_chart() -> None:
    client = _client(FakeIdentityThreadService(), FakeRunTraceService())

    response = client.post(
        "/v1/threads/thread-1/runs/local-demo",
        headers={"X-User-Subject": "owner"},
        json={"question": "各渠道销售额排行", "channel": "web"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    data = body["data"]
    assert data["source_status"] == "local_deterministic_fixture"
    assert "不是实时 MySQL" in data["source_note"]
    assert data["fixture_case_id"] == "T2"
    assert data["policy_allowed"] is True
    assert data["generated_sql"] is None
    assert data["query_result"] == {
        "columns": ["channel", "total_sales"],
        "rows": [["app", 70000.0], ["web", 53456.78]],
    }
    assert data["chart"] == {
        "type": "bar",
        "dataset": {"channel": ["app", "web"], "total_sales": [70000.0, 53456.78]},
        "encoding": {"x": "channel", "y": "total_sales"},
    }
    assert [item["node_name"] for item in data["node_trace"]] == [
        "input_validation",
        "intent_classify",
        "schema_retrieval",
        "sql_generate",
        "sql_policy_check",
        "query_execute",
        "result_validate",
        "interpret",
        "persist_audit",
    ]


def test_create_local_demo_run_blocks_cross_subject_thread() -> None:
    client = _client(FakeIdentityThreadService(), FakeRunTraceService())

    response = client.post(
        "/v1/threads/thread-1/runs/local-demo",
        headers={"X-User-Subject": "other"},
        json={"question": "各渠道销售额排行", "channel": "web"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def test_get_run_returns_status_projection_without_sql() -> None:
    identity_service = FakeIdentityThreadService()
    run_service = FakeRunTraceService()
    client = _client(identity_service, run_service)
    created = client.post(
        "/v1/threads/thread-1/runs",
        headers={"X-User-Subject": "owner"},
        json={"question": "What are total sales?"},
    ).json()

    response = client.get(
        f"/v1/runs/{created['data']['run_id']}",
        headers={"X-User-Subject": "owner"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["run_id"] == "run-1"
    assert body["data"]["status"] == "pending"
    assert "sql" not in body["data"]


def test_get_run_blocks_cross_subject_access() -> None:
    identity_service = FakeIdentityThreadService()
    run_service = FakeRunTraceService()
    client = _client(identity_service, run_service)
    client.post(
        "/v1/threads/thread-1/runs",
        headers={"X-User-Subject": "owner"},
        json={"question": "What are total sales?"},
    )

    response = client.get("/v1/runs/run-1", headers={"X-User-Subject": "other"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_cancel_run_marks_owned_run_canceled_without_queue_interrupt() -> None:
    identity_service = FakeIdentityThreadService()
    run_service = FakeRunTraceService()
    client = _client(identity_service, run_service)
    client.post(
        "/v1/threads/thread-1/runs",
        headers={"X-User-Subject": "owner"},
        json={"question": "What are total sales?"},
    )

    response = client.post("/v1/runs/run-1/cancel", headers={"X-User-Subject": "owner"})

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "canceled"
    assert body["data"]["finished_at"] is not None
    assert "sql" not in body["data"]


def test_retry_run_resets_error_projection_without_workflow_execution() -> None:
    identity_service = FakeIdentityThreadService()
    run_service = FakeRunTraceService()
    client = _client(identity_service, run_service)
    client.post(
        "/v1/threads/thread-1/runs",
        headers={"X-User-Subject": "owner"},
        json={"question": "What are total sales?"},
    )
    run_service.runs[0] = _replace_run(
        run_service.runs[0],
        status=RunStatus.FAILED,
        error_code="QUERY_TIMEOUT",
        error_message="query timeout",
        started_at=_now(),
        finished_at=_now(),
    )

    response = client.post("/v1/runs/run-1/retry", headers={"X-User-Subject": "owner"})

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "retrying"
    assert body["data"]["error_code"] is None
    assert body["data"]["error_message"] is None
    assert body["data"]["started_at"] is None
    assert body["data"]["finished_at"] is None


def test_cancel_and_retry_block_cross_subject_access() -> None:
    identity_service = FakeIdentityThreadService()
    run_service = FakeRunTraceService()
    client = _client(identity_service, run_service)
    client.post(
        "/v1/threads/thread-1/runs",
        headers={"X-User-Subject": "owner"},
        json={"question": "What are total sales?"},
    )

    cancel_response = client.post("/v1/runs/run-1/cancel", headers={"X-User-Subject": "other"})
    retry_response = client.post("/v1/runs/run-1/retry", headers={"X-User-Subject": "other"})

    assert cancel_response.status_code == 404
    assert retry_response.status_code == 404


def _replace_run(
    run: QueryRun,
    *,
    status: RunStatus,
    error_code: str | None = None,
    error_message: str | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
) -> QueryRun:
    return QueryRun(
        id=run.id,
        public_id=run.public_id,
        thread_id=run.thread_id,
        user_id=run.user_id,
        status=status,
        question_message_id=run.question_message_id,
        error_code=error_code,
        error_message=error_message,
        started_at=started_at,
        finished_at=finished_at,
        created_at=run.created_at,
        updated_at=_now(),
    )
