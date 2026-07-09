"""Unit tests for query history API slice."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from data_query_agent.api.dependencies import (
    get_identity_thread_service,
    get_query_run_trace_service,
)
from data_query_agent.domain.entities.identity import UserMirror, UserRole
from data_query_agent.domain.entities.run import QueryRun, RunStatus
from data_query_agent.main import create_app


class FakeIdentityThreadService:
    """Fake identity service for query history tests."""

    async def get_user_for_subject(self, *, external_subject: str) -> UserMirror | None:
        if external_subject == "missing":
            return None
        return UserMirror(
            id=20 if external_subject == "owner" else 30,
            public_id=f"user-{external_subject}",
            external_subject=external_subject,
            role=UserRole.USER,
            display_name=None,
            created_at=_now(),
            updated_at=_now(),
            last_seen_at=_now(),
        )


class FakeRunTraceService:
    """Fake run service for query history tests."""

    def __init__(self) -> None:
        self.runs = [
            _run(public_id="run-1", user_id=20, status=RunStatus.SUCCESS, minutes_ago=1),
            _run(public_id="run-2", user_id=20, status=RunStatus.FAILED, minutes_ago=2),
            _run(public_id="run-3", user_id=30, status=RunStatus.SUCCESS, minutes_ago=3),
        ]

    async def list_runs_for_user(self, *, user_id: int, limit: int = 20, offset: int = 0):
        owned = [run for run in self.runs if run.user_id == user_id]
        return tuple(owned[offset : offset + limit])

    async def get_run_for_user(self, *, run_public_id: str, user_id: int) -> QueryRun | None:
        for run in self.runs:
            if run.public_id == run_public_id and run.user_id == user_id:
                return run
        return None


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_identity_thread_service] = lambda: FakeIdentityThreadService()
    app.dependency_overrides[get_query_run_trace_service] = lambda: FakeRunTraceService()
    return TestClient(app)


def test_list_query_history_returns_only_current_user_summaries_without_sql() -> None:
    client = _client()

    response = client.get("/v1/query-history", headers={"X-User-Subject": "owner"})

    assert response.status_code == 200
    body = response.json()
    assert [item["query_id"] for item in body["data"]["items"]] == ["run-1", "run-2"]
    assert body["data"]["limit"] == 20
    assert body["data"]["offset"] == 0
    assert "sql" not in str(body).lower()


def test_list_query_history_supports_pagination() -> None:
    client = _client()

    response = client.get(
        "/v1/query-history?limit=1&offset=1",
        headers={"X-User-Subject": "owner"},
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["query_id"] for item in body["data"]["items"]] == ["run-2"]
    assert body["data"]["limit"] == 1
    assert body["data"]["offset"] == 1


def test_get_query_history_detail_is_owner_scoped() -> None:
    client = _client()

    owned = client.get("/v1/query-history/run-1", headers={"X-User-Subject": "owner"})
    blocked = client.get("/v1/query-history/run-1", headers={"X-User-Subject": "other"})

    assert owned.status_code == 200
    assert owned.json()["data"]["query_id"] == "run-1"
    assert blocked.status_code == 404
    assert blocked.json()["error"]["code"] == "NOT_FOUND"


def test_missing_user_gets_empty_list_but_no_detail_access() -> None:
    client = _client()

    listed = client.get("/v1/query-history", headers={"X-User-Subject": "missing"})
    detail = client.get("/v1/query-history/run-1", headers={"X-User-Subject": "missing"})

    assert listed.status_code == 200
    assert listed.json()["data"]["items"] == []
    assert detail.status_code == 404


def _run(*, public_id: str, user_id: int, status: RunStatus, minutes_ago: int) -> QueryRun:
    now = _now() - timedelta(minutes=minutes_ago)
    return QueryRun(
        id=minutes_ago,
        public_id=public_id,
        thread_id=10,
        user_id=user_id,
        status=status,
        question_message_id=100 + minutes_ago,
        error_code="QUERY_TIMEOUT" if status is RunStatus.FAILED else None,
        error_message="query timeout" if status is RunStatus.FAILED else None,
        started_at=now,
        finished_at=now if status in {RunStatus.SUCCESS, RunStatus.FAILED} else None,
        created_at=now,
        updated_at=now,
    )


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
