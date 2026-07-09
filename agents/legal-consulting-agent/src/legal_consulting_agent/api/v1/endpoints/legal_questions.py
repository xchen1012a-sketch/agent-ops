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
_STREAMED_PROMPT_VERSION = "deepseek:stream-v1"
_ANSWER_CHUNK_SIZE = 24
_THINKING_CHUNK_SIZE = 16
_STREAM_MAX_ANSWER_CHARS = 700
_STREAM_TRUNCATION_SUFFIX = "\n\n需要我再展开哪一部分？"
_STREAM_CONTEXT_MESSAGE_LIMIT = 8
_STREAM_CONTEXT_MESSAGE_CHAR_LIMIT = 1200
_ROLE_LABELS = {
    "user": "用户",
    "assistant": "法律助手",
    "system": "系统",
}
_CLAUDE_STYLE_RESPONSE_RULES = (
    "输出风格要求：完全对标 Claude 的简洁风格。"
    "先给结论，再给最多 3 个关键要点；每点一两句。"
    "不要写长篇背景、不要堆法条、不要重复免责声明。"
    "信息不足时只问 1-3 个最关键补充问题。"
    "总长度优先控制在 300 字以内，复杂问题最多 600 字。"
)


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
        context_messages=result.context_messages,
        answer=result.answer,
        question_answer_service=question_answer_service,
        user_public_id=user_public_id,
        session_public_id=session_public_id,
        answer_message_public_id=result.answer_message.public_id,
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
    context_messages: list[dict[str, str]],
    answer: str,
    question_answer_service: LegalQuestionAnswerServiceDep,
    user_public_id: str,
    session_public_id: str,
    answer_message_public_id: str,
) -> AsyncIterator[LlmStreamChunk]:
    """Yield progress thinking, then live answer chunks with deterministic fallback."""

    request = LlmCompletionRequest(
        prompt_name=_STREAM_PROMPT_NAME,
        version=_STREAM_PROMPT_VERSION,
        rendered_prompt=_render_stream_prompt(
            question=question,
            context_messages=context_messages,
        ),
    )
    for piece in _chunk_text(_progress_thinking(question), chunk_size=_THINKING_CHUNK_SIZE):
        yield LlmStreamChunk(kind="thinking", text=piece)

    prefer_stream_answer = bool(getattr(adapter, "prefer_stream_answer", True))
    streamed_answer_parts: list[str] = []
    streamed_answer_length = 0
    async for chunk in adapter.stream(request):
        if chunk.kind == "thinking":
            yield chunk
            continue
        if chunk.kind == "answer" and prefer_stream_answer:
            remaining = _STREAM_MAX_ANSWER_CHARS - streamed_answer_length
            if remaining <= 0:
                break
            text = chunk.text
            if len(text) > remaining:
                text = text[:remaining].rstrip() + _STREAM_TRUNCATION_SUFFIX
            streamed_answer_parts.append(text)
            streamed_answer_length += len(text)
            yield LlmStreamChunk(kind="answer", text=text)
            if text.endswith(_STREAM_TRUNCATION_SUFFIX):
                break
            continue

    if streamed_answer_parts:
        streamed_answer = "".join(streamed_answer_parts).strip()
        if streamed_answer:
            await question_answer_service.replace_answer_message_content(
                user_public_id=user_public_id,
                session_public_id=session_public_id,
                answer_message_public_id=answer_message_public_id,
                content=streamed_answer,
                prompt_version=_STREAMED_PROMPT_VERSION,
            )
        return

    for piece in _chunk_answer(answer):
        yield LlmStreamChunk(kind="answer", text=piece)


def _render_stream_prompt(*, question: str, context_messages: list[dict[str, str]]) -> str:
    """Render a bounded multi-turn prompt for the live legal answer stream."""
    history = []
    for message in context_messages[-_STREAM_CONTEXT_MESSAGE_LIMIT:]:
        content = message.get("content", "").strip()
        if not content:
            continue
        role = _ROLE_LABELS.get(message.get("role", ""), "消息")
        history.append(
            f"{role}: {content[:_STREAM_CONTEXT_MESSAGE_CHAR_LIMIT]}"
        )

    if not history:
        return (
            "你是法律咨询助手。请用中文回答用户问题，先说明需要结合事实和适用法律判断，"
            "再给出可执行建议。\n"
            f"{_CLAUDE_STYLE_RESPONSE_RULES}\n\n"
            f"当前问题：{question}"
        )

    return (
        "你是法律咨询助手。请结合历史对话上下文和当前问题回答，保持中文、具体、可执行。"
        "如果当前问题依赖上一轮事实，必须沿用历史事实，不要当作全新问题。\n"
        f"{_CLAUDE_STYLE_RESPONSE_RULES}\n\n"
        "历史对话：\n"
        + "\n".join(history)
        + "\n\n"
        f"当前问题：{question}"
    )


def _progress_thinking(question: str) -> str:
    """Return a safe progress summary for the public thinking panel."""
    normalized = question.strip() or "当前问题"
    return (
        f"正在识别问题：{normalized}\n"
        "梳理法律关系、关键事实和风险点。\n"
        "检查可用知识来源，并组织可执行的处理建议。"
    )


def _chunk_answer(answer: str, *, chunk_size: int = _ANSWER_CHUNK_SIZE) -> list[str]:
    """Split a persisted answer into small SSE deltas for MVP streaming display."""

    if not answer:
        return []
    return [answer[index : index + chunk_size] for index in range(0, len(answer), chunk_size)]


def _chunk_text(text: str, *, chunk_size: int) -> list[str]:
    """Split display text into small streaming deltas."""
    if not text:
        return []
    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]
