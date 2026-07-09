"""DTOs for the agent API config center admin endpoints (CONFIG-100)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# Allowed api_type values per agent. Legal: deepseek/embedding/vector_db/reranker/ocr.
AgentApiType = Literal["deepseek", "embedding", "vector_db", "reranker", "ocr"]


class AgentApiConfigView(BaseModel):
    """Public projection returned to clients; never contains the plaintext key."""

    model_config = ConfigDict(from_attributes=True)

    user_public_id: str
    api_type: str
    display_name: str
    base_url: str | None
    model: str | None
    api_key_hint: str | None
    timeout_seconds: int | None
    max_retries: int | None
    enabled: bool
    extra: dict[str, Any] | None
    updated_by: str
    updated_at: datetime


class AgentApiConfigListData(BaseModel):
    items: list[AgentApiConfigView]


class AgentApiConfigListEnvelope(BaseModel):
    data: AgentApiConfigListData
    error: Literal[None] = None


class AgentApiConfigEnvelope(BaseModel):
    data: AgentApiConfigView
    error: Literal[None] = None


class AgentApiConfigUpdate(BaseModel):
    """Editable fields. `api_key` is optional: empty = do not change."""

    model_config = ConfigDict(str_strip_whitespace=True)

    display_name: str = Field(min_length=1, max_length=64)
    base_url: str | None = Field(default=None, max_length=255)
    model: str | None = Field(default=None, max_length=64)
    api_key: str | None = Field(default=None, min_length=0, max_length=512)
    timeout_seconds: int | None = Field(default=None, ge=1, le=600)
    max_retries: int | None = Field(default=None, ge=0, le=10)
    enabled: bool = True
    extra: dict[str, Any] | None = None
