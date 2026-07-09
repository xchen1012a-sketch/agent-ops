"""Unit tests for the DeepSeek streaming adapter SSE parsing (CONFIG-200)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping

import pytest

from legal_consulting_agent.domain.ports.llm_adapter import (
    LlmCompletionRequest,
    LlmStreamChunk,
    LlmStreamError,
)
from legal_consulting_agent.infrastructure.llm.deepseek_stream_adapter import (
    DeepSeekStreamAdapter,
    DeepSeekStreamConfig,
)


class _FakeStreamClient:
    def __init__(self, lines: list[str], *, raise_exc: Exception | None = None) -> None:
        self._lines = lines
        self._raise = raise_exc

    async def stream_lines(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        json_body: Mapping[str, object],
        timeout: float,
    ) -> AsyncIterator[str]:
        if self._raise is not None:
            raise self._raise
        for line in self._lines:
            yield line


def _config() -> DeepSeekStreamConfig:
    return DeepSeekStreamConfig(
        api_base="https://api.deepseek.test",
        api_key="sk-test-key",
        model="deepseek-chat",
        timeout_seconds=30,
        max_retries=2,
        thinking_fields=("reasoning_content", "reasoning"),
        answer_fields=("content", "text"),
    )


async def _collect(adapter: DeepSeekStreamAdapter) -> list[LlmStreamChunk]:
    request = LlmCompletionRequest(prompt_name="p", version="v", rendered_prompt="q")
    return [chunk async for chunk in adapter.stream(request)]


async def test_reasoning_then_content_map_to_thinking_and_answer() -> None:
    lines = [
        'data: {"choices":[{"delta":{"reasoning_content":"想一下"}}]}',
        'data: {"choices":[{"delta":{"content":"答案"}}]}',
        "data: [DONE]",
    ]
    adapter = DeepSeekStreamAdapter(config=_config(), http_client=_FakeStreamClient(lines))

    chunks = await _collect(adapter)

    assert [(c.kind, c.text) for c in chunks] == [
        ("thinking", "想一下"),
        ("answer", "答案"),
    ]


async def test_blank_and_malformed_lines_are_ignored() -> None:
    lines = [
        "",
        "data: not-json",
        'data: {"choices":[]}',
        'data: {"choices":[{"delta":{"content":"hi"}}]}',
    ]
    adapter = DeepSeekStreamAdapter(config=_config(), http_client=_FakeStreamClient(lines))

    chunks = await _collect(adapter)

    assert [(c.kind, c.text) for c in chunks] == [("answer", "hi")]


async def test_transport_error_becomes_stream_error() -> None:
    adapter = DeepSeekStreamAdapter(
        config=_config(),
        http_client=_FakeStreamClient([], raise_exc=RuntimeError("connection reset")),
    )

    with pytest.raises(LlmStreamError):
        await _collect(adapter)
