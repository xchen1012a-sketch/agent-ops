"""Unit tests for resolving the streaming adapter from the config center (CONFIG-200)."""

from __future__ import annotations

from datetime import UTC, datetime

from cryptography.fernet import Fernet
from pydantic import SecretStr

from legal_consulting_agent.application.services.agent_api_config import ApiConfigCrypto
from legal_consulting_agent.application.services.stream_adapter_resolver import (
    resolve_stream_adapter,
)
from legal_consulting_agent.core.config import Settings
from legal_consulting_agent.domain.entities.agent_api_config import AgentApiConfig
from legal_consulting_agent.infrastructure.llm.deepseek_stream_adapter import DeepSeekStreamAdapter
from legal_consulting_agent.infrastructure.llm.fake_llm_adapter import FakeLlmAdapter


class _FakeReader:
    def __init__(self, config: AgentApiConfig | None) -> None:
        self._config = config

    async def get_by_type(self, user_public_id: str, api_type: str) -> AgentApiConfig | None:
        return self._config


def _config(*, enabled: bool, api_key_encrypted: str | None) -> AgentApiConfig:
    now = datetime.now(UTC)
    return AgentApiConfig(
        user_public_id="user-1",
        api_type="deepseek",
        display_name="DeepSeek",
        base_url="https://api.deepseek.test",
        model="deepseek-chat",
        api_key_encrypted=api_key_encrypted,
        api_key_hint="sk-t****9012" if api_key_encrypted else None,
        timeout_seconds=30,
        max_retries=2,
        enabled=enabled,
        extra=None,
        updated_by="user-1",
        updated_at=now,
        created_at=now,
    )


def _settings(master_key: str) -> Settings:
    return Settings(agent_config_encryption_key=SecretStr(master_key))


async def test_enabled_config_with_key_resolves_real_adapter() -> None:
    master = Fernet.generate_key().decode()
    encrypted = ApiConfigCrypto(master).encrypt("sk-live-key-1234")
    reader = _FakeReader(_config(enabled=True, api_key_encrypted=encrypted))

    adapter = await resolve_stream_adapter(subject="user-1", reader=reader, settings=_settings(master))

    assert isinstance(adapter, DeepSeekStreamAdapter)


async def test_missing_config_falls_back_to_fake() -> None:
    adapter = await resolve_stream_adapter(
        subject="user-1", reader=_FakeReader(None), settings=_settings(Fernet.generate_key().decode())
    )
    assert isinstance(adapter, FakeLlmAdapter)


async def test_disabled_config_falls_back_to_fake() -> None:
    master = Fernet.generate_key().decode()
    encrypted = ApiConfigCrypto(master).encrypt("sk-live-key-1234")
    reader = _FakeReader(_config(enabled=False, api_key_encrypted=encrypted))

    adapter = await resolve_stream_adapter(subject="user-1", reader=reader, settings=_settings(master))

    assert isinstance(adapter, FakeLlmAdapter)


async def test_undecryptable_token_falls_back_to_fake() -> None:
    stored_master = Fernet.generate_key().decode()
    other_master = Fernet.generate_key().decode()
    encrypted = ApiConfigCrypto(stored_master).encrypt("sk-live-key-1234")
    reader = _FakeReader(_config(enabled=True, api_key_encrypted=encrypted))

    adapter = await resolve_stream_adapter(
        subject="user-1", reader=reader, settings=_settings(other_master)
    )

    assert isinstance(adapter, FakeLlmAdapter)
