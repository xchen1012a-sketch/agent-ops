"""Legal question answering endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status

from legal_consulting_agent.api.dependencies import (
    CurrentUserPublicIdDep,
    LegalQuestionAnswerServiceDep,
)
from legal_consulting_agent.api.v1.schemas.legal_questions import (
    LegalMessageRef,
    LegalQuestionAnswerEnvelope,
    LegalQuestionAnswerResponse,
    LegalQuestionRequest,
)
from legal_consulting_agent.application.services import LegalQuestionAnswerResult

router = APIRouter()


def _to_question_answer_response(
    result: LegalQuestionAnswerResult,
) -> LegalQuestionAnswerResponse:
    return LegalQuestionAnswerResponse(
        question_message=LegalMessageRef(public_id=result.question_message.public_id),
        answer_message=LegalMessageRef(public_id=result.answer_message.public_id),
        answer=result.answer,
        citations=result.citations,
        high_risk=result.high_risk,
        risk_reason=result.risk_reason,
        category=result.category,
        node_trace=result.node_trace,
    )


@router.post(
    "/sessions/{session_public_id}/questions",
    response_model=LegalQuestionAnswerEnvelope,
    status_code=status.HTTP_201_CREATED,
)
async def answer_question(
    session_public_id: str,
    payload: LegalQuestionRequest,
    user_public_id: CurrentUserPublicIdDep,
    question_answer_service: LegalQuestionAnswerServiceDep,
) -> LegalQuestionAnswerEnvelope:
    """Persist a question and return a deterministic legal answer."""

    result = await question_answer_service.answer_question(
        user_public_id=user_public_id,
        session_public_id=session_public_id,
        question=payload.question,
    )
    return LegalQuestionAnswerEnvelope(data=_to_question_answer_response(result))
