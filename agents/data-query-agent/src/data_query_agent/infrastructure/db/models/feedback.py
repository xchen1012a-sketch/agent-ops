"""SQLAlchemy models for feedback and follow-up suggestions."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from data_query_agent.infrastructure.db.base import Base


class QueryFeedbackModel(Base):
    """Feedback table attached to query runs."""

    __tablename__ = "feedbacks"
    __table_args__ = (
        UniqueConstraint("run_id", "user_id", name="uq_feedbacks_run_user"),
        Index("ix_feedbacks_user_created", "user_id", "created_at"),
        Index("ix_feedbacks_run", "run_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    run_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("query_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    thread_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("query_threads.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user_mirrors.id", ondelete="CASCADE"),
        nullable=False,
    )
    rating: Mapped[str] = mapped_column(String(32), nullable=False)
    comment: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )


class FollowupSuggestionModel(Base):
    """Follow-up suggestion table scoped to a run or a thread."""

    __tablename__ = "followup_suggestions"
    __table_args__ = (
        Index("ix_followup_suggestions_run_rank", "run_id", "rank"),
        Index("ix_followup_suggestions_thread_rank", "thread_id", "rank"),
        Index("ix_followup_suggestions_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    run_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("query_runs.id", ondelete="CASCADE"),
        nullable=True,
    )
    thread_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("query_threads.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user_mirrors.id", ondelete="CASCADE"),
        nullable=False,
    )
    suggestion_text: Mapped[str] = mapped_column(String(500), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
