"""Unit tests for current-user API config isolation."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from cryptography.fernet import Fernet

from legal_consulting_agent.api.v1.endpoints.admin_api_config import (
    list_api_configs,
    update_api_config,
)
from legal_consulting_agent.api.v1.schemas.agent_api_config import AgentApiConfigUpdate
from legal_consulting_agent.application.services.agent_api_config import ApiConfigCrypto
from legal_consulting_agent.domain.entities.agent_api_config import AgentApiConfig


class FakeAgentApiConfigRepository:
    """In-memory repository that preserves user-level isolation."""

    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], AgentApiConfig] = {}

    async def list_for_user(self, user_public_id: str) -> list[AgentApiConfig]:
        return [
            row
            for (row_user_public_id, _api_type), row in self.rows.items()
            if row_user_public_id == user_public_id
        ]

    async def get_by_type(self, user_public_id: str, api_type: str) -> AgentApiConfig | None:
        return self.rows.get((user_public_id, api_type))

    async def upsert(
        self,
        *,
        user_public_id: str,
        api_type: str,
        display_name: str,
        base_url: str | None,
        model: str | None,
        api_key_encrypted: str | None,
        api_key_hint: str | None,
        timeout_seconds: int | None,
        max_retries: int | None,
        enabled: bool,
        extra: dict | None,
        updated_by: str,
    ) -> AgentApiConfig:
        now = datetime.now(UTC)
        entity = AgentApiConfig(
            id=len(self.rows) + 1,
            user_public_id=user_public_id,
            api_type=api_type,
            display_name=display_name,
            base_url=base_url,
            model=model,
            api_key_encrypted=api_key_encrypted,
            api_key_hint=api_key_hint,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            enabled=enabled,
            extra=extra,
            updated_by=updated_by,
            updated_at=now,
            created_at=now,
        )
        self.rows[(user_public_id, api_type)] = entity
        return entity


@pytest.mark.asyncio
async def test_api_config_is_scoped_to_current_user() -> None:
    repo = FakeAgentApiConfigRepository()
    crypto = ApiConfigCrypto(Fernet.generate_key().decode())
    payload = AgentApiConfigUpdate(
        display_name="DeepSeek",
        base_url="https://api.example.invalid",
        model="deepseek-chat",
        api_key="sk-user-a",
        timeout_seconds=60,
        max_retries=3,
        enabled=True,
        extra=None,
    )

    await update_api_config("deepseek", payload, "user-a", repo, crypto)
    user_a = await list_api_configs("user-a", repo)
    user_b = await list_api_configs("user-b", repo)

    assert next(item for item in user_a.data.items if item.api_type == "deepseek").api_key_hint
    assert next(item for item in user_b.data.items if item.api_type == "deepseek").api_key_hint is None
