"""Domain entity for the agent API config center (CONFIG-100)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class AgentApiConfig:
    """Editable projection of an upstream API dependency.

    `api_key_encrypted` holds a Fernet token; `api_key_hint` is the masked
    echo string (e.g. ``sk-****abcd``) returned to clients. The plaintext key
    never leaves the encryption service boundary.
    """

    user_public_id: str
    api_type: str
    display_name: str
    base_url: str | None
    model: str | None
    api_key_encrypted: str | None
    api_key_hint: str | None
    timeout_seconds: int | None
    max_retries: int | None
    enabled: bool
    extra: dict[str, Any] | None
    updated_by: str
    updated_at: datetime
    created_at: datetime
    id: int | None = None
