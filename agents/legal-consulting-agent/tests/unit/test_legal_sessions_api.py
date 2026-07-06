"""Unit tests for legal session API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from legal_consulting_agent.api.dependencies import (
    get_legal_data_service,
    get_legal_stream_adapter,
)
from legal_consulting_agent.api.error_handlers import register_error_handlers
from legal_consulting_agent.api.v1.router import router as v1_router
from legal_consulting_agent.domain.entities.legal_data import LegalMessage, LegalSession
from legal_consulting_agent.domain.value_objects.legal_enums import MessageRole, SessionStatus
from legal_consulting_agent.infrastructure.llm.fake_llm_adapter import FakeLlmAdapter


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

    async def list_sessions(
        self,
        *,
        user_public_id: str,
        limit: int,
        offset: int,
    ) -> list[LegalSession]:
        self.calls.append(
            {"op": "list", "user_public_id": user_public_id, "limit": limit, "offset": offset}
        )
        return [
            LegalSession(
                id=10,
                public_id="session-public-id",
                user_id=1,
                category_id=2,
                title="劳动争议咨询",
                status=SessionStatus.ACTIVE,
                last_message_at=datetime(2026, 7, 5, 10, 30, 0),
            )
        ]

    async def list_recent_session_messages(
        self,
        *,
        user_public_id: str,
        session_public_id: str,
        limit: int,
    ) -> list[LegalMessage]:
        self.calls.append(
            {"op": "recent", "session_public_id": session_public_id, "limit": limit}
        )
        return [
            LegalMessage(
                id=1,
                public_id="q1",
                session_id=10,
                role=MessageRole.USER,
                content="劳动合同纠纷咨询问题",
                citations=None,
                high_risk=False,
                prompt_version=None,
            ),
            LegalMessage(
                id=2,
                public_id="a1",
                session_id=10,
                role=MessageRole.ASSISTANT,
                content="这是助手回答。",
                citations=None,
                high_risk=False,
                prompt_version=None,
            ),
        ]

    async def rename_session(
        self,
        *,
        user_public_id: str,
        session_public_id: str,
        title: str,
    ) -> LegalSession:
        self.calls.append(
            {
                "op": "rename",
                "user_public_id": user_public_id,
                "session_public_id": session_public_id,
                "title": title,
            }
        )
        return LegalSession(
            id=10,
            public_id=session_public_id,
            user_id=1,
            category_id=2,
            title=title,
            status=SessionStatus.ACTIVE,
            last_message_at=None,
        )


def build_client(fake_service: FakeLegalDataService) -> TestClient:
    app = FastAPI()
    app.include_router(v1_router, prefix="/v1")
    app.dependency_overrides[get_legal_data_service] = lambda: fake_service
    app.dependency_overrides[get_legal_stream_adapter] = lambda: FakeLlmAdapter()
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


def test_list_legal_sessions_returns_paginated_envelope() -> None:
    fake_service = FakeLegalDataService()
    client = build_client(fake_service)

    response = client.get(
        "/v1/sessions",
        headers={"x-user-public-id": "user-public-id"},
        params={"limit": 20, "offset": 0},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["limit"] == 20
    assert body["data"]["items"][0]["public_id"] == "session-public-id"
    assert body["data"]["items"][0]["title"] == "劳动争议咨询"
    assert fake_service.calls == [
        {"op": "list", "user_public_id": "user-public-id", "limit": 20, "offset": 0}
    ]


def test_list_legal_sessions_requires_user_identity_header() -> None:
    client = build_client(FakeLegalDataService())

    response = client.get("/v1/sessions")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_rename_legal_session_updates_title() -> None:
    fake_service = FakeLegalDataService()
    client = build_client(fake_service)

    response = client.patch(
        "/v1/sessions/session-public-id",
        headers={"x-user-public-id": "user-public-id"},
        json={"title": "  改名后的标题  "},
    )

    assert response.status_code == 200
    assert response.json()["data"]["title"] == "改名后的标题"
    assert fake_service.calls == [
        {
            "op": "rename",
            "user_public_id": "user-public-id",
            "session_public_id": "session-public-id",
            "title": "改名后的标题",
        }
    ]


def test_rename_legal_session_rejects_empty_title() -> None:
    client = build_client(FakeLegalDataService())

    response = client.patch(
        "/v1/sessions/session-public-id",
        headers={"x-user-public-id": "user-public-id"},
        json={"title": "   "},
    )

    assert response.status_code == 422


def test_generate_session_title_names_from_first_exchange() -> None:
    fake_service = FakeLegalDataService()
    client = build_client(fake_service)

    response = client.post(
        "/v1/sessions/session-public-id/title",
        headers={"x-user-public-id": "user-public-id"},
    )

    assert response.status_code == 200
    # FakeLlmAdapter returns no title -> deterministic fallback from first question.
    assert response.json()["data"]["title"] == "劳动合同纠纷咨询问题"
    ops = [call.get("op") for call in fake_service.calls]
    assert ops == ["recent", "rename"]
