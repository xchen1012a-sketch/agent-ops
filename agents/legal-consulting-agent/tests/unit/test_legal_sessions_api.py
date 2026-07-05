"""Unit tests for legal session API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from legal_consulting_agent.api.dependencies import get_legal_data_service
from legal_consulting_agent.api.error_handlers import register_error_handlers
from legal_consulting_agent.api.v1.router import router as v1_router
from legal_consulting_agent.domain.entities.legal_data import LegalSession
from legal_consulting_agent.domain.value_objects.legal_enums import SessionStatus


class FakeLegalDataService:
    """Fake service for API contract tests."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def create_session(
        self,
        *,
        user_public_id: str,
        category_code: str,
        title: str | None,
    ) -> LegalSession:
        self.calls.append(
            {
                "user_public_id": user_public_id,
                "category_code": category_code,
                "title": title,
            }
        )
        return LegalSession(
            id=10,
            public_id="session-public-id",
            user_id=1,
            category_id=2,
            title=title,
            status=SessionStatus.ACTIVE,
            last_message_at=datetime(2026, 7, 5, 10, 30, 0),
        )


def build_client(fake_service: FakeLegalDataService) -> TestClient:
    app = FastAPI()
    app.include_router(v1_router, prefix="/v1")
    app.dependency_overrides[get_legal_data_service] = lambda: fake_service
    register_error_handlers(app)
    return TestClient(app)


def test_create_legal_session_returns_success_envelope() -> None:
    fake_service = FakeLegalDataService()
    client = build_client(fake_service)

    response = client.post(
        "/v1/sessions",
        headers={"x-user-public-id": "user-public-id"},
        json={"category_code": "civil_labor", "title": "Labor dispute"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "data": {
            "public_id": "session-public-id",
            "title": "Labor dispute",
            "status": "active",
            "last_message_at": "2026-07-05T10:30:00",
        },
        "error": None,
    }
    assert fake_service.calls == [
        {
            "user_public_id": "user-public-id",
            "category_code": "civil_labor",
            "title": "Labor dispute",
        }
    ]


def test_create_legal_session_requires_user_identity_header() -> None:
    client = build_client(FakeLegalDataService())

    response = client.post(
        "/v1/sessions",
        json={"category_code": "civil_labor", "title": "Labor dispute"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_create_legal_session_rejects_invalid_category_code() -> None:
    client = build_client(FakeLegalDataService())

    response = client.post(
        "/v1/sessions",
        headers={"x-user-public-id": "user-public-id"},
        json={"category_code": "../outside", "title": "Labor dispute"},
    )

    assert response.status_code == 422
