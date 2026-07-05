"""SQLAlchemy repository for SQL audit records."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data_query_agent.domain.entities.audit import SqlAudit, SqlPolicyDecision
from data_query_agent.infrastructure.db.models.audit import SqlAuditModel


class SqlAlchemySqlAuditRepository:
    """SQLAlchemy implementation of the SQL audit repository port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        model = SqlAuditModel(
            public_id=public_id,
            run_id=run_id,
            user_id=user_id,
            decision=decision.value,
            sql_fingerprint=sql_fingerprint,
            generated_sql=generated_sql,
            redacted_summary=redacted_summary,
            policy_summary=policy_summary,
            row_count=row_count,
            result_summary=result_summary,
            expires_at=expires_at,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def list_sql_audits_for_user(
        self,
        *,
        user_id: int,
        limit: int,
        offset: int,
    ) -> Sequence[SqlAudit]:
        result = await self._session.execute(
            select(SqlAuditModel)
            .where(SqlAuditModel.user_id == user_id)
            .order_by(SqlAuditModel.created_at.desc(), SqlAuditModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return tuple(_to_entity(model) for model in result.scalars().all())


def _to_entity(model: SqlAuditModel) -> SqlAudit:
    return SqlAudit(
        id=model.id,
        public_id=model.public_id,
        run_id=model.run_id,
        user_id=model.user_id,
        decision=SqlPolicyDecision(model.decision),
        sql_fingerprint=model.sql_fingerprint,
        generated_sql=model.generated_sql,
        redacted_summary=model.redacted_summary,
        policy_summary=model.policy_summary,
        row_count=model.row_count,
        result_summary=model.result_summary,
        created_at=model.created_at,
        expires_at=model.expires_at,
    )
