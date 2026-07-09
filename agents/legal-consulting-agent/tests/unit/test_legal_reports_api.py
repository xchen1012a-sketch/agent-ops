"""Unit tests for legal report API contracts."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from legal_consulting_agent.api.dependencies import get_legal_report_service
from legal_consulting_agent.api.error_handlers import register_error_handlers
from legal_consulting_agent.api.v1.router import router as v1_router
from legal_consulting_agent.application.services import LegalConsultationReport


class FakeLegalReportService:
    """Fake report service for API contract tests."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def build_markdown_report(
        self,
        *,
        user_public_id: str,
        record_public_id: str,
    ) -> LegalConsultationReport:
        self.calls.append({"user_public_id": user_public_id, "record_public_id": record_public_id})
        return LegalConsultationReport(
            record_public_id=record_public_id,
            format="markdown",
            content="# Legal Consultation Report\n\nReport body",
        )


def build_client(fake_service: FakeLegalReportService) -> TestClient:
    app = FastAPI()
    app.include_router(v1_router, prefix="/v1")
    app.dependency_overrides[get_legal_report_service] = lambda: fake_service
    register_error_handlers(app)
    return TestClient(app)


def test_export_consultation_report_returns_markdown_envelope() -> None:
    fake_service = FakeLegalReportService()
    client = build_client(fake_service)

    response = client.get(
        "/v1/consultation-records/record-public-id/report",
        headers={"x-user-public-id": "user-public-id"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "record_public_id": "record-public-id",
            "format": "markdown",
            "content": "# Legal Consultation Report\n\nReport body",
        },
        "error": None,
    }
    assert fake_service.calls == [
        {"user_public_id": "user-public-id", "record_public_id": "record-public-id"}
    ]
