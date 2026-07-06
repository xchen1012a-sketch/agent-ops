"""Legal question answering endpoints."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse

from legal_consulting_agent.api.dependencies import (
    CurrentUserPublicIdDep,
    LegalQuestionAnswerServiceDep,
    LegalStreamAdapterDep,
)
from legal_consulting_agent.api.v1.schemas.legal_questions import (
    LegalMessageRef,
    LegalQuestionAnswerEnvelope,
    LegalQuestionAnswerResponse,
    LegalQuestionRequest,
)
from legal_consulting_agent.application.services import LegalQuestionAnswerResult
from legal_consulting_agent.domain.ports.llm_adapter import (
    LlmAdapter,
    LlmCompletionRequest,
    LlmStreamChunk,
)
from legal_consulting_agent.infrastructure.sse import iter_llm_sse

router = APIRouter()

_STREAM_PROMPT_NAME = "legal_answer"
_STREAM_PROMPT_VERSION = "v1"
_ANSWER_CHUNK_SIZE = 24


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
    stream_adapter: LegalStreamAdapterDep,
) -> StreamingResponse:
    """Stream the deterministic answer with a thinking channel via the shared SSE layer."""

    return StreamingResponse(
        _stream_question_answer_events(
            session_public_id=session_public_id,
            payload=payload,
            user_public_id=user_public_id,
            question_answer_service=question_answer_service,
            stream_adapter=stream_adapter,
        ),
        media_type="text/event-stream",
    )


async def _stream_question_answer_events(
    *,
    session_public_id: str,
    payload: LegalQuestionRequest,
    user_public_id: str,
    question_answer_service: LegalQuestionAnswerServiceDep,
    stream_adapter: LlmAdapter,
) -> AsyncIterator[str]:
    result = await question_answer_service.answer_question(
        user_public_id=user_public_id,
        session_public_id=session_public_id,
        question=payload.question,
    )
    response = _to_question_answer_response(result)
    chunks = _thinking_then_answer(
        stream_adapter,
        question=payload.question,
        answer=result.answer,
    )
    async for frame in iter_llm_sse(
        chunks,
        run_id=result.answer_message.public_id,
        completed_extra=response.model_dump(mode="json"),
    ):
        yield frame


async def _thinking_then_answer(
    adapter: LlmAdapter,
    *,
    question: str,
    answer: str,
) -> AsyncIterator[LlmStreamChunk]:
    """Yield adapter-generated thinking, then the deterministic answer in deltas."""

    request = LlmCompletionRequest(
        prompt_name=_STREAM_PROMPT_NAME,
        version=_STREAM_PROMPT_VERSION,
        rendered_prompt=question,
    )
    async for chunk in adapter.stream(request):
        if chunk.kind == "thinking":
            yield chunk
    for piece in _chunk_answer(answer):
        yield LlmStreamChunk(kind="answer", text=piece)


def _chunk_answer(answer: str, *, chunk_size: int = _ANSWER_CHUNK_SIZE) -> list[str]:
    """Split a persisted answer into small SSE deltas for MVP streaming display."""

    if not answer:
        return []
    return [answer[index : index + chunk_size] for index in range(0, len(answer), chunk_size)]
