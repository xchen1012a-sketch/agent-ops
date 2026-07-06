"""Fake LLM adapter for prompt-backed workflow tests."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from data_query_agent.domain.ports.llm_adapter import (
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
        """Return a fixture or a deterministic response for known prompt names."""
        self.requests.append(request)
        fixture = self._fixtures.get((request.prompt_name, request.version))
        if fixture is not None:
            return LlmCompletionResponse(content=fixture)
        return LlmCompletionResponse(content=_default_content(request))

    async def stream(self, request: LlmCompletionRequest) -> AsyncIterator[LlmStreamChunk]:
        """Yield deterministic thinking then answer chunks for local streaming demos."""
        self.requests.append(request)
        for piece in _chunk_text(_default_thinking(request)):
            yield LlmStreamChunk(kind="thinking", text=piece)
        for piece in _chunk_text(_default_answer(request)):
            yield LlmStreamChunk(kind="answer", text=piece)


def _default_thinking(request: LlmCompletionRequest) -> str:
    return (
        f"先理解问题：{request.rendered_prompt.strip()}。"
        "拆解为查询目标与约束，规划最小查询路径，再组织回答。"
    )


def _default_answer(request: LlmCompletionRequest) -> str:
    return (
        "### 回答\n\n"
        f"针对「{request.rendered_prompt.strip()}」，这是一段用于本地演示的确定性回答，"
        "用于验证思考展示与正文流式渲染链路。\n\n"
        "- 思考阶段独立成一条通道\n"
        "- 正文按 markdown 流式呈现\n"
    )


def _chunk_text(text: str, *, chunk_size: int = _STREAM_CHUNK_SIZE) -> list[str]:
    """Split text into small deltas for a typewriter-style streaming display."""
    if not text:
        return []
    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]


def _default_content(request: LlmCompletionRequest) -> str:
    if request.prompt_name == "nl2sql":
        sql = "SELECT SUM(total_amount) AS total_sales FROM wide_orders LIMIT 100"
        if "refund" in request.rendered_prompt.lower():
            sql = (
                "SELECT SUM(refund_amount) AS refund_amount "
                "FROM wide_orders WHERE is_refunded = 1 LIMIT 100"
            )
        return json.dumps(
            {
                "sql": sql,
                "confidence": 0.8,
                "reasoning_summary": "deterministic fake llm mapping",
            }
        )
    if request.prompt_name == "interpret_result":
        return json.dumps(
            {
                "answer": "Query result is available.",
                "followups": [],
            }
        )
    raise ValueError(f"fake LLM fixture not registered: {request.prompt_name}@{request.version}")
