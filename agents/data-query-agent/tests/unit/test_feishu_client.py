"""Unit tests for the Feishu OpenAPI client (token caching + text send)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest
from pydantic import SecretStr

from data_query_agent.infrastructure.integrations.feishu_client import (
    FeishuApiError,
    FeishuClient,
    FeishuClientConfig,
    InMemoryFeishuTokenCache,
)


class _FakeResponse:
    def __init__(self, *, status_code: int, body: dict[str, Any]) -> None:
        self.status_code = status_code
        self._body = body

    def json(self) -> object:
        return self._body


class _FakeHttpClient:
    """Records requests and returns queued responses in order."""

    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = responses
        self.calls: list[dict[str, Any]] = []

    async def post(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        json: Mapping[str, object],
        timeout: float,
    ) -> _FakeResponse:
        self.calls.append({"url": url, "headers": dict(headers), "json": dict(json)})
        return self._responses.pop(0)


def _config() -> FeishuClientConfig:
    return FeishuClientConfig(
        api_base="https://open.feishu.cn/open-apis",
        app_id="cli_test",
        app_secret=SecretStr("secret"),
        timeout_seconds=10,
        token_cache_ttl_seconds=6600,
    )


async def test_get_tenant_access_token_fetches_then_caches() -> None:
    http = _FakeHttpClient(
        [_FakeResponse(status_code=200, body={"code": 0, "tenant_access_token": "t-1", "expire": 7200})]
    )
    cache = InMemoryFeishuTokenCache()
    client = FeishuClient(config=_config(), token_cache=cache, http_client=http)

    first = await client.get_tenant_access_token()
    second = await client.get_tenant_access_token()

    assert first == "t-1"
    assert second == "t-1"
    assert len(http.calls) == 1  # 第二次命中缓存，不再请求飞书


async def test_send_text_uses_bearer_token_and_text_payload() -> None:
    http = _FakeHttpClient(
        [
            _FakeResponse(status_code=200, body={"code": 0, "tenant_access_token": "t-1", "expire": 7200}),
            _FakeResponse(status_code=200, body={"code": 0, "data": {"message_id": "m-1"}}),
        ]
    )
    client = FeishuClient(config=_config(), token_cache=InMemoryFeishuTokenCache(), http_client=http)

    await client.send_text(receive_id="ou_123", text="hello")

    send_call = http.calls[1]
    assert "receive_id_type=open_id" in send_call["url"]
    assert send_call["headers"]["Authorization"] == "Bearer t-1"
    assert send_call["json"]["msg_type"] == "text"
    assert send_call["json"]["content"] == '{"text": "hello"}'


async def test_send_text_raises_on_non_zero_business_code() -> None:
    http = _FakeHttpClient(
        [
            _FakeResponse(status_code=200, body={"code": 0, "tenant_access_token": "t-1", "expire": 7200}),
            _FakeResponse(status_code=200, body={"code": 230001, "msg": "bot not in chat"}),
        ]
    )
    client = FeishuClient(config=_config(), token_cache=InMemoryFeishuTokenCache(), http_client=http)

    with pytest.raises(FeishuApiError):
        await client.send_text(receive_id="ou_123", text="hello")
