"""Unit tests for data-query workflow runner audit and failure semantics."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import pytest

from data_query_agent.application.services.audit_service import SqlAuditService
from data_query_agent.application.services.run_service import QueryRunTraceService
from data_query_agent.application.services.workflow_runner_service import (
    QUERY_CONNECTION_FAILED,
    QUERY_RESULT_TOO_LARGE,
    QUERY_TIMEOUT,
    SQL_POLICY_VIOLATION,
    DataQueryWorkflowRunner,
)
from data_query_agent.domain.entities.audit import SqlAudit, SqlPolicyDecision
from data_query_agent.domain.entities.run import NodeRun, NodeStatus, QueryRun, RunStatus
from data_query_agent.domain.ports.query_adapter import QueryExecutionErrorCode
from data_query_agent.infrastructure.db.fake_query_adapter import (
    FakeReadOnlyQueryAdapter,
    make_query_result,
)
from data_query_agent.workflows.state import DataQueryState


class FakeRunRepository:
    """In-memory run repository that records run/node transitions."""

    def __init__(self) -> None:
        now = _now()
        self.run = QueryRun(
            id=1,
            public_id="run-1",
            thread_id=10,
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
        self.node_runs: list[NodeRun] = []
        self.node_events: list[tuple[str, NodeStatus]] = []
        self.next_node_id = 1

    async def create_query_run(self, **kwargs: object) -> QueryRun:
        return self.run

    async def get_query_run_for_user(self, *, run_public_id: str, user_id: int) -> QueryRun | None:
        return (
            self.run
            if self.run.public_id == run_public_id and self.run.user_id == user_id
            else None
        )

    async def update_query_run_status(
        self,
        *,
        run_id: int,
        status: RunStatus,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> QueryRun:
        self.run = QueryRun(
            id=self.run.id,
            public_id=self.run.public_id,
            thread_id=self.run.thread_id,
            user_id=self.run.user_id,
            status=status,
            question_message_id=self.run.question_message_id,
            error_code=error_code if error_code is not None else self.run.error_code,
            error_message=error_message if error_message is not None else self.run.error_message,
            started_at=started_at if started_at is not None else self.run.started_at,
            finished_at=finished_at if finished_at is not None else self.run.finished_at,
            created_at=self.run.created_at,
            updated_at=_now(),
        )
        return self.run

    async def create_node_run(
        self,
        *,
        public_id: str,
        run_id: int,
        node_name: str,
        attempt: int = 1,
    ) -> NodeRun:
        now = _now()
        node = NodeRun(
            id=self.next_node_id,
            public_id=public_id,
            run_id=run_id,
            node_name=node_name,
            status=NodeStatus.PENDING,
            attempt=attempt,
            error_code=None,
            error_message=None,
            started_at=None,
            finished_at=None,
            created_at=now,
            updated_at=now,
        )
        self.next_node_id += 1
        self.node_runs.append(node)
        return node

    async def update_node_run_status(
        self,
        *,
        node_run_id: int,
        status: NodeStatus,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> NodeRun:
        existing = self.node_runs[node_run_id - 1]
        updated = NodeRun(
            id=existing.id,
            public_id=existing.public_id,
            run_id=existing.run_id,
            node_name=existing.node_name,
            status=status,
            attempt=existing.attempt,
            error_code=error_code if error_code is not None else existing.error_code,
            error_message=error_message if error_message is not None else existing.error_message,
            started_at=started_at if started_at is not None else existing.started_at,
            finished_at=finished_at if finished_at is not None else existing.finished_at,
            created_at=existing.created_at,
            updated_at=_now(),
        )
        self.node_runs[node_run_id - 1] = updated
        self.node_events.append((updated.node_name, updated.status))
        return updated

    async def list_node_runs_for_run(self, *, run_id: int) -> Sequence[NodeRun]:
        return tuple(node for node in self.node_runs if node.run_id == run_id)


class FakeSqlAuditRepository:
    """In-memory SQL audit repository for runner tests."""

    def __init__(self) -> None:
        self.audits: list[SqlAudit] = []

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
            id=len(self.audits) + 1,
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
            created_at=_now(),
            expires_at=expires_at,
        )
        self.audits.append(audit)
        return audit

    async def list_sql_audits_for_user(
        self, *, user_id: int, limit: int, offset: int
    ) -> Sequence[SqlAudit]:
        return tuple(audit for audit in self.audits if audit.user_id == user_id)[
            offset : offset + limit
        ]

class CountingAdapter(FakeReadOnlyQueryAdapter):
    """Fake adapter that counts execution attempts."""

    def __init__(self) -> None:
        super().__init__()
        self.execute_count = 0

    async def execute(self, request):  # type: ignore[no-untyped-def]
        self.execute_count += 1
        return await super().execute(request)


def _runner(
    adapter: FakeReadOnlyQueryAdapter,
) -> tuple[DataQueryWorkflowRunner, FakeRunRepository, FakeSqlAuditRepository]:
    run_repository = FakeRunRepository()
    audit_repository = FakeSqlAuditRepository()
    return (
        DataQueryWorkflowRunner(
            run_trace_service=QueryRunTraceService(run_repository),
            audit_service=SqlAuditService(audit_repository),
            query_adapter=adapter,
        ),
        run_repository,
        audit_repository,
    )


@pytest.mark.asyncio
async def test_runner_records_success_run_node_and_audit_boundaries() -> None:
    sql = "SELECT SUM(total_amount) AS total_sales FROM wide_orders LIMIT 100"
    adapter = FakeReadOnlyQueryAdapter(
        fixtures={sql: make_query_result(columns=("total_sales",), rows=((98765.43,),))}
    )
    runner, run_repository, audit_repository = _runner(adapter)

    result = await runner.run(run=run_repository.run, question="What are total sales?")

    assert result.succeeded is True
    assert result.retryable is False
    assert result.run.status is RunStatus.SUCCESS
    assert result.state["answer"] == "Query result is 98765.43."
    assert any(
        event == ("query_execute", NodeStatus.RUNNING) for event in run_repository.node_events
    )
    assert any(
        event == ("query_execute", NodeStatus.SUCCESS) for event in run_repository.node_events
    )
    assert audit_repository.audits[0].decision is SqlPolicyDecision.ALLOWED
    assert audit_repository.audits[0].row_count == 1


@pytest.mark.asyncio
async def test_sql_policy_violation_fails_without_executing_query_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = CountingAdapter()
    runner, run_repository, audit_repository = _runner(adapter)

    def blocked_sql_node(state: DataQueryState) -> DataQueryState:
        return {**state, "generated_sql": "SELECT password FROM wide_orders LIMIT 10"}

    monkeypatch.setattr(
        "data_query_agent.application.services.workflow_runner_service.sql_generate_node",
        blocked_sql_node,
    )

    result = await runner.run(run=run_repository.run, question="What are total sales?")

    assert result.succeeded is False
    assert result.retryable is False
    assert result.error_code == SQL_POLICY_VIOLATION
    assert result.run.status is RunStatus.FAILED
    assert adapter.execute_count == 0
    assert audit_repository.audits[0].decision is SqlPolicyDecision.BLOCKED
    assert audit_repository.audits[0].policy_summary == "column_not_allowed"
    assert all(node.node_name != "query_execute" for node in run_repository.node_runs)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("adapter_error", "expected_code"),
    [
        (QueryExecutionErrorCode.TIMEOUT, QUERY_TIMEOUT),
        (QueryExecutionErrorCode.CONNECTION_FAILED, QUERY_CONNECTION_FAILED),
    ],
)
async def test_retryable_query_errors_are_marked_retryable(
    adapter_error: QueryExecutionErrorCode,
    expected_code: str,
) -> None:
    sql = "SELECT SUM(total_amount) AS total_sales FROM wide_orders LIMIT 100"
    adapter = FakeReadOnlyQueryAdapter(failures={sql: adapter_error})
    runner, run_repository, audit_repository = _runner(adapter)

    result = await runner.run(run=run_repository.run, question="What are total sales?")

    assert result.succeeded is False
    assert result.retryable is True
    assert result.error_code == expected_code
    assert result.run.status is RunStatus.FAILED
    assert audit_repository.audits[0].decision is SqlPolicyDecision.ALLOWED
    assert any(
        event == ("query_execute", NodeStatus.FAILED) for event in run_repository.node_events
    )


@pytest.mark.asyncio
async def test_result_too_large_is_non_retryable() -> None:
    sql = "SELECT SUM(total_amount) AS total_sales FROM wide_orders LIMIT 100"
    adapter = FakeReadOnlyQueryAdapter(failures={sql: QueryExecutionErrorCode.RESULT_TOO_LARGE})
    runner, run_repository, audit_repository = _runner(adapter)

    result = await runner.run(run=run_repository.run, question="What are total sales?")

    assert result.succeeded is False
    assert result.retryable is False
    assert result.error_code == QUERY_RESULT_TOO_LARGE
    assert result.run.status is RunStatus.FAILED
    assert audit_repository.audits[0].result_summary == "Query result is too large"


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
