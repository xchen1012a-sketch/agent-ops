"""Fake LLM adapter for prompt-backed workflow tests."""

from __future__ import annotations

import json

from data_query_agent.domain.ports.llm_adapter import (
    LlmAdapter,
    LlmCompletionRequest,
    LlmCompletionResponse,
)


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
