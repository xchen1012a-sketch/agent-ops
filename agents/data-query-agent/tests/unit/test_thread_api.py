"""Unit tests for thread API contract slice."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from data_query_agent.api.dependencies import get_identity_thread_service
from data_query_agent.domain.entities.identity import QueryThread, ThreadStatus
from data_query_agent.main import create_app


class FakeIdentityThreadService:
    """Fake service for API boundary tests."""

    def __init__(self) -> None:
        self.threads_by_subject: dict[str, list[QueryThread]] = {}
        self.next_id = 1

    async def create_thread_for_subject(
        self,
        *,
        external_subject: str,
        title: str | None,
        role: object | None = None,
        display_name: str | None = None,
    ) -> QueryThread:
        now = datetime.now(UTC).replace(tzinfo=None)
        thread = QueryThread(
            id=self.next_id,
            public_id=f"thread-{self.next_id}",
            user_id=abs(hash(external_subject)) % 10000,
            title=title,
            status=ThreadStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        self.next_id += 1
        self.threads_by_subject.setdefault(external_subject, []).append(thread)
        return thread

    async def list_owned_threads(
        self,
        *,
        external_subject: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[QueryThread]:
        threads = self.threads_by_subject.get(external_subject, [])
        return tuple(threads[offset : offset + limit])

    async def get_owned_thread(
        self,
        *,
        thread_public_id: str,
        external_subject: str,
    ) -> QueryThread | None:
        for thread in self.threads_by_subject.get(external_subject, []):
            if thread.public_id == thread_public_id:
                return thread
        return None


def _client(service: FakeIdentityThreadService) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_identity_thread_service] = lambda: service
    return TestClient(app)


def test_create_thread_returns_enveloped_public_dto() -> None:
    service = FakeIdentityThreadService()
    client = _client(service)

    response = client.post(
        "/v1/threads",
        headers={"X-User-Subject": "user-a"},
        json={"title": "Sales analysis"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["error"] is None
    assert body["data"]["thread_id"] == "thread-1"
    assert body["data"]["title"] == "Sales analysis"
    assert body["data"]["status"] == "active"
    assert "user_id" not in body["data"]


def test_list_threads_is_scoped_to_current_subject_and_paginated() -> None:
    service = FakeIdentityThreadService()
    client = _client(service)
    client.post("/v1/threads", headers={"X-User-Subject": "user-a"}, json={"title": "A1"})
    client.post("/v1/threads", headers={"X-User-Subject": "user-a"}, json={"title": "A2"})
    client.post("/v1/threads", headers={"X-User-Subject": "user-b"}, json={"title": "B1"})

    response = client.get(
        "/v1/threads?limit=1&offset=1",
        headers={"X-User-Subject": "user-a"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["limit"] == 1
    assert body["data"]["offset"] == 1
    assert [item["title"] for item in body["data"]["items"]] == ["A2"]


def test_get_thread_blocks_cross_subject_access() -> None:
    service = FakeIdentityThreadService()
    client = _client(service)
    created = client.post(
        "/v1/threads",
        headers={"X-User-Subject": "owner"},
        json={"title": "Owned"},
    ).json()

    owned = client.get(
        f"/v1/threads/{created['data']['thread_id']}",
        headers={"X-User-Subject": "owner"},
    )
    blocked = client.get(
        f"/v1/threads/{created['data']['thread_id']}",
        headers={"X-User-Subject": "other"},
    )

    assert owned.status_code == 200
    assert owned.json()["data"]["title"] == "Owned"
    assert blocked.status_code == 404
    assert blocked.json()["error"]["code"] == "NOT_FOUND"


def test_thread_api_requires_subject_header() -> None:
    client = _client(FakeIdentityThreadService())

    response = client.get("/v1/threads")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"
