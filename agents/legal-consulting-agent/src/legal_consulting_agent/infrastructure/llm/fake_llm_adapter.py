"""Deterministic in-memory LLM adapter (STREAM-100).

Provides mock thinking chunks so the legal question stream can render the
Claude.ai-style reasoning panel while the deterministic answer keeps coming from
the persisted question-answer service. Real DeepSeek streaming lands in 阶段5.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from legal_consulting_agent.domain.ports.llm_adapter import (
    LlmAdapter,
    LlmCompletionRequest,
    LlmCompletionResponse,
    LlmStreamChunk,
)

_STREAM_CHUNK_SIZE = 8


class FakeLlmAdapter(LlmAdapter):
    """Deterministic in-memory LLM adapter that never calls external models."""

    def __init__(self, fixtures: dict[tuple[str, str], str] | None = None) -> None:
        self._fixtures = fixtures or {}
        self.requests: list[LlmCompletionRequest] = []

    async def complete(self, request: LlmCompletionRequest) -> LlmCompletionResponse:
        """Return a fixture or an empty deterministic response."""
        self.requests.append(request)
        fixture = self._fixtures.get((request.prompt_name, request.version))
        return LlmCompletionResponse(content=fixture or "")

    async def stream(self, request: LlmCompletionRequest) -> AsyncIterator[LlmStreamChunk]:
        """Yield deterministic thinking then answer chunks for local streaming demos."""
        self.requests.append(request)
        for piece in _chunk_text(_default_thinking(request)):
            yield LlmStreamChunk(kind="thinking", text=piece)
        for piece in _chunk_text(_default_answer(request)):
            yield LlmStreamChunk(kind="answer", text=piece)


def _default_thinking(request: LlmCompletionRequest) -> str:
    return (
        f"先理解咨询问题：{request.rendered_prompt.strip()}。"
        "识别涉及的法律关系与关键事实，规划回答结构，再组织答复与依据。"
    )


def _default_answer(request: LlmCompletionRequest) -> str:
    return (
        "这是一段用于本地演示的确定性法律答复占位，用于验证思考展示与正文流式渲染链路。"
    )


def _chunk_text(text: str, *, chunk_size: int = _STREAM_CHUNK_SIZE) -> list[str]:
    """Split text into small deltas for a typewriter-style streaming display."""
    if not text:
        return []
    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]
