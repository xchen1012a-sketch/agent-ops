"""Unit tests for the live streaming endpoint (NL2SQL → execute → interpret)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from data_query_agent.api.dependencies import (
    get_chat_llm_adapter,
    get_data_catalog_service,
    get_identity_thread_service,
    get_prompt_template_service,
    get_query_adapter,
    get_shop_schema_loader,
)
from data_query_agent.application.services.data_catalog_service import DataCatalogService
from data_query_agent.application.services.prompt_template_service import PromptTemplateService
from data_query_agent.domain.entities.identity import MessageRole, ThreadMessage
from data_query_agent.domain.ports.query_adapter import (
    QueryExecutionResult,
)
from data_query_agent.infrastructure.db.fake_query_adapter import FakeReadOnlyQueryAdapter
from data_query_agent.infrastructure.llm.fake_llm_adapter import FakeLlmAdapter
from data_query_agent.main import create_app

_FAKE_SQL = "SELECT SUM(total_amount) AS total_sales FROM wide_orders LIMIT 100"


class _FakeThread:
    """Minimal stand-in; the endpoint only checks ownership, not thread fields."""

    public_id = "thread-1"
    id = 1  # type: ignore[assignment]
    user_id = 1


class FakeIdentityThreadService:
    """Fake identity service tracking messages so tests can assert persistence."""

    def __init__(self) -> None:
        self.messages: list[ThreadMessage] = []

    async def get_owned_thread(self, *, thread_public_id: str, external_subject: str) -> _FakeThread | None:
        if external_subject == "owner" and thread_public_id == "thread-1":
            return _FakeThread()
        return None

    async def list_messages_for_subject(self, *, external_subject: str, thread_public_id: str, limit: int = 20) -> tuple[ThreadMessage, ...]:
        return tuple(self.messages)

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
            public_id=f"m-{len(self.messages) + 1}",
            thread_id=1,
            user_id=1,
            role=role,
            content=content,
            created_at=None,  # type: ignore[arg-type]
        )
        self.messages.append(message)
        return message


def _result_for_fake_sql() -> QueryExecutionResult:
    return QueryExecutionResult(
        columns=("total_sales",),
        rows=((98765.43,),),
        row_count=1,
        field_count=1,
        byte_count=64,
        truncated=False,
    )


def _client(identity_service: FakeIdentityThreadService | None = None) -> TestClient:
    identity_service = identity_service or FakeIdentityThreadService()
    app = create_app()
    app.dependency_overrides[get_identity_thread_service] = lambda: identity_service
    # FakeLlmAdapter ships default nl2sql / interpret_result fixtures so no
    # real DeepSeek key is needed.
    app.dependency_overrides[get_chat_llm_adapter] = lambda: FakeLlmAdapter()
    app.dependency_overrides[get_prompt_template_service] = lambda: PromptTemplateService()
    # Register the SQL the fake LLM emits so the fake adapter returns a row.
    app.dependency_overrides[get_query_adapter] = lambda: FakeReadOnlyQueryAdapter(
        fixtures={_FAKE_SQL: _result_for_fake_sql()}
    )
    app.dependency_overrides[get_data_catalog_service] = lambda: DataCatalogService()

    class _StaticLoader:
        def load_schema_description(self) -> str:
            return "CREATE TABLE `wide_orders` (`total_amount` decimal(12,2));"

    app.dependency_overrides[get_shop_schema_loader] = lambda: _StaticLoader()  # type: ignore[arg-type]
    return TestClient(app)


def test_stream_run_completion_runs_nl2sql_and_emits_answer() -> None:
    identity = FakeIdentityThreadService()
    client = _client(identity)

    response = client.post(
        "/v1/threads/thread-1/runs/stream",
        json={"question": "上周总销售额是多少？"},
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
    # thinking carries the SQL, answer carries the interpretation.
    assert "SELECT SUM(total_amount)" in body
    assert body.index("message.thinking.delta") < body.index("message.delta")
    # assistant message persisted for conversation memory.
    assert any(message.role is MessageRole.ASSISTANT for message in identity.messages)


def test_stream_run_completion_blocks_cross_subject_access() -> None:
    client = _client()

    response = client.post(
        "/v1/threads/thread-1/runs/stream",
        json={"question": "hi"},
        headers={"X-User-Subject": "other"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_stream_run_completion_persists_assistant_for_next_turn() -> None:
    identity = FakeIdentityThreadService()
    client = _client(identity)

    client.post(
        "/v1/threads/thread-1/runs/stream",
        json={"question": "上周总销售额"},
        headers={"X-User-Subject": "owner"},
    )

    # second turn: history now contains the first user question + assistant answer.
    # Both user and assistant turns are persisted so the next prompt sees the
    # same conversation shape as the live endpoint.
    response = client.post(
        "/v1/threads/thread-1/runs/stream",
        json={"question": "那退款率呢？"},
        headers={"X-User-Subject": "owner"},
    )

    assert response.status_code == 200
    assert len(identity.messages) == 4
    assert [message.role for message in identity.messages] == [
        MessageRole.USER,
        MessageRole.ASSISTANT,
        MessageRole.USER,
        MessageRole.ASSISTANT,
    ]


def test_stream_run_completion_degrades_when_query_adapter_lacks_fixture() -> None:
    identity = FakeIdentityThreadService()
    app = create_app()
    app.dependency_overrides[get_identity_thread_service] = lambda: identity
    app.dependency_overrides[get_chat_llm_adapter] = lambda: FakeLlmAdapter()
    app.dependency_overrides[get_prompt_template_service] = lambda: PromptTemplateService()
    # adapter with no fixture for the generated SQL → QueryExecutionError mapping
    app.dependency_overrides[get_query_adapter] = lambda: FakeReadOnlyQueryAdapter()
    app.dependency_overrides[get_data_catalog_service] = lambda: DataCatalogService()

    class _StaticLoader:
        def load_schema_description(self) -> str:
            return "CREATE TABLE `wide_orders` (`total_amount` decimal(12,2));"

    app.dependency_overrides[get_shop_schema_loader] = lambda: _StaticLoader()  # type: ignore[arg-type]

    client = TestClient(app)
    response = client.post(
        "/v1/threads/thread-1/runs/stream",
        json={"question": "上周总销售额"},
        headers={"X-User-Subject": "owner"},
    )

    assert response.status_code == 200
    body = response.text
    # degraded path still emits run.failed-style info in completed payload
    assert "sql_not_registered" in body or "执行状态" in body
