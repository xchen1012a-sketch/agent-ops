"""ORM models for the LEGAL-130 identity and data layer."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from legal_consulting_agent.domain.value_objects.legal_enums import (
    MessageRole,
    RunStatus,
    SessionStatus,
    UserRole,
    UserStatus,
)
from legal_consulting_agent.infrastructure.db.base import Base

UnsignedBigInteger = mysql.BIGINT(unsigned=True)
DateTimeFsp = mysql.DATETIME(fsp=6)


def _enum_values(
    enum_cls: type[UserRole]
    | type[UserStatus]
    | type[SessionStatus]
    | type[MessageRole]
    | type[RunStatus],
) -> list[str]:
    return [member.value for member in enum_cls]


class TimestampMixin:
    """Common MySQL datetime columns for mutable business rows."""

    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )


class UserModel(TimestampMixin, Base):
    """Legal service mirror of a unified-auth user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(mysql.CHAR(36), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    display_name: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, values_callable=_enum_values, name="user_role"),
        nullable=False,
        default=UserRole.USER,
        server_default=UserRole.USER.value,
    )
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus, values_callable=_enum_values, name="user_status"),
        nullable=False,
        default=UserStatus.ACTIVE,
        server_default=UserStatus.ACTIVE.value,
    )

    sessions: Mapped[list[LegalSessionModel]] = relationship(back_populates="user")


class LegalCategoryModel(TimestampMixin, Base):
    """Legal category table; data is inserted only after category policy approval."""

    __tablename__ = "legal_categories"

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(mysql.CHAR(36), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    sessions: Mapped[list[LegalSessionModel]] = relationship(back_populates="category")


class LegalSessionModel(TimestampMixin, Base):
    """Legal consultation session owned by one user."""

    __tablename__ = "sessions"
    __table_args__ = (Index("idx_sessions_user_time", "user_id", "last_message_at"),)

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(mysql.CHAR(36), nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("users.id", name="fk_sessions_user"),
        nullable=False,
    )
    category_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("legal_categories.id", name="fk_sessions_category"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[SessionStatus] = mapped_column(
        SAEnum(SessionStatus, values_callable=_enum_values, name="session_status"),
        nullable=False,
        default=SessionStatus.ACTIVE,
        server_default=SessionStatus.ACTIVE.value,
    )
    last_message_at: Mapped[datetime | None] = mapped_column(DateTimeFsp)

    user: Mapped[UserModel] = relationship(back_populates="sessions")
    category: Mapped[LegalCategoryModel] = relationship(back_populates="sessions")
    messages: Mapped[list[LegalMessageModel]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class LegalMessageModel(Base):
    """Persisted message inside a legal consultation session."""

    __tablename__ = "messages"
    __table_args__ = (Index("idx_messages_session_time", "session_id", "created_at"),)

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(mysql.CHAR(36), nullable=False, unique=True)
    session_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("sessions.id", name="fk_messages_session", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[MessageRole] = mapped_column(
        SAEnum(MessageRole, values_callable=_enum_values, name="message_role"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(mysql.MEDIUMTEXT, nullable=False)
    citations: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    high_risk: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    prompt_version: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )

    session: Mapped[LegalSessionModel] = relationship(back_populates="messages")


class ConsultationRecordModel(Base):
    """Structured snapshot used by history search and report projection."""

    __tablename__ = "consultation_records"
    __table_args__ = (
        UniqueConstraint("answer_message_id", name="uk_consultation_answer"),
        Index("idx_consultation_user_time", "user_id", "created_at"),
        Index("idx_consultation_category_time", "category_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(mysql.CHAR(36), nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("users.id", name="fk_consultation_user"),
        nullable=False,
    )
    session_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("sessions.id", name="fk_consultation_session"),
        nullable=False,
    )
    category_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("legal_categories.id", name="fk_consultation_category"),
        nullable=False,
    )
    question_message_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("messages.id", name="fk_consultation_question"),
        nullable=False,
    )
    answer_message_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("messages.id", name="fk_consultation_answer"),
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    high_risk: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    disclaimer: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )


class FeedbackModel(Base):
    """User feedback for one assistant answer."""

    __tablename__ = "feedbacks"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_feedback_rating"),
        UniqueConstraint("user_id", "message_id", name="uk_feedback_user_message"),
        Index("idx_feedback_message", "message_id"),
    )

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("messages.id", name="fk_feedback_message"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("users.id", name="fk_feedback_user"),
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(mysql.TINYINT, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTimeFsp,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )


class AgentRunModel(Base):
    """Auditable Agent run record."""

    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("idx_runs_thread", "thread_id", "started_at"),
        Index("idx_runs_status", "status"),
    )

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(mysql.CHAR(36), nullable=False, unique=True)
    thread_id: Mapped[str] = mapped_column(mysql.CHAR(36), nullable=False)
    user_id: Mapped[int] = mapped_column(UnsignedBigInteger, nullable=False)
    workflow_version: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[RunStatus] = mapped_column(
        SAEnum(RunStatus, values_callable=_enum_values, name="run_status"),
        nullable=False,
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_summary: Mapped[str | None] = mapped_column(String(500))
    started_at: Mapped[datetime] = mapped_column(DateTimeFsp, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTimeFsp)
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    node_runs: Mapped[list[NodeRunModel]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )


class NodeRunModel(Base):
    """Auditable LangGraph node execution record."""

    __tablename__ = "node_runs"
    __table_args__ = (Index("idx_node_runs_run", "run_id", "started_at"),)

    id: Mapped[int] = mapped_column(UnsignedBigInteger, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(
        UnsignedBigInteger,
        ForeignKey("agent_runs.id", name="fk_node_run", ondelete="CASCADE"),
        nullable=False,
    )
    node_name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[RunStatus] = mapped_column(
        SAEnum(RunStatus, values_callable=_enum_values, name="node_run_status"),
        nullable=False,
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(64))
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    started_at: Mapped[datetime] = mapped_column(DateTimeFsp, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTimeFsp)

    run: Mapped[AgentRunModel] = relationship(back_populates="node_runs")
