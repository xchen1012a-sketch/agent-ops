"""Unit tests for SQL audit application service."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

import pytest

from data_query_agent.application.services.audit_service import SqlAuditService
from data_query_agent.domain.entities.audit import SqlAudit, SqlPolicyDecision
from data_query_agent.domain.entities.identity import UserMirror, UserRole
from data_query_agent.domain.entities.run import QueryRun, RunStatus


class FakeSqlAuditRepository:
    """In-memory SQL audit repository for service tests."""

    def __init__(self) -> None:
        self.audits: list[SqlAudit] = []
        self.next_id = 1

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
        audit = SqlAudit(
            id=self.next_id,
            public_id=public_id,
            run_id=run_id,
            user_id=user_id,
            decision=decision,
            sql_fingerprint=sql_fingerprint,
            generated_sql=generated_sql,
            redacted_summary=redacted_summary,
            policy_summary=policy_summary,
            row_count=row_count,
            result_summary=result_summary,
            created_at=datetime.now(UTC).replace(tzinfo=None),
            expires_at=expires_at,
        )
        self.next_id += 1
        self.audits.append(audit)
        return audit

    async def list_sql_audits_for_user(
        self,
        *,
        user_id: int,
        limit: int,
        offset: int,
    ) -> Sequence[SqlAudit]:
        owned = [audit for audit in self.audits if audit.user_id == user_id]
        return tuple(owned[offset : offset + limit])

    async def list_sql_audits_for_admin(
        self,
        *,
        limit: int,
        offset: int,
    ) -> Sequence[SqlAudit]:
        return tuple(self.audits[offset : offset + limit])


def _run(user_id: int = 20) -> QueryRun:
    now = datetime.now(UTC).replace(tzinfo=None)
    return QueryRun(
        id=10,
        public_id="run-public-id",
        thread_id=30,
        user_id=user_id,
        status=RunStatus.SUCCESS,
        question_message_id=40,
        error_code=None,
        error_message=None,
        started_at=now,
        finished_at=now,
        created_at=now,
        updated_at=now,
    )


def _user(*, user_id: int = 20, role: UserRole = UserRole.USER) -> UserMirror:
    now = datetime.now(UTC).replace(tzinfo=None)
    return UserMirror(
        id=user_id,
        public_id=f"user-{user_id}",
        external_subject=f"subject-{user_id}",
        role=role,
        display_name=None,
        created_at=now,
        updated_at=now,
        last_seen_at=now,
    )


@pytest.mark.asyncio
async def test_record_sql_audit_sets_90_day_expiry_and_policy_decision() -> None:
    service = SqlAuditService(FakeSqlAuditRepository())
    before = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=90)

    audit = await service.record_sql_audit(
        run=_run(),
        decision=SqlPolicyDecision.ALLOWED,
        sql_fingerprint="sha256:abc",
        generated_sql="SELECT SUM(amount) FROM orders LIMIT 100",
        redacted_summary="orders aggregate query",
        policy_summary="single select within limits",
        row_count=1,
        result_summary="one aggregate row",
    )

    after = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=90)
    assert audit.run_id == 10
    assert audit.user_id == 20
    assert audit.decision is SqlPolicyDecision.ALLOWED
    assert audit.sql_fingerprint == "sha256:abc"
    assert audit.generated_sql == "SELECT SUM(amount) FROM orders LIMIT 100"
    assert before <= audit.expires_at <= after


@pytest.mark.asyncio
async def test_user_summary_hides_raw_generated_sql() -> None:
    repository = FakeSqlAuditRepository()
    service = SqlAuditService(repository)
    audit = await service.record_sql_audit(
        run=_run(user_id=20),
        decision=SqlPolicyDecision.BLOCKED,
        sql_fingerprint="sha256:blocked",
        generated_sql="DROP TABLE orders",
        redacted_summary="blocked non-select statement",
        policy_summary="write keyword blocked",
    )

    summaries = await service.list_user_audit_summaries(user=_user(user_id=20))

    assert len(summaries) == 1
    assert summaries[0].public_id == audit.public_id
    assert summaries[0].decision is SqlPolicyDecision.BLOCKED
    assert summaries[0].sql_fingerprint == "sha256:blocked"
    assert not hasattr(summaries[0], "generated_sql")


@pytest.mark.asyncio
async def test_user_summary_keeps_user_boundary() -> None:
    repository = FakeSqlAuditRepository()
    service = SqlAuditService(repository)
    await service.record_sql_audit(
        run=_run(user_id=20),
        decision=SqlPolicyDecision.ALLOWED,
        sql_fingerprint="sha256:owner",
        generated_sql="SELECT 1",
        redacted_summary="owner query",
        policy_summary="allowed",
    )
    await service.record_sql_audit(
        run=_run(user_id=21),
        decision=SqlPolicyDecision.ALLOWED,
        sql_fingerprint="sha256:other",
        generated_sql="SELECT 2",
        redacted_summary="other query",
        policy_summary="allowed",
    )

    summaries = await service.list_user_audit_summaries(user=_user(user_id=20))

    assert [summary.sql_fingerprint for summary in summaries] == ["sha256:owner"]


@pytest.mark.asyncio
async def test_admin_can_see_full_sql_audits_but_user_cannot() -> None:
    repository = FakeSqlAuditRepository()
    service = SqlAuditService(repository)
    await service.record_sql_audit(
        run=_run(user_id=20),
        decision=SqlPolicyDecision.ALLOWED,
        sql_fingerprint="sha256:full",
        generated_sql="SELECT COUNT(*) FROM orders",
        redacted_summary="count orders",
        policy_summary="allowed",
    )

    full_audits = await service.list_admin_sql_audits(
        admin_user=_user(user_id=99, role=UserRole.ADMIN)
    )

    assert full_audits[0].generated_sql == "SELECT COUNT(*) FROM orders"
    with pytest.raises(PermissionError):
        await service.list_admin_sql_audits(admin_user=_user(user_id=20, role=UserRole.USER))


@pytest.mark.asyncio
async def test_rejects_unpersisted_run_and_invalid_retention() -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    unpersisted_run = QueryRun(
        id=None,
        public_id="run-public-id",
        thread_id=30,
        user_id=20,
        status=RunStatus.PENDING,
        question_message_id=None,
        error_code=None,
        error_message=None,
        started_at=None,
        finished_at=None,
        created_at=now,
        updated_at=now,
    )

    with pytest.raises(ValueError):
        SqlAuditService(FakeSqlAuditRepository(), retention_days=0)
    with pytest.raises(ValueError):
        await SqlAuditService(FakeSqlAuditRepository()).record_sql_audit(
            run=unpersisted_run,
            decision=SqlPolicyDecision.ALLOWED,
            sql_fingerprint="sha256:none",
            generated_sql=None,
            redacted_summary="none",
            policy_summary="none",
        )
