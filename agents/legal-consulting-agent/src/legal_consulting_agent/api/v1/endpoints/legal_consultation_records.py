"""Legal consultation record history endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from legal_consulting_agent.api.dependencies import CurrentUserPublicIdDep, LegalDataServiceDep
from legal_consulting_agent.api.v1.schemas.legal_consultation_records import (
    LegalConsultationRecordListData,
    LegalConsultationRecordListEnvelope,
    LegalConsultationRecordResponse,
)
from legal_consulting_agent.domain.entities.legal_data import ConsultationRecord

router = APIRouter()


def _to_record_response(record: ConsultationRecord) -> LegalConsultationRecordResponse:
    return LegalConsultationRecordResponse(
        public_id=record.public_id,
        summary=record.summary,
        citations=record.citations,
        high_risk=record.high_risk,
        disclaimer=record.disclaimer,
    )


@router.get(
    "/consultation-records",
    response_model=LegalConsultationRecordListEnvelope,
)
async def list_consultation_records(
    user_public_id: CurrentUserPublicIdDep,
    legal_data_service: LegalDataServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    query: Annotated[str | None, Query(alias="q", min_length=1, max_length=200)] = None,
) -> LegalConsultationRecordListEnvelope:
    """List user-owned consultation records for history lookup."""

    records = await legal_data_service.list_consultation_records(
        user_public_id=user_public_id,
        limit=limit,
        offset=offset,
        query=query,
    )
    return LegalConsultationRecordListEnvelope(
        data=LegalConsultationRecordListData(
            items=[_to_record_response(record) for record in records],
            limit=limit,
            offset=offset,
            query=query,
        )
    )
