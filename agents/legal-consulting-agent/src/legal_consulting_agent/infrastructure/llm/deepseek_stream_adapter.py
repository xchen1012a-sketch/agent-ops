"""DeepSeek streaming LLM adapter (CONFIG-200).

Streams chat completions and normalizes each provider delta into thinking/answer
chunks using configurable field names (model-agnostic classification). The HTTP
boundary is injectable so the SSE parsing is unit-testable without a real key or
network.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from typing import Protocol

import httpx

from legal_consulting_agent.domain.ports.llm_adapter import (
    LlmAdapter,
    LlmCompletionRequest,
    LlmCompletionResponse,
    LlmStreamChunk,
    LlmStreamError,
)

_CHAT_COMPLETIONS_PATH = "/chat/completions"
_DONE_SENTINEL = "[DONE]"
_DATA_PREFIX = "data:"


class DeepSeekStreamHttpClient(Protocol):
    """Minimal async HTTP boundary that yields raw SSE lines."""

    def stream_lines(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        json_body: Mapping[str, object],
        timeout: float,
    ) -> AsyncIterator[str]:
        """Yield raw SSE lines for a streaming chat completion request."""


@dataclass(frozen=True, slots=True)
class DeepSeekStreamConfig:
    """Validated DeepSeek streaming configuration resolved from the config center."""

    api_base: str
    api_key: str
    model: str
    timeout_seconds: int
    max_retries: int
    thinking_fields: tuple[str, ...]
    answer_fields: tuple[str, ...]


class DeepSeekStreamAdapter(LlmAdapter):
    """DeepSeek chat-completions adapter that yields normalized stream chunks."""

    def __init__(
        self,
        *,
        config: DeepSeekStreamConfig,
        http_client: DeepSeekStreamHttpClient | None = None,
    ) -> None:
        self._config = config
        self._http_client = http_client or _HttpxDeepSeekStreamClient()

    async def complete(self, request: LlmCompletionRequest) -> LlmCompletionResponse:
        """Not supported: this adapter is streaming-only."""
        raise NotImplementedError("DeepSeekStreamAdapter is streaming-only; use stream()")

    async def stream(self, request: LlmCompletionRequest) -> AsyncIterator[LlmStreamChunk]:
        """Stream DeepSeek deltas and classify each into thinking/answer chunks."""
        payload: dict[str, object] = {
            "model": self._config.model,
            "messages": [{"role": "user", "content": request.rendered_prompt}],
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
        url = self._config.api_base.rstrip("/") + _CHAT_COMPLETIONS_PATH
        try:
            lines = self._http_client.stream_lines(
                url,
                headers=headers,
                json_body=payload,
                timeout=float(self._config.timeout_seconds),
            )
            async for line in lines:
                for chunk in self._chunks_from_line(line):
                    yield chunk
        except LlmStreamError:
            raise
        except Exception as exc:  # network/protocol boundary → typed stream error
            raise LlmStreamError(
                "deepseek stream request failed", error_code="LLM_STREAM_ERROR"
            ) from exc

    def _chunks_from_line(self, line: str) -> list[LlmStreamChunk]:
        stripped = line.strip()
        if not stripped or not stripped.startswith(_DATA_PREFIX):
            return []
        data = stripped[len(_DATA_PREFIX) :].strip()
        if not data or data == _DONE_SENTINEL:
            return []
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            return []
        return self._chunks_from_payload(payload)

    def _chunks_from_payload(self, payload: object) -> list[LlmStreamChunk]:
        if not isinstance(payload, dict):
            return []
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            return []
        first = choices[0]
        if not isinstance(first, dict):
            return []
        delta = first.get("delta")
        if not isinstance(delta, dict):
            return []
        chunks: list[LlmStreamChunk] = []
        for field in self._config.thinking_fields:
            value = delta.get(field)
            if isinstance(value, str) and value:
                chunks.append(LlmStreamChunk(kind="thinking", text=value))
        for field in self._config.answer_fields:
            value = delta.get(field)
            if isinstance(value, str) and value:
                chunks.append(LlmStreamChunk(kind="answer", text=value))
        return chunks


class _HttpxDeepSeekStreamClient:
    """Production streaming client that keeps the adapter independent from httpx."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient()

    async def stream_lines(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        json_body: Mapping[str, object],
        timeout: float,
    ) -> AsyncIterator[str]:
        async with self._client.stream(
            "POST", url, headers=dict(headers), json=dict(json_body), timeout=timeout
        ) as response:
            if response.status_code >= 400:
                raise LlmStreamError(
                    f"deepseek stream failed: HTTP {response.status_code}",
                    error_code="LLM_STREAM_HTTP",
                    retryable=response.status_code >= 500,
                )
            async for line in response.aiter_lines():
                yield line
