"""Unit tests for legal question API contracts."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.testclient import TestClient

from legal_consulting_agent.api.dependencies import (
    get_legal_question_answer_service,
    get_legal_stream_adapter,
)
from legal_consulting_agent.api.error_handlers import register_error_handlers
from legal_consulting_agent.api.v1.router import router as v1_router
from legal_consulting_agent.application.services import LegalQuestionAnswerResult
from legal_consulting_agent.domain.entities.legal_data import LegalMessage
from legal_consulting_agent.domain.ports.llm_adapter import LlmCompletionRequest, LlmStreamChunk
from legal_consulting_agent.domain.value_objects.legal_enums import MessageRole
from legal_consulting_agent.infrastructure.llm.fake_llm_adapter import FakeLlmAdapter


class FakeQuestionAnswerService:
    """Fake question-answer service for API contract tests."""

    def __init__(self, context_messages: list[dict[str, str]] | None = None) -> None:
        self.calls: list[dict[str, str]] = []
        self.context_messages = context_messages or []

    async def answer_question(
        self,
        *,
        user_public_id: str,
        session_public_id: str,
        question: str,
    ) -> LegalQuestionAnswerResult:
        self.calls.append(
            {
                "user_public_id": user_public_id,
                "session_public_id": session_public_id,
                "question": question,
            }
        )
        return LegalQuestionAnswerResult(
            question_message=LegalMessage(
                id=1,
                public_id="question-message-id",
                session_id=10,
                role=MessageRole.USER,
                content=question,
                citations=None,
                high_risk=False,
                prompt_version=None,
            ),
            answer_message=LegalMessage(
                id=2,
                public_id="answer-message-id",
                session_id=10,
                role=MessageRole.ASSISTANT,
                content="Mock legal answer",
                citations=[],
                high_risk=False,
                prompt_version="deterministic:v1",
            ),
            answer="Mock legal answer",
            context_messages=self.context_messages,
            citations=[],
            high_risk=False,
            risk_reason=None,
            category="other",
            node_trace=["input_safety", "classification"],
        )

    async def replace_answer_message_content(
        self,
        *,
        user_public_id: str,
        session_public_id: str,
        answer_message_public_id: str,
        content: str,
        prompt_version: str | None = None,
    ) -> LegalMessage:
        self.calls.append(
            {
                "user_public_id": user_public_id,
                "session_public_id": session_public_id,
                "question": f"replace:{content}",
            }
        )
        return LegalMessage(
            id=2,
            public_id=answer_message_public_id,
            session_id=10,
            role=MessageRole.ASSISTANT,
            content=content,
            citations=[],
            high_risk=False,
            prompt_version=prompt_version,
        )


class AnswerOnlyAdapter(FakeLlmAdapter):
    prefer_stream_answer = True

    async def stream(self, request: LlmCompletionRequest) -> AsyncIterator[LlmStreamChunk]:
        self.requests.append(request)
        yield LlmStreamChunk(kind="answer", text="Live ")
        yield LlmStreamChunk(kind="answer", text="legal answer")


class LongAnswerAdapter(FakeLlmAdapter):
    prefer_stream_answer = True

    async def stream(self, request: LlmCompletionRequest) -> AsyncIterator[LlmStreamChunk]:
        self.requests.append(request)
        yield LlmStreamChunk(kind="answer", text="简洁回答：" + "要点" * 400)


def build_client(fake_service: FakeQuestionAnswerService) -> TestClient:
    app = FastAPI()
    app.include_router(v1_router, prefix="/v1")
    app.dependency_overrides[get_legal_question_answer_service] = lambda: fake_service
    # Force the mock adapter so the SSE test needs no DB-backed config lookup.
    app.dependency_overrides[get_legal_stream_adapter] = lambda: FakeLlmAdapter()
    register_error_handlers(app)
    return TestClient(app)


def test_answer_question_returns_success_envelope() -> None:
    fake_service = FakeQuestionAnswerService()
    client = build_client(fake_service)

    response = client.post(
        "/v1/sessions/thread-public-id/questions",
        headers={"x-user-public-id": "user-public-id"},
        json={"question": "Can my employer transfer me?"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "data": {
            "question_message": {"public_id": "question-message-id"},
            "answer_message": {"public_id": "answer-message-id"},
            "answer": "Mock legal answer",
            "citations": [],
            "high_risk": False,
            "risk_reason": None,
            "category": "other",
            "node_trace": ["input_safety", "classification"],
        },
        "error": None,
    }
    assert fake_service.calls == [
        {
            "user_public_id": "user-public-id",
            "session_public_id": "thread-public-id",
            "question": "Can my employer transfer me?",
        }
    ]


def test_answer_question_rejects_empty_question() -> None:
    client = build_client(FakeQuestionAnswerService())

    response = client.post(
        "/v1/sessions/thread-public-id/questions",
        headers={"x-user-public-id": "user-public-id"},
        json={"question": ""},
    )

    assert response.status_code == 422


def test_answer_question_events_streams_thinking_then_answer_contract() -> None:
    fake_service = FakeQuestionAnswerService()
    client = build_client(fake_service)

    response = client.post(
        "/v1/sessions/thread-public-id/questions/events",
        headers={"x-user-public-id": "user-public-id"},
        json={"question": "Can my employer transfer me?"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert "event: run.started" in body
    assert "event: message.thinking.delta" in body
    assert "event: message.thinking.completed" in body
    assert "event: message.delta" in body
    assert '"delta":"Mock legal answer"' in body
    assert "event: message.completed" in body
    # The terminal event still carries the legal DTO for the frontend.
    assert '"answer":"Mock legal answer"' in body
    # Thinking must be streamed before the answer body starts.
    assert body.index("message.thinking.delta") < body.index("message.delta")


def test_answer_question_events_streams_live_answer_when_adapter_provides_answer() -> None:
    fake_service = FakeQuestionAnswerService()
    adapter = AnswerOnlyAdapter()
    app = FastAPI()
    app.include_router(v1_router, prefix="/v1")
    app.dependency_overrides[get_legal_question_answer_service] = lambda: fake_service
    app.dependency_overrides[get_legal_stream_adapter] = lambda: adapter
    register_error_handlers(app)
    client = TestClient(app)

    response = client.post(
        "/v1/sessions/thread-public-id/questions/events",
        headers={"x-user-public-id": "user-public-id"},
        json={"question": "Can my employer transfer me?"},
    )

    assert response.status_code == 200
    body = response.text
    assert "event: message.thinking.delta" in body
    assert '"delta":"Live "' in body
    assert '"delta":"legal answer"' in body
    assert '"delta":"Mock legal answer"' not in body
    assert {
        "user_public_id": "user-public-id",
        "session_public_id": "thread-public-id",
        "question": "replace:Live legal answer",
    } in fake_service.calls


def test_answer_question_events_passes_recent_context_to_stream_adapter() -> None:
    fake_service = FakeQuestionAnswerService(
        context_messages=[
            {"role": "user", "content": "上一轮我说公司拖欠我两个月工资。"},
            {"role": "assistant", "content": "上一轮建议先保留劳动合同和工资流水。"},
        ]
    )
    adapter = AnswerOnlyAdapter()
    app = FastAPI()
    app.include_router(v1_router, prefix="/v1")
    app.dependency_overrides[get_legal_question_answer_service] = lambda: fake_service
    app.dependency_overrides[get_legal_stream_adapter] = lambda: adapter
    register_error_handlers(app)
    client = TestClient(app)

    response = client.post(
        "/v1/sessions/thread-public-id/questions/events",
        headers={"x-user-public-id": "user-public-id"},
        json={"question": "那我下一步应该怎么做？"},
    )

    assert response.status_code == 200
    assert len(adapter.requests) == 1
    rendered_prompt = adapter.requests[0].rendered_prompt
    assert "上一轮我说公司拖欠我两个月工资" in rendered_prompt
    assert "上一轮建议先保留劳动合同和工资流水" in rendered_prompt
    assert "那我下一步应该怎么做？" in rendered_prompt
    assert "先给结论，再给最多 3 个关键要点" in rendered_prompt
    assert "总长度优先控制在 300 字以内" in rendered_prompt


def test_answer_question_events_caps_overlong_live_answer() -> None:
    fake_service = FakeQuestionAnswerService()
    adapter = LongAnswerAdapter()
    app = FastAPI()
    app.include_router(v1_router, prefix="/v1")
    app.dependency_overrides[get_legal_question_answer_service] = lambda: fake_service
    app.dependency_overrides[get_legal_stream_adapter] = lambda: adapter
    register_error_handlers(app)
    client = TestClient(app)

    response = client.post(
        "/v1/sessions/thread-public-id/questions/events",
        headers={"x-user-public-id": "user-public-id"},
        json={"question": "公司拖欠工资，我下一步怎么做？"},
    )

    assert response.status_code == 200
    body = response.text
    assert "需要我再展开哪一部分？" in body
    replace_calls = [call for call in fake_service.calls if call["question"].startswith("replace:")]
    assert len(replace_calls) == 1
    persisted_answer = replace_calls[0]["question"].removeprefix("replace:")
    assert len(persisted_answer) <= 720
