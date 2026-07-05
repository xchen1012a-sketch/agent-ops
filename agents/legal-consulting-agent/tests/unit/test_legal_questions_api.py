"""Unit tests for legal question API contracts."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from legal_consulting_agent.api.dependencies import get_legal_question_answer_service
from legal_consulting_agent.api.error_handlers import register_error_handlers
from legal_consulting_agent.api.v1.router import router as v1_router
from legal_consulting_agent.application.services import LegalQuestionAnswerResult
from legal_consulting_agent.domain.entities.legal_data import LegalMessage
from legal_consulting_agent.domain.value_objects.legal_enums import MessageRole


class FakeQuestionAnswerService:
    """Fake question-answer service for API contract tests."""

    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

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
            citations=[],
            high_risk=False,
            risk_reason=None,
            category="other",
            node_trace=["input_safety", "classification"],
        )


def build_client(fake_service: FakeQuestionAnswerService) -> TestClient:
    app = FastAPI()
    app.include_router(v1_router, prefix="/v1")
    app.dependency_overrides[get_legal_question_answer_service] = lambda: fake_service
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


def test_answer_question_events_returns_sse_started_delta_and_completed() -> None:
    fake_service = FakeQuestionAnswerService()
    client = build_client(fake_service)

    response = client.post(
        "/v1/sessions/thread-public-id/questions/events",
        headers={"x-user-public-id": "user-public-id"},
        json={"question": "Can my employer transfer me?"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: started" in response.text
    assert "event: message.delta" in response.text
    assert '"delta":"Mock legal answer"' in response.text
    assert "event: completed" in response.text
    assert '"answer":"Mock legal answer"' in response.text
