"""Unit tests for run SSE event contract."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from data_query_agent.api.dependencies import (
    get_identity_thread_service,
    get_query_run_trace_service,
)
from data_query_agent.domain.entities.identity import UserMirror, UserRole
from data_query_agent.domain.entities.run import NodeRun, NodeStatus, QueryRun, RunStatus
from data_query_agent.main import create_app


class FakeIdentityThreadService:
    """Fake identity service for stream API tests."""

    async def get_user_for_subject(self, *, external_subject: str) -> UserMirror | None:
        if external_subject != "owner":
            return None
        return UserMirror(
            id=20,
            public_id="user-20",
            external_subject=external_subject,
            role=UserRole.USER,
            display_name=None,
            created_at=_now(),
            updated_at=_now(),
            last_seen_at=_now(),
        )


class FakeRunTraceService:
    """Fake run trace service for deterministic stream projection."""

    def __init__(self, *, run: QueryRun, nodes: Sequence[NodeRun]) -> None:
        self.run = run
        self.nodes = tuple(nodes)

    async def get_run_for_user(self, *, run_public_id: str, user_id: int) -> QueryRun | None:
        if self.run.public_id == run_public_id and self.run.user_id == user_id:
            return self.run
        return None

    async def list_node_runs(self, *, run: QueryRun) -> Sequence[NodeRun]:
        return self.nodes if run.public_id == self.run.public_id else ()


def _client(run_service: FakeRunTraceService) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_identity_thread_service] = lambda: FakeIdentityThreadService()
    app.dependency_overrides[get_query_run_trace_service] = lambda: run_service
    return TestClient(app)


def test_stream_run_events_projects_success_contract_without_token_streaming() -> None:
    client = _client(
        FakeRunTraceService(
            run=_run(status=RunStatus.SUCCESS),
            nodes=(
                _node("input_validation", NodeStatus.SUCCESS),
                _node("interpret", NodeStatus.SUCCESS),
            ),
        )
    )

    response = client.get("/v1/runs/run-1/stream", headers={"X-User-Subject": "owner"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert "event: run.started" in body
    assert "event: node.started" in body
    assert "event: node.completed" in body
    assert "event: run.completed" in body
    assert "token" not in body.lower()


def test_stream_run_events_projects_failure_contract() -> None:
    client = _client(
        FakeRunTraceService(
            run=_run(status=RunStatus.FAILED, error_code="SQL_POLICY_VIOLATION"),
            nodes=(_node("sql_policy_check", NodeStatus.FAILED, error_code="column_not_allowed"),),
        )
    )

    response = client.get("/v1/runs/run-1/stream", headers={"X-User-Subject": "owner"})

    assert response.status_code == 200
    body = response.text
    assert "event: node.failed" in body
    assert "event: run.failed" in body
    assert "SQL_POLICY_VIOLATION" in body


def test_stream_run_events_blocks_cross_subject_access() -> None:
    client = _client(FakeRunTraceService(run=_run(status=RunStatus.SUCCESS), nodes=()))

    response = client.get("/v1/runs/run-1/stream", headers={"X-User-Subject": "other"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def _run(*, status: RunStatus, error_code: str | None = None) -> QueryRun:
    return QueryRun(
        id=1,
        public_id="run-1",
        thread_id=10,
        user_id=20,
        status=status,
        question_message_id=30,
        error_code=error_code,
        error_message="safe error" if error_code else None,
        started_at=_now(),
        finished_at=_now() if status in {RunStatus.SUCCESS, RunStatus.FAILED} else None,
        created_at=_now(),
        updated_at=_now(),
    )


def _node(node_name: str, status: NodeStatus, error_code: str | None = None) -> NodeRun:
    return NodeRun(
        id=1,
        public_id=f"node-{node_name}",
        run_id=1,
        node_name=node_name,
        status=status,
        attempt=1,
        error_code=error_code,
        error_message="safe node error" if error_code else None,
        started_at=_now(),
        finished_at=_now(),
        created_at=_now(),
        updated_at=_now(),
    )


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
