"""SQLAlchemy models for query runs and workflow node traces."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data_query_agent.infrastructure.db.base import Base


class QueryRunModel(Base):
    """Query run table that records runtime status for one question."""

    __tablename__ = "query_runs"
    __table_args__ = (
        Index("ix_query_runs_thread_created", "thread_id", "created_at"),
        Index("ix_query_runs_user_status_created", "user_id", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
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
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    question_message_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("thread_messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    node_runs: Mapped[list[NodeRunModel]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )


class NodeRunModel(Base):
    """Workflow node trace table under one query run."""

    __tablename__ = "node_runs"
    __table_args__ = (
        Index("ix_node_runs_run_created", "run_id", "created_at"),
        Index("ix_node_runs_run_node_attempt", "run_id", "node_name", "attempt"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    run_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("query_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    node_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    attempt: Mapped[int] = mapped_column(nullable=False, default=1)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    run: Mapped[QueryRunModel] = relationship(back_populates="node_runs")
