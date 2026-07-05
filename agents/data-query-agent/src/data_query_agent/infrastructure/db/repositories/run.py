"""SQLAlchemy repository for query runs and workflow node traces."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data_query_agent.domain.entities.run import NodeRun, NodeStatus, QueryRun, RunStatus
from data_query_agent.infrastructure.db.models.run import NodeRunModel, QueryRunModel


class SqlAlchemyRunRepository:
    """SQLAlchemy implementation of the run repository port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_query_run(
        self,
        *,
        public_id: str,
        thread_id: int,
        user_id: int,
        question_message_id: int | None,
    ) -> QueryRun:
        now = _utcnow_naive()
        model = QueryRunModel(
            public_id=public_id,
            thread_id=thread_id,
            user_id=user_id,
            status=RunStatus.PENDING.value,
            question_message_id=question_message_id,
            created_at=now,
            updated_at=now,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_query_run_entity(model)

    async def get_query_run_for_user(
        self,
        *,
        run_public_id: str,
        user_id: int,
    ) -> QueryRun | None:
        result = await self._session.execute(
            select(QueryRunModel).where(
                QueryRunModel.public_id == run_public_id,
                QueryRunModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return _to_query_run_entity(model) if model is not None else None

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
        model = await self._session.get(QueryRunModel, run_id)
        if model is None:
            raise LookupError(f"query run not found: {run_id}")
        model.status = status.value
        model.updated_at = _utcnow_naive()
        if started_at is not None:
            model.started_at = started_at
        if finished_at is not None:
            model.finished_at = finished_at
        if error_code is not None:
            model.error_code = error_code
        if error_message is not None:
            model.error_message = error_message
        await self._session.flush()
        return _to_query_run_entity(model)

    async def create_node_run(
        self,
        *,
        public_id: str,
        run_id: int,
        node_name: str,
        attempt: int = 1,
    ) -> NodeRun:
        now = _utcnow_naive()
        model = NodeRunModel(
            public_id=public_id,
            run_id=run_id,
            node_name=node_name,
            status=NodeStatus.PENDING.value,
            attempt=attempt,
            created_at=now,
            updated_at=now,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_node_run_entity(model)

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
        model = await self._session.get(NodeRunModel, node_run_id)
        if model is None:
            raise LookupError(f"node run not found: {node_run_id}")
        model.status = status.value
        model.updated_at = _utcnow_naive()
        if started_at is not None:
            model.started_at = started_at
        if finished_at is not None:
            model.finished_at = finished_at
        if error_code is not None:
            model.error_code = error_code
        if error_message is not None:
            model.error_message = error_message
        await self._session.flush()
        return _to_node_run_entity(model)

    async def list_node_runs_for_run(self, *, run_id: int) -> Sequence[NodeRun]:
        result = await self._session.execute(
            select(NodeRunModel)
            .where(NodeRunModel.run_id == run_id)
            .order_by(NodeRunModel.created_at.asc(), NodeRunModel.id.asc())
        )
        return tuple(_to_node_run_entity(model) for model in result.scalars().all())


def _utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _to_query_run_entity(model: QueryRunModel) -> QueryRun:
    return QueryRun(
        id=model.id,
        public_id=model.public_id,
        thread_id=model.thread_id,
        user_id=model.user_id,
        status=RunStatus(model.status),
        question_message_id=model.question_message_id,
        error_code=model.error_code,
        error_message=model.error_message,
        started_at=model.started_at,
        finished_at=model.finished_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_node_run_entity(model: NodeRunModel) -> NodeRun:
    return NodeRun(
        id=model.id,
        public_id=model.public_id,
        run_id=model.run_id,
        node_name=model.node_name,
        status=NodeStatus(model.status),
        attempt=model.attempt,
        error_code=model.error_code,
        error_message=model.error_message,
        started_at=model.started_at,
        finished_at=model.finished_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
