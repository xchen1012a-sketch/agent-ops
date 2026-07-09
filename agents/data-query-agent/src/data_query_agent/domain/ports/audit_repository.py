"""Repository port for SQL audit records."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from data_query_agent.domain.entities.audit import SqlAudit, SqlPolicyDecision


class SqlAuditRepository(Protocol):
    """Persistence boundary for SQL policy and execution audit records."""

    async def create_sql_audit(
        self,
        *,
        public_id: str,
        run_id: int,
        user_id: int,
        decision: SqlPolicyDecision,
        sql_fingerprint: str,
        generated_sql: str | None,
        redacted_summary: str,
        policy_summary: str,
        row_count: int | None,
        result_summary: str | None,
        expires_at: datetime,
    ) -> SqlAudit:
        """Create an SQL audit record for one query run."""

    async def list_sql_audits_for_user(
        self,
        *,
        user_id: int,
        limit: int,
        offset: int,
    ) -> Sequence[SqlAudit]:
        """List SQL audits owned by one user."""
