"""Application service for SQL audit persistence and projections."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from data_query_agent.domain.entities.audit import (
    SqlAudit,
    SqlPolicyDecision,
    UserSqlAuditSummary,
)
from data_query_agent.domain.entities.identity import UserMirror, UserRole
from data_query_agent.domain.entities.run import QueryRun
from data_query_agent.domain.ports.audit_repository import SqlAuditRepository

SQL_AUDIT_RETENTION_DAYS = 90


class SqlAuditService:
    """Use cases for SQL audit retention and role-aware projections."""

    def __init__(
        self,
        repository: SqlAuditRepository,
        *,
        retention_days: int = SQL_AUDIT_RETENTION_DAYS,
    ) -> None:
        if retention_days < 1:
            raise ValueError("sql audit retention days must be positive")
        self._repository = repository
        self._retention_days = retention_days

    async def record_sql_audit(
        self,
        *,
        run: QueryRun,
        decision: SqlPolicyDecision,
        sql_fingerprint: str,
        generated_sql: str | None,
        redacted_summary: str,
        policy_summary: str,
        row_count: int | None = None,
        result_summary: str | None = None,
    ) -> SqlAudit:
        """Record policy decision and SQL summary for a persisted query run."""
        if run.id is None:
            raise ValueError("persisted query run must have an id")
        now = _utcnow_naive()
        return await self._repository.create_sql_audit(
            public_id=str(uuid4()),
            run_id=run.id,
            user_id=run.user_id,
            decision=decision,
            sql_fingerprint=sql_fingerprint,
            generated_sql=generated_sql,
            redacted_summary=redacted_summary,
            policy_summary=policy_summary,
            row_count=row_count,
            result_summary=result_summary,
            expires_at=now + timedelta(days=self._retention_days),
        )

    async def list_user_audit_summaries(
        self,
        *,
        user: UserMirror,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[UserSqlAuditSummary]:
        """List user-owned SQL audit summaries without exposing raw SQL."""
        if user.id is None:
            raise ValueError("persisted user mirror must have an id")
        audits = await self._repository.list_sql_audits_for_user(
            user_id=user.id,
            limit=limit,
            offset=offset,
        )
        return tuple(_to_user_summary(audit) for audit in audits)

    async def list_admin_sql_audits(
        self,
        *,
        admin_user: UserMirror,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[SqlAudit]:
        """List full SQL audits only for admin mirrors."""
        if admin_user.id is None:
            raise ValueError("persisted user mirror must have an id")
        if admin_user.role is not UserRole.ADMIN:
            raise PermissionError("admin role required for full SQL audit access")
        return await self._repository.list_sql_audits_for_admin(limit=limit, offset=offset)


def _to_user_summary(audit: SqlAudit) -> UserSqlAuditSummary:
    return UserSqlAuditSummary(
        public_id=audit.public_id,
        run_id=audit.run_id,
        decision=audit.decision,
        sql_fingerprint=audit.sql_fingerprint,
        redacted_summary=audit.redacted_summary,
        created_at=audit.created_at,
        expires_at=audit.expires_at,
    )


def _utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
