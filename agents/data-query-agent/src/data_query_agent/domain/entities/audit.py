"""Domain entities for SQL audit records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class SqlPolicyDecision(StrEnum):
    """Decision made by the SQL safety policy boundary."""

    ALLOWED = "allowed"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class SqlAudit:
    """Persisted SQL audit record for one query run."""

    id: int | None
    public_id: str
    run_id: int
    user_id: int
    decision: SqlPolicyDecision
    sql_fingerprint: str
    generated_sql: str | None
    redacted_summary: str
    policy_summary: str
    row_count: int | None
    result_summary: str | None
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class UserSqlAuditSummary:
    """User-safe SQL audit projection that never exposes raw SQL text."""

    public_id: str
    run_id: int
    decision: SqlPolicyDecision
    sql_fingerprint: str
    redacted_summary: str
    created_at: datetime
    expires_at: datetime
