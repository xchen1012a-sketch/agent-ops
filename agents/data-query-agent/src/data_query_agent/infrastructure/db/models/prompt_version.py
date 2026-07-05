"""SQLAlchemy models for prompt version records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from data_query_agent.infrastructure.db.base import Base


class PromptVersionModel(Base):
    """Prompt version table with admin creation ownership."""

    __tablename__ = "prompt_versions"
    __table_args__ = (
        UniqueConstraint("prompt_name", "version", name="uq_prompt_versions_name_version"),
        Index("ix_prompt_versions_name_active", "prompt_name", "is_active"),
        Index("ix_prompt_versions_created_by", "created_by_user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    prompt_name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    template_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    template_body: Mapped[str] = mapped_column(Text, nullable=False)
    variables_schema: Mapped[str] = mapped_column(Text, nullable=False)
    output_schema: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user_mirrors.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
