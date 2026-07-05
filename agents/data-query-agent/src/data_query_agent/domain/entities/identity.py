"""Domain entities for user mirrors and query threads."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class UserRole(StrEnum):
    """User role mirrored from the unified auth boundary."""

    USER = "user"
    ADMIN = "admin"


class ThreadStatus(StrEnum):
    """Lifecycle status for a query thread."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class MessageRole(StrEnum):
    """Role of a message in one query thread."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True)
class UserMirror:
    """Local mirror of an authenticated user."""

    id: int | None
    public_id: str
    external_subject: str
    role: UserRole
    display_name: str | None
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime | None


@dataclass(frozen=True, slots=True)
class QueryThread:
    """Conversation thread owned by a mirrored user."""

    id: int | None
    public_id: str
    user_id: int
    title: str | None
    status: ThreadStatus
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ThreadMessage:
    """Message stored inside a query thread."""

    id: int | None
    public_id: str
    thread_id: int
    user_id: int
    role: MessageRole
    content: str
    created_at: datetime
