"""SQLAlchemy models for SQL audit records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from data_query_agent.infrastructure.db.base import Base


class SqlAuditModel(Base):
    """SQL audit table for policy decisions and safe summaries."""

    __tablename__ = "sql_audits"
    __table_args__ = (
        Index("ix_sql_audits_user_created", "user_id", "created_at"),
        Index("ix_sql_audits_decision_created", "decision", "created_at"),
        Index("ix_sql_audits_expires_at", "expires_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    run_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("query_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user_mirrors.id", ondelete="CASCADE"),
        nullable=False,
    )
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    sql_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    generated_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    redacted_summary: Mapped[str] = mapped_column(String(1000), nullable=False)
    policy_summary: Mapped[str] = mapped_column(String(1000), nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
