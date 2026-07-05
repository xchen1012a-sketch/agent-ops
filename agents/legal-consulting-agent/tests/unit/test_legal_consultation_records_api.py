"""Unit tests for legal consultation record history API contracts."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from legal_consulting_agent.api.dependencies import get_legal_data_service
from legal_consulting_agent.api.error_handlers import register_error_handlers
from legal_consulting_agent.api.v1.router import router as v1_router
from legal_consulting_agent.domain.entities.legal_data import ConsultationRecord


class FakeLegalDataService:
    """Fake service for consultation record API contract tests."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def list_consultation_records(
        self,
        *,
        user_public_id: str,
        limit: int,
        offset: int,
        query: str | None,
    ) -> list[ConsultationRecord]:
        self.calls.append(
            {
                "user_public_id": user_public_id,
                "limit": limit,
                "offset": offset,
                "query": query,
            }
        )
        return [
            ConsultationRecord(
                id=40,
                public_id="record-public-id",
                user_id=1,
                session_id=10,
                category_id=2,
                question_message_id=11,
                answer_message_id=12,
                summary="labor contract role change",
                citations=[{"source": "labor-contract-law"}],
                high_risk=False,
                disclaimer="reference only",
            )
        ]


def build_client(fake_service: FakeLegalDataService) -> TestClient:
    app = FastAPI()
    app.include_router(v1_router, prefix="/v1")
    app.dependency_overrides[get_legal_data_service] = lambda: fake_service
    register_error_handlers(app)
    return TestClient(app)


def test_list_consultation_records_returns_success_envelope() -> None:
    fake_service = FakeLegalDataService()
    client = build_client(fake_service)

    response = client.get(
        "/v1/consultation-records?limit=10&offset=5&q=labor",
        headers={"x-user-public-id": "user-public-id"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "items": [
                {
                    "public_id": "record-public-id",
                    "summary": "labor contract role change",
                    "citations": [{"source": "labor-contract-law"}],
                    "high_risk": False,
                    "disclaimer": "reference only",
                }
            ],
            "limit": 10,
            "offset": 5,
            "query": "labor",
        },
        "error": None,
    }
    assert fake_service.calls == [
        {
            "user_public_id": "user-public-id",
            "limit": 10,
            "offset": 5,
            "query": "labor",
        }
    ]


def test_list_consultation_records_requires_user_identity_header() -> None:
    client = build_client(FakeLegalDataService())

    response = client.get("/v1/consultation-records")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_list_consultation_records_rejects_invalid_limit() -> None:
    client = build_client(FakeLegalDataService())

    response = client.get(
        "/v1/consultation-records?limit=101",
        headers={"x-user-public-id": "user-public-id"},
    )

    assert response.status_code == 422
