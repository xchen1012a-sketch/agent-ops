"""Admin SQL audit API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from data_query_agent.domain.entities.audit import SqlAudit


class AdminSqlAuditItem(BaseModel):
    """Full SQL audit projection for admin users only."""

    audit_id: str
    run_id: int
    user_id: int
    decision: str
    sql_fingerprint: str
    generated_sql: str | None
    redacted_summary: str
    policy_summary: str
    row_count: int | None
    result_summary: str | None
    created_at: datetime
    expires_at: datetime

    @classmethod
    def from_entity(cls, audit: SqlAudit) -> AdminSqlAuditItem:
        """Convert a SQL audit entity to an admin-only DTO."""
        return cls(
            audit_id=audit.public_id,
            run_id=audit.run_id,
            user_id=audit.user_id,
            decision=audit.decision.value,
            sql_fingerprint=audit.sql_fingerprint,
            generated_sql=audit.generated_sql,
            redacted_summary=audit.redacted_summary,
            policy_summary=audit.policy_summary,
            row_count=audit.row_count,
            result_summary=audit.result_summary,
            created_at=audit.created_at,
            expires_at=audit.expires_at,
        )


class AdminSqlAuditListData(BaseModel):
    """Paginated admin SQL audit payload."""

    items: list[AdminSqlAuditItem]
    limit: int
    offset: int


class AdminSqlAuditListEnvelope(BaseModel):
    """Success envelope for admin SQL audit list."""

    data: AdminSqlAuditListData
    error: None = None


class ErrorEnvelope(BaseModel):
    """OpenAPI error envelope shape."""

    data: None = None
    error: dict[str, Any]
