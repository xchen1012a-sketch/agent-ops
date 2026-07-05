"""Domain entities for the LEGAL-130 identity and data layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from legal_consulting_agent.domain.value_objects.legal_enums import (
    MessageRole,
    RunStatus,
    SessionStatus,
    UserRole,
    UserStatus,
)


@dataclass(frozen=True, slots=True)
class UserMirror:
    """Unified-auth user mirror stored by the legal Agent.

    Passwords and refresh tokens remain outside this service.
    """

    public_id: str
    email: str
    display_name: str | None
    role: UserRole
    status: UserStatus
    id: int | None = None


@dataclass(frozen=True, slots=True)
class LegalCategory:
    """Legal category metadata without seed data assumptions."""

    public_id: str
    code: str
    display_name: str
    description: str | None
    sort_order: int
    id: int | None = None


@dataclass(frozen=True, slots=True)
class LegalSession:
    """Consultation thread owned by one user and one category."""

    public_id: str
    user_id: int
    category_id: int
    title: str | None
    status: SessionStatus
    last_message_at: datetime | None
    id: int | None = None


@dataclass(frozen=True, slots=True)
class LegalMessage:
    """Persisted message in a legal consultation session."""

    public_id: str
    session_id: int
    role: MessageRole
    content: str
    citations: list[dict[str, Any]] | None
    high_risk: bool
    prompt_version: str | None
    id: int | None = None


@dataclass(frozen=True, slots=True)
class AgentRun:
    """Auditable LangGraph run record."""

    public_id: str
    thread_id: str
    user_id: int
    workflow_version: str
    prompt_version: str
    status: RunStatus
    retry_count: int
    error_code: str | None
    error_summary: str | None
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    id: int | None = None


@dataclass(frozen=True, slots=True)
class NodeRun:
    """Auditable LangGraph node execution record."""

    run_id: int
    node_name: str
    status: RunStatus
    duration_ms: int | None
    error_code: str | None
    metadata: dict[str, Any] | None
    started_at: datetime
    finished_at: datetime | None
    id: int | None = None
