"""Unit tests for legal consultation report service."""

from __future__ import annotations

import pytest

from legal_consulting_agent.application.services import LegalDataService, LegalReportService
from legal_consulting_agent.domain.entities.legal_data import ConsultationRecord, UserMirror
from legal_consulting_agent.domain.value_objects.legal_enums import UserRole, UserStatus
from tests.unit.test_legal_data_service import FakeLegalDataRepository


@pytest.mark.asyncio
async def test_build_markdown_report_uses_user_owned_record() -> None:
    repo = FakeLegalDataRepository()
    repo.user = UserMirror(
        id=1,
        public_id="user-public-id",
        email="user@example.test",
        display_name=None,
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    repo.consultation_records = [
        ConsultationRecord(
            id=40,
            public_id="record-public-id",
            user_id=1,
            session_id=10,
            category_id=2,
            question_message_id=11,
            answer_message_id=12,
            summary="Labor contract summary",
            citations=[
                {
                    "source": "Labor Contract Law",
                    "section": "Article 35",
                    "snippet": "Consensus required.",
                }
            ],
            high_risk=False,
            disclaimer="For reference only.",
        )
    ]
    service = LegalReportService(LegalDataService(repo))

    report = await service.build_markdown_report(
        user_public_id="user-public-id",
        record_public_id="record-public-id",
    )

    assert report.record_public_id == "record-public-id"
    assert report.format == "markdown"
    assert "# Legal Consultation Report" in report.content
    assert "Labor contract summary" in report.content
    assert "Labor Contract Law Article 35" in report.content
