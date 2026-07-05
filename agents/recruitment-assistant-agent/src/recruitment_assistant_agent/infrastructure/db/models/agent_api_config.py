"""ORM model for agent_api_config (CONFIG-100)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from recruitment_assistant_agent.infrastructure.db.base import Base
from recruitment_assistant_agent.infrastructure.db.models.recruit_data import (
    DateTimeFsp,
    UnsignedBigInteger,
)

_TEXT_HINT_LENGTH = 16
_NAME_LENGTH = 64
_BASE_URL_LENGTH = 255
_MODEL_LENGTH = 64
_API_TYPE_LENGTH = 32
_USER_PUBLIC_ID_LENGTH = 64


class AgentApiConfigModel(Base):
    """Editable upstream API dependency (DeepSeek, Redis, ...).

    `api_key_encrypted` is a Fernet token; the plaintext never persists.
    `api_key_hint` is the masked echo shown to clients.
    """

    __tablename__ = "agent_api_config"
    __table_args__ = (
        UniqueConstraint("user_public_id", "api_type", name="uk_agent_api_config_user_type"),
    )

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    user_public_id: Mapped[str] = mapped_column(String(_USER_PUBLIC_ID_LENGTH), nullable=False)
    api_type: Mapped[str] = mapped_column(String(_API_TYPE_LENGTH), nullable=False)
    display_name: Mapped[str] = mapped_column(String(_NAME_LENGTH), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(_BASE_URL_LENGTH))
    model: Mapped[str | None] = mapped_column(String(_MODEL_LENGTH))
    api_key_encrypted: Mapped[str | None] = mapped_column(Text)
    api_key_hint: Mapped[str | None] = mapped_column(String(_TEXT_HINT_LENGTH))
    timeout_seconds: Mapped[int | None] = mapped_column(Integer)
    max_retries: Mapped[int | None] = mapped_column(Integer)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1"
    )
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    updated_by: Mapped[str] = mapped_column(String(_NAME_LENGTH), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        onupdate=text("CURRENT_TIMESTAMP(6)"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
