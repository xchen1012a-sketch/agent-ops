"""Unit tests for query run and node trace application service."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import pytest

from data_query_agent.application.services.run_service import QueryRunTraceService
from data_query_agent.domain.entities.identity import QueryThread, ThreadStatus
from data_query_agent.domain.entities.run import NodeRun, NodeStatus, QueryRun, RunStatus


class FakeRunRepository:
    """In-memory run repository for service tests."""

    def __init__(self) -> None:
        self.runs_by_id: dict[int, QueryRun] = {}
        self.runs_by_public_id: dict[str, QueryRun] = {}
        self.node_runs_by_id: dict[int, NodeRun] = {}
        self.next_run_id = 1
        self.next_node_run_id = 1

    async def create_query_run(
        self,
        *,
        public_id: str,
        thread_id: int,
        user_id: int,
        question_message_id: int | None,
    ) -> QueryRun:
        now = datetime.now(UTC).replace(tzinfo=None)
        run = QueryRun(
            id=self.next_run_id,
            public_id=public_id,
            thread_id=thread_id,
            user_id=user_id,
            status=RunStatus.PENDING,
            question_message_id=question_message_id,
            error_code=None,
            error_message=None,
            started_at=None,
            finished_at=None,
            created_at=now,
            updated_at=now,
        )
        self.next_run_id += 1
        self.runs_by_id[run.id or 0] = run
        self.runs_by_public_id[public_id] = run
        return run

    async def get_query_run_for_user(
        self,
        *,
        run_public_id: str,
        user_id: int,
    ) -> QueryRun | None:
        run = self.runs_by_public_id.get(run_public_id)
        if run is None or run.user_id != user_id:
            return None
        return run

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
        existing = self.runs_by_id[run_id]
        updated = QueryRun(
            id=existing.id,
            public_id=existing.public_id,
            thread_id=existing.thread_id,
            user_id=existing.user_id,
            status=status,
            question_message_id=existing.question_message_id,
            error_code=error_code if error_code is not None else existing.error_code,
            error_message=error_message if error_message is not None else existing.error_message,
            started_at=started_at if started_at is not None else existing.started_at,
            finished_at=finished_at if finished_at is not None else existing.finished_at,
            created_at=existing.created_at,
            updated_at=datetime.now(UTC).replace(tzinfo=None),
        )
        self.runs_by_id[run_id] = updated
        self.runs_by_public_id[updated.public_id] = updated
        return updated

    async def create_node_run(
        self,
        *,
        public_id: str,
        run_id: int,
        node_name: str,
        attempt: int = 1,
    ) -> NodeRun:
        now = datetime.now(UTC).replace(tzinfo=None)
        node_run = NodeRun(
            id=self.next_node_run_id,
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
        self.next_node_run_id += 1
        self.node_runs_by_id[node_run.id or 0] = node_run
        return node_run

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
        existing = self.node_runs_by_id[node_run_id]
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
            updated_at=datetime.now(UTC).replace(tzinfo=None),
        )
        self.node_runs_by_id[node_run_id] = updated
        return updated

    async def list_node_runs_for_run(self, *, run_id: int) -> Sequence[NodeRun]:
        return tuple(node for node in self.node_runs_by_id.values() if node.run_id == run_id)


def _thread() -> QueryThread:
    now = datetime.now(UTC).replace(tzinfo=None)
    return QueryThread(
        id=10,
        public_id="thread-public-id",
        user_id=20,
        title="Sales analysis",
        status=ThreadStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_create_run_for_thread_starts_pending() -> None:
    service = QueryRunTraceService(FakeRunRepository())

    run = await service.create_run_for_thread(thread=_thread(), question_message_id=30)

    assert run.thread_id == 10
    assert run.user_id == 20
    assert run.question_message_id == 30
    assert run.status is RunStatus.PENDING
    assert run.started_at is None
    assert run.finished_at is None


@pytest.mark.asyncio
async def test_run_status_transitions_are_auditable() -> None:
    service = QueryRunTraceService(FakeRunRepository())
    run = await service.create_run_for_thread(thread=_thread())
    assert run.id is not None

    running = await service.start_run(run_id=run.id)
    retrying = await service.mark_run_retrying(run_id=run.id)
    failed = await service.fail_run(
        run_id=run.id,
        error_code="SQL_POLICY_VIOLATION",
        error_message="blocked by policy",
    )

    assert running.status is RunStatus.RUNNING
    assert running.started_at is not None
    assert retrying.status is RunStatus.RETRYING
    assert failed.status is RunStatus.FAILED
    assert failed.finished_at is not None
    assert failed.error_code == "SQL_POLICY_VIOLATION"
    assert failed.error_message == "blocked by policy"


@pytest.mark.asyncio
async def test_run_can_be_completed_or_canceled() -> None:
    service = QueryRunTraceService(FakeRunRepository())
    first = await service.create_run_for_thread(thread=_thread())
    second = await service.create_run_for_thread(thread=_thread())
    assert first.id is not None
    assert second.id is not None

    completed = await service.complete_run(run_id=first.id)
    canceled = await service.cancel_run(run_id=second.id)

    assert completed.status is RunStatus.SUCCESS
    assert completed.finished_at is not None
    assert canceled.status is RunStatus.CANCELED
    assert canceled.finished_at is not None


@pytest.mark.asyncio
async def test_node_started_and_finished_can_be_recorded() -> None:
    service = QueryRunTraceService(FakeRunRepository())
    run = await service.create_run_for_thread(thread=_thread())
    node = await service.create_node_run(run=run, node_name="sql_policy_check")
    assert node.id is not None

    started = await service.start_node(node_run_id=node.id)
    finished = await service.finish_node(node_run_id=node.id)

    assert started.status is NodeStatus.RUNNING
    assert started.started_at is not None
    assert finished.status is NodeStatus.SUCCESS
    assert finished.finished_at is not None


@pytest.mark.asyncio
async def test_failed_and_skipped_node_finish_are_terminal() -> None:
    service = QueryRunTraceService(FakeRunRepository())
    run = await service.create_run_for_thread(thread=_thread())
    failed_node = await service.create_node_run(run=run, node_name="query_execute")
    skipped_node = await service.create_node_run(run=run, node_name="interpret_result", attempt=2)
    assert failed_node.id is not None
    assert skipped_node.id is not None

    failed = await service.finish_node(
        node_run_id=failed_node.id,
        status=NodeStatus.FAILED,
        error_code="QUERY_TIMEOUT",
        error_message="query timeout",
    )
    skipped = await service.finish_node(node_run_id=skipped_node.id, status=NodeStatus.SKIPPED)
    node_runs = await service.list_node_runs(run=run)

    assert failed.status is NodeStatus.FAILED
    assert failed.error_code == "QUERY_TIMEOUT"
    assert skipped.status is NodeStatus.SKIPPED
    assert [node.node_name for node in node_runs] == ["query_execute", "interpret_result"]


@pytest.mark.asyncio
async def test_rejects_unpersisted_run_and_non_terminal_node_finish() -> None:
    service = QueryRunTraceService(FakeRunRepository())
    now = datetime.now(UTC).replace(tzinfo=None)
    unpersisted_run = QueryRun(
        id=None,
        public_id="unpersisted",
        thread_id=1,
        user_id=1,
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
        await service.create_node_run(run=unpersisted_run, node_name="schema_lookup")
    with pytest.raises(ValueError):
        await service.finish_node(node_run_id=1, status=NodeStatus.RUNNING)
