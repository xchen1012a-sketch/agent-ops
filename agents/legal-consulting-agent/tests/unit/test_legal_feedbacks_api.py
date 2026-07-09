"""Unit tests for legal feedback API contracts."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from legal_consulting_agent.api.dependencies import get_legal_data_service
from legal_consulting_agent.api.error_handlers import register_error_handlers
from legal_consulting_agent.api.v1.router import router as v1_router
from legal_consulting_agent.domain.entities.legal_data import Feedback


class FakeLegalDataService:
    """Fake service for feedback API tests."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def create_feedback(
        self,
        *,
        user_public_id: str,
        session_public_id: str,
        message_public_id: str,
        rating: int,
        comment: str | None,
    ) -> Feedback:
        self.calls.append(
            {
                "user_public_id": user_public_id,
                "session_public_id": session_public_id,
                "message_public_id": message_public_id,
                "rating": rating,
                "comment": comment,
            }
        )
        return Feedback(id=50, message_id=12, user_id=1, rating=rating, comment=comment)


def build_client(fake_service: FakeLegalDataService) -> TestClient:
    app = FastAPI()
    app.include_router(v1_router, prefix="/v1")
    app.dependency_overrides[get_legal_data_service] = lambda: fake_service
    register_error_handlers(app)
    return TestClient(app)


def test_create_feedback_returns_success_envelope() -> None:
    fake_service = FakeLegalDataService()
    client = build_client(fake_service)

    response = client.post(
        "/v1/sessions/thread-public-id/messages/answer-message-id/feedback",
        headers={"x-user-public-id": "user-public-id"},
        json={"rating": 5, "comment": "Helpful"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "data": {"id": 50, "rating": 5, "comment": "Helpful"},
        "error": None,
    }
    assert fake_service.calls == [
        {
            "user_public_id": "user-public-id",
            "session_public_id": "thread-public-id",
            "message_public_id": "answer-message-id",
            "rating": 5,
            "comment": "Helpful",
        }
    ]


def test_create_feedback_rejects_invalid_rating() -> None:
    client = build_client(FakeLegalDataService())

    response = client.post(
        "/v1/sessions/thread-public-id/messages/answer-message-id/feedback",
        headers={"x-user-public-id": "user-public-id"},
        json={"rating": 6, "comment": None},
    )

    assert response.status_code == 422
