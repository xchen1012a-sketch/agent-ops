"""Repository port for query run status and node trace records."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from data_query_agent.domain.entities.run import NodeRun, NodeStatus, QueryRun, RunStatus


class RunRepository(Protocol):
    """Persistence boundary for query runs and workflow node traces."""

    async def create_query_run(
        self,
        *,
        public_id: str,
        thread_id: int,
        user_id: int,
        question_message_id: int | None,
    ) -> QueryRun:
        """Create a pending query run for an owned thread."""

    async def list_query_runs_for_user(
        self, *, user_id: int, limit: int, offset: int
    ) -> Sequence[QueryRun]:
        """List query runs owned by one user in reverse creation order."""

    async def get_query_run_for_user(
        self,
        *,
        run_public_id: str,
        user_id: int,
    ) -> QueryRun | None:
        """Return one query run only when it belongs to the given user."""

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
        """Persist a query run status transition and audit fields."""

    async def reset_query_run_for_retry(self, *, run_id: int) -> QueryRun:
        """Clear retry-sensitive fields and mark a query run as retrying."""

    async def delete_node_runs_for_run(self, *, run_id: int) -> None:
        """Delete node traces before a retry attempt starts."""

    async def create_node_run(
        self,
        *,
        public_id: str,
        run_id: int,
        node_name: str,
        attempt: int = 1,
    ) -> NodeRun:
        """Create a pending node trace under one query run."""

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
        """Persist a node trace status transition and timestamps."""

    async def list_node_runs_for_run(self, *, run_id: int) -> Sequence[NodeRun]:
        """List node traces for one query run in creation order."""
