"""Domain entities for query runs and workflow node traces."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class RunStatus(StrEnum):
    """Lifecycle status for one natural-language query run."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELED = "canceled"


class NodeStatus(StrEnum):
    """Lifecycle status for one workflow node trace."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class QueryRun:
    """Runtime record for one question execution inside a query thread."""

    id: int | None
    public_id: str
    thread_id: int
    user_id: int
    status: RunStatus
    question_message_id: int | None
    error_code: str | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class NodeRun:
    """Trace record for one node execution inside a query run."""

    id: int | None
    public_id: str
    run_id: int
    node_name: str
    status: NodeStatus
    attempt: int
    error_code: str | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime
