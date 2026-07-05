"""Feishu Open API client: tenant token, IM, CardKit."""

from __future__ import annotations

import json
import time
from threading import Lock
from typing import Any

import httpx

from app.config import Settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class FeishuApiError(Exception):
    """Raised when Feishu Open API returns an error."""


class FeishuApiClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base = settings.feishu_api_base.rstrip("/")
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._lock = Lock()

    async def _get_tenant_access_token(self) -> str:
        now = time.time()
        with self._lock:
            if self._token and now < self._token_expires_at - 60:
                return self._token

        url = f"{self._base}/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self._settings.feishu_app_id,
            "app_secret": self._settings.feishu_app_secret,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        if data.get("code") != 0:
            raise FeishuApiError(
                f"Failed to get tenant_access_token: {data.get('msg', data)}"
            )

        token = data.get("tenant_access_token")
        if not isinstance(token, str) or not token:
            raise FeishuApiError("tenant_access_token missing in response")

        expire = data.get("expire", 7200)
        with self._lock:
            self._token = token
            self._token_expires_at = now + float(expire)
        return token

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        token = await self._get_tenant_access_token()
        url = f"{self._base}{path}"
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_body,
            )
            if response.status_code >= 400:
                raise FeishuApiError(
                    f"Feishu HTTP {response.status_code}: {response.text[:500]}"
                )
            data = response.json()

        if data.get("code") != 0:
            raise FeishuApiError(f"Feishu API error: {data.get('msg', data)}")
        return data

    async def create_streaming_card(self, *, initial_text: str, title: str = "AI 助手") -> str:
        card_json = {
            "schema": "2.0",
            "config": {
                "update_multi": True,
                "streaming_mode": True,
                "streaming_config": {
                    "print_frequency_ms": {
                        "default": 70,
                        "android": 70,
                        "ios": 70,
                        "pc": 70,
                    },
                    "print_step": {"default": 1, "android": 1, "ios": 1, "pc": 1},
                    "print_strategy": "fast",
                },
            },
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": "blue",
            },
            "body": {
                "elements": [
                    {
                        "tag": "markdown",
                        "content": initial_text,
                        "element_id": "markdown_1",
                    }
                ]
            },
        }
        data = await self._request(
            "POST",
            "/open-apis/cardkit/v1/cards",
            json_body={
                "type": "card_json",
                "data": json.dumps(card_json, ensure_ascii=False),
            },
        )
        card_id = (data.get("data") or {}).get("card_id")
        if not isinstance(card_id, str) or not card_id:
            raise FeishuApiError("card_id missing in create card response")
        return card_id

    async def send_card_message(self, *, chat_id: str, card_id: str) -> str:
        content = json.dumps({"type": "card", "data": {"card_id": card_id}}, ensure_ascii=False)
        data = await self._request(
            "POST",
            "/open-apis/im/v1/messages",
            params={"receive_id_type": "chat_id"},
            json_body={
                "receive_id": chat_id,
                "msg_type": "interactive",
                "content": content,
            },
        )
        message_id = (data.get("data") or {}).get("message_id")
        if not isinstance(message_id, str):
            raise FeishuApiError("message_id missing in send message response")
        return message_id

    async def update_card_content(
        self,
        *,
        card_id: str,
        element_id: str,
        content: str,
        sequence: int,
    ) -> None:
        await self._request(
            "PUT",
            f"/open-apis/cardkit/v1/cards/{card_id}/elements/{element_id}/content",
            json_body={
                "content": content,
                "sequence": sequence,
            },
        )

    async def end_card_stream(self, *, card_id: str, sequence: int) -> None:
        settings_json = json.dumps({"config": {"streaming_mode": False}}, ensure_ascii=False)
        await self._request(
            "PATCH",
            f"/open-apis/cardkit/v1/cards/{card_id}/settings",
            json_body={
                "settings": settings_json,
                "sequence": sequence,
            },
        )

    async def send_text_message(self, *, chat_id: str, text: str) -> str:
        content = json.dumps({"text": text}, ensure_ascii=False)
        data = await self._request(
            "POST",
            "/open-apis/im/v1/messages",
            params={"receive_id_type": "chat_id"},
            json_body={
                "receive_id": chat_id,
                "msg_type": "text",
                "content": content,
            },
        )
        message_id = (data.get("data") or {}).get("message_id")
        if not isinstance(message_id, str):
            raise FeishuApiError("message_id missing in send text response")
        return message_id
