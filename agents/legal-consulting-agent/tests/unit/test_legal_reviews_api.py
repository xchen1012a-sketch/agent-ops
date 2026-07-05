"""Unit tests for legal high-risk review API contracts."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from legal_consulting_agent.api.dependencies import get_legal_data_service
from legal_consulting_agent.api.error_handlers import register_error_handlers
from legal_consulting_agent.api.v1.router import router as v1_router
from legal_consulting_agent.domain.entities.legal_data import HighRiskReview
from legal_consulting_agent.domain.value_objects.legal_enums import ReviewStatus


class FakeLegalDataService:
    """Fake service for high-risk review API tests."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def create_high_risk_review(
        self,
        *,
        user_public_id: str,
        session_public_id: str,
        message_public_id: str,
        reason: str,
    ) -> HighRiskReview:
        self.calls.append(
            {
                "user_public_id": user_public_id,
                "session_public_id": session_public_id,
                "message_public_id": message_public_id,
                "reason": reason,
            }
        )
        return HighRiskReview(
            id=60,
            message_id=12,
            user_id=1,
            reason=reason,
            status=ReviewStatus.PENDING,
            reviewed_by=None,
            resolution=None,
            reviewed_at=None,
        )

    async def list_high_risk_reviews(
        self,
        *,
        reviewer_public_id: str,
        review_status: ReviewStatus,
        limit: int,
        offset: int,
    ) -> list[HighRiskReview]:
        self.calls.append(
            {
                "reviewer_public_id": reviewer_public_id,
                "review_status": review_status,
                "limit": limit,
                "offset": offset,
            }
        )
        return [
            HighRiskReview(
                id=60,
                message_id=12,
                user_id=1,
                reason="personal_safety",
                status=review_status,
                reviewed_by=None,
                resolution=None,
                reviewed_at=None,
            )
        ]

    async def resolve_high_risk_review(
        self,
        *,
        reviewer_public_id: str,
        review_id: int,
        review_status: ReviewStatus,
        resolution: str,
    ) -> HighRiskReview:
        self.calls.append(
            {
                "reviewer_public_id": reviewer_public_id,
                "review_id": review_id,
                "review_status": review_status,
                "resolution": resolution,
            }
        )
        return HighRiskReview(
            id=review_id,
            message_id=12,
            user_id=1,
            reason="personal_safety",
            status=review_status,
            reviewed_by=99,
            resolution=resolution,
            reviewed_at=None,
        )


def build_client(fake_service: FakeLegalDataService) -> TestClient:
    app = FastAPI()
    app.include_router(v1_router, prefix="/v1")
    app.dependency_overrides[get_legal_data_service] = lambda: fake_service
    register_error_handlers(app)
    return TestClient(app)


def test_create_high_risk_review_returns_success_envelope() -> None:
    fake_service = FakeLegalDataService()
    client = build_client(fake_service)

    response = client.post(
        "/v1/sessions/thread-public-id/messages/answer-message-id/high-risk-review",
        headers={"x-user-public-id": "user-public-id"},
        json={"reason": "personal_safety"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "data": {"id": 60, "reason": "personal_safety", "status": "pending"},
        "error": None,
    }
    assert fake_service.calls == [
        {
            "user_public_id": "user-public-id",
            "session_public_id": "thread-public-id",
            "message_public_id": "answer-message-id",
            "reason": "personal_safety",
        }
    ]


def test_create_high_risk_review_rejects_empty_reason() -> None:
    client = build_client(FakeLegalDataService())

    response = client.post(
        "/v1/sessions/thread-public-id/messages/answer-message-id/high-risk-review",
        headers={"x-user-public-id": "user-public-id"},
        json={"reason": ""},
    )

    assert response.status_code == 422


def test_list_high_risk_reviews_returns_success_envelope() -> None:
    fake_service = FakeLegalDataService()
    client = build_client(fake_service)

    response = client.get(
        "/v1/high-risk-reviews?status=pending&limit=10&offset=2",
        headers={"x-user-public-id": "admin-public-id"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "items": [
                {
                    "id": 60,
                    "message_id": 12,
                    "user_id": 1,
                    "reason": "personal_safety",
                    "status": "pending",
                    "reviewed_by": None,
                    "resolution": None,
                }
            ],
            "limit": 10,
            "offset": 2,
            "status": "pending",
        },
        "error": None,
    }
    assert fake_service.calls == [
        {
            "reviewer_public_id": "admin-public-id",
            "review_status": ReviewStatus.PENDING,
            "limit": 10,
            "offset": 2,
        }
    ]


def test_resolve_high_risk_review_returns_success_envelope() -> None:
    fake_service = FakeLegalDataService()
    client = build_client(fake_service)

    response = client.post(
        "/v1/high-risk-reviews/60/resolution",
        headers={"x-user-public-id": "admin-public-id"},
        json={"status": "resolved", "resolution": "Escalated offline."},
    )

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "id": 60,
            "message_id": 12,
            "user_id": 1,
            "reason": "personal_safety",
            "status": "resolved",
            "reviewed_by": 99,
            "resolution": "Escalated offline.",
        },
        "error": None,
    }


def test_resolve_high_risk_review_rejects_pending_status() -> None:
    client = build_client(FakeLegalDataService())

    response = client.post(
        "/v1/high-risk-reviews/60/resolution",
        headers={"x-user-public-id": "admin-public-id"},
        json={"status": "pending", "resolution": "not allowed"},
    )

    assert response.status_code == 422
