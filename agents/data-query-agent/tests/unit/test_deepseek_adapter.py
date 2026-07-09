"""Unit tests for DeepSeek adapter configuration and HTTP boundary."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass

import pytest
from pydantic import SecretStr

from data_query_agent.core.config import Settings
from data_query_agent.domain.ports.llm_adapter import LlmCompletionRequest
from data_query_agent.infrastructure.llm.deepseek_adapter import (
    DeepSeekAdapter,
    DeepSeekAdapterConfig,
)


@dataclass(frozen=True, slots=True)
class FakeDeepSeekResponse:
    status_code: int
    body: object
    text: str = "fake response"

    def json(self) -> object:
        return self.body


class FakeDeepSeekHttpClient:
    """Fake HTTP client that records requests and returns queued responses."""

    def __init__(self, responses: list[FakeDeepSeekResponse]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    async def post(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        json: Mapping[str, object],
        timeout: float,
    ) -> FakeDeepSeekResponse:
        self.calls.append(
            {
                "url": url,
                "headers": dict(headers),
                "json": dict(json),
                "timeout": timeout,
            }
        )
        return self.responses.pop(0)


def _config(*, max_retries: int = 0) -> DeepSeekAdapterConfig:
    return DeepSeekAdapterConfig(
        api_base="https://deepseek.invalid",
        api_key=SecretStr("sk-test"),
        model="deepseek-chat",
        timeout_seconds=3,
        max_retries=max_retries,
    )


def _success_response(content: str = '{"sql":"SELECT 1"}') -> FakeDeepSeekResponse:
    return FakeDeepSeekResponse(
        status_code=200,
        body={"choices": [{"message": {"content": content}}]},
    )


def test_deepseek_config_from_settings_validates_required_values() -> None:
    settings = Settings(
        deepseek_api_base="https://deepseek.invalid",
        deepseek_api_key="sk-test",
        deepseek_model="deepseek-chat",
        deepseek_timeout_seconds=3,
        deepseek_max_retries=1,
    )

    config = DeepSeekAdapterConfig.from_settings(settings)

    assert config.api_base == "https://deepseek.invalid"
    assert config.api_key.get_secret_value() == "sk-test"
    assert config.model == "deepseek-chat"


@pytest.mark.parametrize(
    "config",
    [
        DeepSeekAdapterConfig(
            api_base="",
            api_key=SecretStr("sk-test"),
            model="deepseek-chat",
            timeout_seconds=3,
            max_retries=0,
        ),
        DeepSeekAdapterConfig(
            api_base="https://deepseek.invalid",
            api_key=SecretStr(""),
            model="deepseek-chat",
            timeout_seconds=3,
            max_retries=0,
        ),
        DeepSeekAdapterConfig(
            api_base="https://deepseek.invalid",
            api_key=SecretStr("sk-test"),
            model="",
            timeout_seconds=0,
            max_retries=-1,
        ),
    ],
)
def test_deepseek_config_rejects_missing_or_invalid_values(config: DeepSeekAdapterConfig) -> None:
    with pytest.raises(ValueError, match="DeepSeek adapter configuration invalid"):
        config.validate()


@pytest.mark.asyncio
async def test_deepseek_adapter_uses_injected_http_client_without_network() -> None:
    http_client = FakeDeepSeekHttpClient([_success_response('{"sql":"SELECT 1"}')])
    adapter = DeepSeekAdapter(config=_config(), http_client=http_client)

    response = await adapter.complete(
        LlmCompletionRequest(
            prompt_name="nl2sql",
            version="v1",
            rendered_prompt="Return JSON SQL.",
        )
    )

    assert json.loads(response.content) == {"sql": "SELECT 1"}
    assert http_client.calls[0]["url"] == "https://deepseek.invalid/chat/completions"
    assert http_client.calls[0]["timeout"] == 3.0
    payload = http_client.calls[0]["json"]
    assert isinstance(payload, dict)
    assert payload["model"] == "deepseek-chat"
    assert payload["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_deepseek_adapter_retries_server_errors_then_returns_content() -> None:
    http_client = FakeDeepSeekHttpClient(
        [
            FakeDeepSeekResponse(status_code=500, body={"error": "temporary"}),
            _success_response('{"answer":"ok"}'),
        ]
    )
    adapter = DeepSeekAdapter(config=_config(max_retries=1), http_client=http_client)

    response = await adapter.complete(
        LlmCompletionRequest(
            prompt_name="interpret_result",
            version="v1",
            rendered_prompt="Return JSON answer.",
        )
    )

    assert json.loads(response.content) == {"answer": "ok"}
    assert len(http_client.calls) == 2


@pytest.mark.asyncio
async def test_deepseek_adapter_rejects_malformed_response() -> None:
    http_client = FakeDeepSeekHttpClient([FakeDeepSeekResponse(status_code=200, body={})])
    adapter = DeepSeekAdapter(config=_config(), http_client=http_client)

    with pytest.raises(RuntimeError, match="missing choices"):
        await adapter.complete(
            LlmCompletionRequest(
                prompt_name="nl2sql",
                version="v1",
                rendered_prompt="Return JSON SQL.",
            )
        )


@pytest.mark.asyncio
async def test_deepseek_adapter_reports_http_error_without_response_body() -> None:
    http_client = FakeDeepSeekHttpClient([FakeDeepSeekResponse(status_code=401, body={})])
    adapter = DeepSeekAdapter(config=_config(), http_client=http_client)

    with pytest.raises(RuntimeError, match="status 401"):
        await adapter.complete(
            LlmCompletionRequest(
                prompt_name="nl2sql",
                version="v1",
                rendered_prompt="Return JSON SQL.",
            )
        )
