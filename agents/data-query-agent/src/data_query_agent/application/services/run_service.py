"""Application service for query run and node trace lifecycle."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

from data_query_agent.domain.entities.identity import QueryThread
from data_query_agent.domain.entities.run import NodeRun, NodeStatus, QueryRun, RunStatus
from data_query_agent.domain.ports.run_repository import RunRepository


class QueryRunTraceService:
    """Use cases for auditable query run and node trace transitions."""

    def __init__(self, repository: RunRepository) -> None:
        self._repository = repository

    async def create_run_for_thread(
        self,
        *,
        thread: QueryThread,
        question_message_id: int | None = None,
    ) -> QueryRun:
        """Create a pending query run under an already-owned thread."""
        if thread.id is None:
            raise ValueError("persisted thread must have an id")
        return await self._repository.create_query_run(
            public_id=str(uuid4()),
            thread_id=thread.id,
            user_id=thread.user_id,
            question_message_id=question_message_id,
        )

    async def start_run(self, *, run_id: int) -> QueryRun:
        """Mark a query run as running."""
        return await self._repository.update_query_run_status(
            run_id=run_id,
            status=RunStatus.RUNNING,
            started_at=_utcnow_naive(),
        )

    async def complete_run(self, *, run_id: int) -> QueryRun:
        """Mark a query run as successful."""
        return await self._repository.update_query_run_status(
            run_id=run_id,
            status=RunStatus.SUCCESS,
            finished_at=_utcnow_naive(),
        )

    async def fail_run(
        self,
        *,
        run_id: int,
        error_code: str,
        error_message: str,
    ) -> QueryRun:
        """Mark a query run as failed with a safe error summary."""
        return await self._repository.update_query_run_status(
            run_id=run_id,
            status=RunStatus.FAILED,
            finished_at=_utcnow_naive(),
            error_code=error_code,
            error_message=error_message,
        )

    async def cancel_run(self, *, run_id: int) -> QueryRun:
        """Mark a query run as canceled."""
        return await self._repository.update_query_run_status(
            run_id=run_id,
            status=RunStatus.CANCELED,
            finished_at=_utcnow_naive(),
        )

    async def mark_run_retrying(self, *, run_id: int) -> QueryRun:
        """Mark a query run as retrying without deleting historical traces."""
        return await self._repository.update_query_run_status(
            run_id=run_id,
            status=RunStatus.RETRYING,
        )

    async def retry_run(self, *, run_id: int) -> QueryRun:
        """Prepare a failed or canceled query run for retry.

        The current cycle only defines application-layer state semantics:
        clearing previous error fields and node traces. It does not interrupt
        or enqueue real background jobs.
        """
        await self._repository.delete_node_runs_for_run(run_id=run_id)
        return await self._repository.reset_query_run_for_retry(run_id=run_id)

    async def create_node_run(
        self,
        *,
        run: QueryRun,
        node_name: str,
        attempt: int = 1,
    ) -> NodeRun:
        """Create a pending node trace under a persisted query run."""
        if run.id is None:
            raise ValueError("persisted query run must have an id")
        if attempt < 1:
            raise ValueError("node attempt must be positive")
        return await self._repository.create_node_run(
            public_id=str(uuid4()),
            run_id=run.id,
            node_name=node_name,
            attempt=attempt,
        )

    async def start_node(self, *, node_run_id: int) -> NodeRun:
        """Record node start timestamp."""
        return await self._repository.update_node_run_status(
            node_run_id=node_run_id,
            status=NodeStatus.RUNNING,
            started_at=_utcnow_naive(),
        )

    async def finish_node(
        self,
        *,
        node_run_id: int,
        status: NodeStatus = NodeStatus.SUCCESS,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> NodeRun:
        """Record node finish timestamp with final status."""
        if status not in {NodeStatus.SUCCESS, NodeStatus.FAILED, NodeStatus.SKIPPED}:
            raise ValueError("node finish status must be terminal")
        return await self._repository.update_node_run_status(
            node_run_id=node_run_id,
            status=status,
            finished_at=_utcnow_naive(),
            error_code=error_code,
            error_message=error_message,
        )

    async def list_node_runs(self, *, run: QueryRun) -> Sequence[NodeRun]:
        """List node traces for a persisted query run."""
        if run.id is None:
            raise ValueError("persisted query run must have an id")
        return await self._repository.list_node_runs_for_run(run_id=run.id)


def _utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
