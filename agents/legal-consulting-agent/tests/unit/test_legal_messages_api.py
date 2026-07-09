"""Unit tests for legal session message API contracts."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from legal_consulting_agent.api.dependencies import get_legal_data_service
from legal_consulting_agent.api.error_handlers import register_error_handlers
from legal_consulting_agent.api.v1.router import router as v1_router
from legal_consulting_agent.domain.entities.legal_data import LegalMessage
from legal_consulting_agent.domain.value_objects.legal_enums import MessageRole


class FakeLegalDataService:
    """Fake service for session message API tests."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def list_session_messages(
        self,
        *,
        user_public_id: str,
        session_public_id: str,
        limit: int,
        offset: int,
    ) -> list[LegalMessage]:
        self.calls.append(
            {
                "user_public_id": user_public_id,
                "session_public_id": session_public_id,
                "limit": limit,
                "offset": offset,
            }
        )
        return [
            LegalMessage(
                id=1,
                public_id="question-message-id",
                session_id=10,
                role=MessageRole.USER,
                content="Question",
                citations=None,
                high_risk=False,
                prompt_version=None,
            ),
            LegalMessage(
                id=2,
                public_id="answer-message-id",
                session_id=10,
                role=MessageRole.ASSISTANT,
                content="Answer",
                citations=[],
                high_risk=False,
                prompt_version="deterministic:v1",
            ),
        ]


def build_client(fake_service: FakeLegalDataService) -> TestClient:
    app = FastAPI()
    app.include_router(v1_router, prefix="/v1")
    app.dependency_overrides[get_legal_data_service] = lambda: fake_service
    register_error_handlers(app)
    return TestClient(app)


def test_list_session_messages_returns_paginated_envelope() -> None:
    fake_service = FakeLegalDataService()
    client = build_client(fake_service)

    response = client.get(
        "/v1/sessions/thread-public-id/messages?limit=2&offset=1",
        headers={"x-user-public-id": "user-public-id"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "items": [
                {
                    "public_id": "question-message-id",
                    "role": "user",
                    "content": "Question",
                    "citations": None,
                    "high_risk": False,
                    "prompt_version": None,
                },
                {
                    "public_id": "answer-message-id",
                    "role": "assistant",
                    "content": "Answer",
                    "citations": [],
                    "high_risk": False,
                    "prompt_version": "deterministic:v1",
                },
            ],
            "limit": 2,
            "offset": 1,
        },
        "error": None,
    }
    assert fake_service.calls == [
        {
            "user_public_id": "user-public-id",
            "session_public_id": "thread-public-id",
            "limit": 2,
            "offset": 1,
        }
    ]


def test_list_session_messages_rejects_invalid_limit() -> None:
    client = build_client(FakeLegalDataService())

    response = client.get(
        "/v1/sessions/thread-public-id/messages?limit=101",
        headers={"x-user-public-id": "user-public-id"},
    )

    assert response.status_code == 422
