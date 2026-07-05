"""SQLAlchemy models for user mirrors and query threads."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data_query_agent.infrastructure.db.base import Base


class UserMirrorModel(Base):
    """Local user mirror table."""

    __tablename__ = "user_mirrors"
    __table_args__ = (Index("ix_user_mirrors_external_subject", "external_subject", unique=True),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    external_subject: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="user")
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
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
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    threads: Mapped[list[QueryThreadModel]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list[ThreadMessageModel]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class QueryThreadModel(Base):
    """Query thread table owned by a user mirror."""

    __tablename__ = "query_threads"
    __table_args__ = (Index("ix_query_threads_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user_mirrors.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
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
    user: Mapped[UserMirrorModel] = relationship(back_populates="threads")
    messages: Mapped[list[ThreadMessageModel]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
    )


class ThreadMessageModel(Base):
    """Message table for a query thread."""

    __tablename__ = "thread_messages"
    __table_args__ = (
        Index("ix_thread_messages_thread_created", "thread_id", "created_at"),
        Index("ix_thread_messages_user_created", "user_id", "created_at"),
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
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(String(4000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
    thread: Mapped[QueryThreadModel] = relationship(back_populates="messages")
    user: Mapped[UserMirrorModel] = relationship(back_populates="messages")
