"""Resolve the streaming LLM adapter from the per-user API config center (CONFIG-200).

Reads the current account's ``deepseek`` config; when it is enabled and holds a
decryptable key, streaming goes to the real DeepSeek adapter. Otherwise (no
config, disabled, no key, missing master key, or decryption failure) it falls
back to the deterministic FakeLlmAdapter — so behavior is unchanged until a key
is entered.
"""

from __future__ import annotations

from typing import Protocol

from data_query_agent.application.services.agent_api_config import ApiConfigCrypto
from data_query_agent.core.config import Settings
from data_query_agent.core.errors import ConfigDecryptError, ConfigKeyTooShortError
from data_query_agent.domain.entities.agent_api_config import AgentApiConfig
from data_query_agent.domain.ports.llm_adapter import LlmAdapter
from data_query_agent.infrastructure.llm.deepseek_stream_adapter import (
    DeepSeekStreamAdapter,
    DeepSeekStreamConfig,
)
from data_query_agent.infrastructure.llm.fake_llm_adapter import FakeLlmAdapter

_DEEPSEEK_API_TYPE = "deepseek"


class AgentApiConfigReader(Protocol):
    """Read-only view of the per-user API config store used by the resolver."""

    async def get_by_type(self, user_public_id: str, api_type: str) -> AgentApiConfig | None:
        """Return one config entry for a user by api_type, or None."""


async def resolve_stream_adapter(
    *,
    subject: str,
    reader: AgentApiConfigReader,
    settings: Settings,
) -> LlmAdapter:
    """Select the real DeepSeek stream adapter or fall back to the fake adapter."""
    config = await reader.get_by_type(subject, _DEEPSEEK_API_TYPE)
    if config is None or not config.enabled or not config.api_key_encrypted:
        return FakeLlmAdapter()
    try:
        crypto = ApiConfigCrypto(settings.agent_config_encryption_key.get_secret_value())
        api_key = crypto.decrypt(config.api_key_encrypted)
    except (ConfigKeyTooShortError, ConfigDecryptError):
        return FakeLlmAdapter()
    return DeepSeekStreamAdapter(
        config=DeepSeekStreamConfig(
            api_base=config.base_url or settings.deepseek_api_base,
            api_key=api_key,
            model=config.model or settings.deepseek_model,
            timeout_seconds=config.timeout_seconds or settings.deepseek_timeout_seconds,
            max_retries=(
                config.max_retries
                if config.max_retries is not None
                else settings.deepseek_max_retries
            ),
            thinking_fields=settings.llm_stream_thinking_field_names,
            answer_fields=settings.llm_stream_answer_field_names,
        )
    )
