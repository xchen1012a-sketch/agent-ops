"""Legal question answering endpoints."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse

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


@router.post("/sessions/{session_public_id}/questions/events")
async def answer_question_events(
    session_public_id: str,
    payload: LegalQuestionRequest,
    user_public_id: CurrentUserPublicIdDep,
    question_answer_service: LegalQuestionAnswerServiceDep,
) -> StreamingResponse:
    """Return deterministic question-answer progress as SSE events."""

    return StreamingResponse(
        _stream_question_answer_events(
            session_public_id=session_public_id,
            payload=payload,
            user_public_id=user_public_id,
            question_answer_service=question_answer_service,
        ),
        media_type="text/event-stream",
    )


async def _stream_question_answer_events(
    *,
    session_public_id: str,
    payload: LegalQuestionRequest,
    user_public_id: str,
    question_answer_service: LegalQuestionAnswerServiceDep,
) -> AsyncIterator[str]:
    yield _sse_event(
        "started",
        {
            "session_public_id": session_public_id,
        },
    )
    result = await question_answer_service.answer_question(
        user_public_id=user_public_id,
        session_public_id=session_public_id,
        question=payload.question,
    )
    for chunk in _chunk_answer(result.answer):
        yield _sse_event("message.delta", {"delta": chunk})
        await asyncio.sleep(0)
    yield _sse_event(
        "completed",
        _to_question_answer_response(result).model_dump(mode="json"),
    )


def _chunk_answer(answer: str, *, chunk_size: int = 24) -> list[str]:
    """Split a persisted answer into small SSE deltas for MVP streaming display."""

    if not answer:
        return []
    return [answer[index : index + chunk_size] for index in range(0, len(answer), chunk_size)]


def _sse_event(event: str, data: dict[str, object]) -> str:
    return (
        f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, separators=(',', ':'))}\n\n"
    )
