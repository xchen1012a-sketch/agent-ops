"""DeepSeek LLM adapter with injectable HTTP client boundary."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
from pydantic import SecretStr

from data_query_agent.core.config import Settings
from data_query_agent.domain.ports.llm_adapter import (
    LlmAdapter,
    LlmCompletionRequest,
    LlmCompletionResponse,
)

_CHAT_COMPLETIONS_PATH = "/chat/completions"
_RESPONSE_CHOICES_FIELD = "choices"
_RESPONSE_MESSAGE_FIELD = "message"
_RESPONSE_CONTENT_FIELD = "content"


class DeepSeekHttpResponse(Protocol):
    """Minimal HTTP response shape used by the DeepSeek adapter."""

    @property
    def status_code(self) -> int:
        """HTTP response status code."""

    @property
    def text(self) -> str:
        """Raw response text for safe diagnostics."""

    def json(self) -> object:
        """Return decoded JSON response body."""


class DeepSeekHttpClient(Protocol):
    """Minimal async HTTP client boundary for tests and production clients."""

    async def post(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        json: Mapping[str, object],
        timeout: float,
    ) -> DeepSeekHttpResponse:
        """Post one JSON request."""


@dataclass(frozen=True, slots=True)
class DeepSeekAdapterConfig:
    """Validated DeepSeek adapter configuration without exposing secrets."""

    api_base: str
    api_key: SecretStr
    model: str
    timeout_seconds: int
    max_retries: int

    @classmethod
    def from_settings(cls, settings: Settings) -> DeepSeekAdapterConfig:
        """Create adapter config from typed application settings."""
        config = cls(
            api_base=settings.deepseek_api_base,
            api_key=settings.deepseek_api_key,
            model=settings.deepseek_model,
            timeout_seconds=settings.deepseek_timeout_seconds,
            max_retries=settings.deepseek_max_retries,
        )
        config.validate()
        return config

    def validate(self) -> None:
        """Fail fast when required DeepSeek adapter settings are missing."""
        errors: list[str] = []
        if not self.api_base:
            errors.append("DEEPSEEK_API_BASE is required")
        if not self.api_key.get_secret_value():
            errors.append("DEEPSEEK_API_KEY is required")
        if not self.model:
            errors.append("DEEPSEEK_MODEL is required")
        if self.timeout_seconds <= 0:
            errors.append("DEEPSEEK_TIMEOUT_SECONDS must be positive")
        if self.max_retries < 0:
            errors.append("DEEPSEEK_MAX_RETRIES must be >= 0")
        if errors:
            raise ValueError("DeepSeek adapter configuration invalid: " + "; ".join(errors))


class DeepSeekAdapter(LlmAdapter):
    """DeepSeek chat completion adapter that returns structured text only."""

    def __init__(
        self,
        *,
        config: DeepSeekAdapterConfig,
        http_client: DeepSeekHttpClient | None = None,
    ) -> None:
        config.validate()
        self._config = config
        self._http_client = http_client or _HttpxDeepSeekClient()

    async def complete(self, request: LlmCompletionRequest) -> LlmCompletionResponse:
        """Call DeepSeek chat completions and extract message content safely."""
        payload: dict[str, object] = {
            "model": self._config.model,
            "messages": [
                {
                    "role": "user",
                    "content": request.rendered_prompt,
                }
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self._config.api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }
        response = await self._post_with_retries(
            _join_url(self._config.api_base, _CHAT_COMPLETIONS_PATH),
            headers=headers,
            payload=payload,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"DeepSeek request failed with status {response.status_code}")
        return LlmCompletionResponse(content=_extract_content(response.json()))

    async def _post_with_retries(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
    ) -> DeepSeekHttpResponse:
        attempts = self._config.max_retries + 1
        last_response: DeepSeekHttpResponse | None = None
        for _ in range(attempts):
            response = await self._http_client.post(
                url,
                headers=headers,
                json=payload,
                timeout=float(self._config.timeout_seconds),
            )
            last_response = response
            if response.status_code < 500:
                return response
        if last_response is None:
            raise RuntimeError("DeepSeek request did not return a response")
        return last_response


def _extract_content(payload: object) -> str:
    body = _as_object(payload, "DeepSeek response")
    choices = body.get(_RESPONSE_CHOICES_FIELD)
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("DeepSeek response missing choices")
    first_choice = _as_object(choices[0], "DeepSeek response choice")
    message = _as_object(first_choice.get(_RESPONSE_MESSAGE_FIELD), "DeepSeek response message")
    content = message.get(_RESPONSE_CONTENT_FIELD)
    if not isinstance(content, str) or not content:
        raise RuntimeError("DeepSeek response missing message content")
    return content


def _as_object(value: Any, field_name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise RuntimeError(f"{field_name} must be an object")
    return value


def _join_url(api_base: str, path: str) -> str:
    return api_base.rstrip("/") + path


class _HttpxDeepSeekClient:
    """Small httpx adapter that satisfies the internal HTTP client protocol."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient()

    async def post(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        json: Mapping[str, object],
        timeout: float,
    ) -> DeepSeekHttpResponse:
        response = await self._client.post(url, headers=headers, json=json, timeout=timeout)
        return _HttpxDeepSeekResponse(response)


@dataclass(frozen=True, slots=True)
class _HttpxDeepSeekResponse:
    """Response wrapper that keeps the adapter independent from httpx types."""

    _response: httpx.Response

    @property
    def status_code(self) -> int:
        return self._response.status_code

    @property
    def text(self) -> str:
        return self._response.text

    def json(self) -> object:
        return self._response.json()
