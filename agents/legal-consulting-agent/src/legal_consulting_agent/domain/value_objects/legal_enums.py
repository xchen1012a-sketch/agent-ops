"""Central legal domain enums used by ORM, services, and workflow state."""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    """Roles trusted from the unified auth JWT claims."""

    USER = "user"
    ADMIN = "admin"


class UserStatus(StrEnum):
    """User mirror lifecycle states."""

    ACTIVE = "active"
    DISABLED = "disabled"


class SessionStatus(StrEnum):
    """Legal consultation session lifecycle states."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class MessageRole(StrEnum):
    """Allowed message authors in a legal consultation thread."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class RunStatus(StrEnum):
    """Shared Agent and node execution states."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELED = "canceled"


class ReviewStatus(StrEnum):
    """Lifecycle states for a high-risk human review."""

    PENDING = "pending"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"


class PromptStatus(StrEnum):
    """Lifecycle states for versioned Prompt metadata."""

    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"


class MaterialStatus(StrEnum):
    """Indexing lifecycle states for legal knowledge materials."""

    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"
