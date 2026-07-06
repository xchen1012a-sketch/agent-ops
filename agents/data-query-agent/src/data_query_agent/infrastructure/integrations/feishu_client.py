"""Feishu Open Platform client: tenant token acquisition/caching and text sending.

外部服务 adapter。封装飞书 OpenAPI 协议：获取并缓存 ``tenant_access_token``、发送文本消息。
HTTP 客户端与令牌缓存都以 Protocol 边界注入，核心逻辑可脱离真实飞书与 Redis 离线测试
（与 DeepSeek adapter 同一模式）。第三方响应视为不可信输入，使用前校验 ``code`` 字段。
"""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

import httpx
from pydantic import SecretStr

from data_query_agent.core.config import Settings

_TOKEN_PATH = "/auth/v3/tenant_access_token/internal"
_MESSAGE_PATH = "/im/v1/messages"
_TOKEN_REFRESH_BUFFER_SECONDS = 120


class FeishuHttpResponse(Protocol):
    """Minimal HTTP response shape used by the Feishu client."""

    @property
    def status_code(self) -> int:
        """HTTP response status code."""

    def json(self) -> object:
        """Return decoded JSON response body."""


class FeishuHttpClient(Protocol):
    """Minimal async HTTP client boundary for tests and production clients."""

    async def post(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        json: Mapping[str, object],
        timeout: float,
    ) -> FeishuHttpResponse:
        """Post one JSON request."""


class FeishuTokenCache(Protocol):
    """Shared cache boundary for the tenant access token (Redis in production)."""

    async def get(self) -> str | None:
        """Return the cached token or None when absent/expired."""

    async def set(self, token: str, *, ttl_seconds: int) -> None:
        """Store the token with a time-to-live in seconds."""


class FeishuApiError(RuntimeError):
    """Raised when Feishu OpenAPI returns a non-zero business code or bad status."""


@dataclass(frozen=True, slots=True)
class FeishuClientConfig:
    """Validated Feishu client configuration without exposing secrets."""

    api_base: str
    app_id: str
    app_secret: SecretStr
    timeout_seconds: int
    token_cache_ttl_seconds: int

    @classmethod
    def from_settings(cls, settings: Settings) -> FeishuClientConfig:
        """Create client config from typed application settings."""
        config = cls(
            api_base=settings.feishu_api_base,
            app_id=settings.feishu_app_id,
            app_secret=settings.feishu_app_secret,
            timeout_seconds=settings.feishu_timeout_seconds,
            token_cache_ttl_seconds=settings.feishu_token_cache_ttl_seconds,
        )
        config.validate()
        return config

    def validate(self) -> None:
        """Fail fast when required Feishu client settings are missing."""
        errors: list[str] = []
        if not self.api_base:
            errors.append("FEISHU_API_BASE is required")
        if not self.app_id:
            errors.append("FEISHU_APP_ID is required")
        if not self.app_secret.get_secret_value():
            errors.append("FEISHU_APP_SECRET is required")
        if self.timeout_seconds <= 0:
            errors.append("timeout_seconds must be positive")
        if errors:
            raise ValueError("Feishu client configuration invalid: " + "; ".join(errors))


class FeishuClient:
    """Feishu OpenAPI client for tenant token and text message sending."""

    def __init__(
        self,
        *,
        config: FeishuClientConfig,
        token_cache: FeishuTokenCache,
        http_client: FeishuHttpClient | None = None,
    ) -> None:
        config.validate()
        self._config = config
        self._token_cache = token_cache
        self._http_client = http_client or _HttpxFeishuClient()

    async def get_tenant_access_token(self) -> str:
        """Return a cached token or fetch, cache and return a fresh one.

        缓存 TTL 取「飞书返回的 expire - 缓冲」与配置上限的较小值，避免多进程各自
        频繁刷新触发频控，也避免使用临近过期的令牌。
        """
        cached = await self._token_cache.get()
        if cached:
            return cached
        token, expire_seconds = await self._fetch_tenant_access_token()
        ttl = max(
            1,
            min(self._config.token_cache_ttl_seconds, expire_seconds - _TOKEN_REFRESH_BUFFER_SECONDS),
        )
        await self._token_cache.set(token, ttl_seconds=ttl)
        return token

    async def send_text(self, *, receive_id: str, text: str, receive_id_type: str = "open_id") -> None:
        """Send a plain-text message to a Feishu user/chat.

        飞书要求 ``content`` 为 JSON 字符串。非零 ``code`` 视为失败并抛 ``FeishuApiError``。
        """
        token = await self.get_tenant_access_token()
        url = f"{_join(self._config.api_base, _MESSAGE_PATH)}?receive_id_type={receive_id_type}"
        payload: dict[str, object] = {
            "receive_id": receive_id,
            "msg_type": "text",
            "content": json.dumps({"text": text}, ensure_ascii=False),
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        response = await self._http_client.post(
            url, headers=headers, json=payload, timeout=float(self._config.timeout_seconds)
        )
        _ensure_ok(response, action="send message")

    async def _fetch_tenant_access_token(self) -> tuple[str, int]:
        url = _join(self._config.api_base, _TOKEN_PATH)
        payload: dict[str, object] = {
            "app_id": self._config.app_id,
            "app_secret": self._config.app_secret.get_secret_value(),
        }
        response = await self._http_client.post(
            url,
            headers={"Content-Type": "application/json; charset=utf-8"},
            json=payload,
            timeout=float(self._config.timeout_seconds),
        )
        body = _ensure_ok(response, action="fetch tenant token")
        token = body.get("tenant_access_token")
        expire = body.get("expire")
        if not isinstance(token, str) or not token:
            raise FeishuApiError("Feishu token response missing tenant_access_token")
        if not isinstance(expire, int) or expire <= 0:
            raise FeishuApiError("Feishu token response missing valid expire")
        return token, expire


class InMemoryFeishuTokenCache(FeishuTokenCache):
    """Process-local token cache. Fallback/testing only; unsafe across workers."""

    def __init__(self) -> None:
        self._token: str | None = None
        self._expires_at: float = 0.0

    async def get(self) -> str | None:
        if self._token is not None and time.monotonic() < self._expires_at:
            return self._token
        return None

    async def set(self, token: str, *, ttl_seconds: int) -> None:
        self._token = token
        self._expires_at = time.monotonic() + ttl_seconds


class RedisLike(Protocol):
    """Structural boundary for the redis.asyncio client methods we depend on.

    只声明用到的方法，让缓存/去重实现独立于 redis 具体类型，便于离线测试替身。
    """

    async def get(self, name: str) -> Any:
        """Return the raw value for a key (bytes/str/None)."""

    async def set(
        self,
        name: str,
        value: str,
        *,
        ex: int | None = None,
        nx: bool = False,
    ) -> Any:
        """Set a key; ``ex`` TTL seconds, ``nx`` only-if-absent."""


class RedisFeishuTokenCache(FeishuTokenCache):
    """Redis-backed token cache shared across workers on the cloud deployment."""

    def __init__(self, redis: RedisLike, *, key: str = "feishu:tenant_access_token") -> None:
        self._redis = redis
        self._key = key

    async def get(self) -> str | None:
        value = await self._redis.get(self._key)
        return _decode(value)

    async def set(self, token: str, *, ttl_seconds: int) -> None:
        await self._redis.set(self._key, token, ex=ttl_seconds)


def _decode(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, str):
        return value
    return None


def _ensure_ok(response: FeishuHttpResponse, *, action: str) -> dict[str, Any]:
    """Validate transport status and Feishu business code; return the JSON object."""
    if response.status_code >= 400:
        raise FeishuApiError(f"Feishu {action} failed with status {response.status_code}")
    body = response.json()
    if not isinstance(body, dict):
        raise FeishuApiError(f"Feishu {action} returned a non-object body")
    code = body.get("code")
    if code != 0:
        message = body.get("msg", "unknown error")
        raise FeishuApiError(f"Feishu {action} failed: code={code} msg={message}")
    return body


def _join(api_base: str, path: str) -> str:
    return api_base.rstrip("/") + path


class _HttpxFeishuClient:
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
    ) -> FeishuHttpResponse:
        response = await self._client.post(url, headers=headers, json=json, timeout=timeout)
        return _HttpxFeishuResponse(response)


@dataclass(frozen=True, slots=True)
class _HttpxFeishuResponse:
    """Response wrapper that keeps the client independent from httpx types."""

    _response: httpx.Response

    @property
    def status_code(self) -> int:
        return self._response.status_code

    def json(self) -> object:
        return self._response.json()
