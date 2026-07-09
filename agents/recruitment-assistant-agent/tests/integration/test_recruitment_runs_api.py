"""Integration tests for recruitment run MVP endpoints."""

from __future__ import annotations

from httpx import AsyncClient


async def test_start_and_get_recruitment_run(app_client: AsyncClient) -> None:
    create_response = await app_client.post(
        "/v1/recruitment-tasks",
        json={"title": "Run task", "resume_text": "Python APIs", "jd_text": "Python role"},
    )
    task_id = create_response.json()["task"]["task_id"]

    start_response = await app_client.post(
        f"/v1/recruitment-tasks/{task_id}/runs",
        json={"prompt_version": "recruit_prompt:v1", "workflow_version": "recruitment_workflow:v1"},
        headers={"x-request-id": "req-run-1"},
    )

    assert start_response.status_code == 202
    body = start_response.json()
    run = body["run"]
    assert body["request_id"] == "req-run-1"
    assert run["run_id"].startswith("run_")
    assert run["task_id"] == task_id
    assert run["status"] == "success"
    assert run["error_code"] is None
    assert run["node_trace"] == [
        "file_safety",
        "task_route",
        "resume_parse",
        "jd_parse",
        "evidence_match",
        "fairness_check",
        "gap_question_gen",
        "persist",
    ]
    assert body["stream_url"] == f"/v1/recruitment-runs/{run['run_id']}/stream"

    get_response = await app_client.get(f"/v1/recruitment-runs/{run['run_id']}")

    assert get_response.status_code == 200
    assert get_response.json()["run"]["run_id"] == run["run_id"]


async def test_stream_recruitment_run_events(app_client: AsyncClient) -> None:
    create_response = await app_client.post(
        "/v1/recruitment-tasks",
        json={"title": "Stream task", "resume_text": "Python", "jd_text": "FastAPI"},
    )
    task_id = create_response.json()["task"]["task_id"]
    start_response = await app_client.post(f"/v1/recruitment-tasks/{task_id}/runs", json={})
    run_id = start_response.json()["run"]["run_id"]

    stream_response = await app_client.get(
        f"/v1/recruitment-runs/{run_id}/stream",
        headers={"x-request-id": "req-stream-1"},
    )

    assert stream_response.status_code == 200
    assert stream_response.headers["content-type"].startswith("text/event-stream")
    text = stream_response.text
    assert "event: run.started" in text
    assert "event: node.completed" in text
    assert "event: run.completed" in text
    assert '"request_id": "req-stream-1"' in text
    assert '"node_name": "fairness_check"' in text


async def test_cancel_recruitment_run_is_idempotent(app_client: AsyncClient) -> None:
    create_response = await app_client.post(
        "/v1/recruitment-tasks",
        json={"title": "Cancel task"},
    )
    task_id = create_response.json()["task"]["task_id"]
    start_response = await app_client.post(f"/v1/recruitment-tasks/{task_id}/runs", json={})
    run_id = start_response.json()["run"]["run_id"]

    cancel_response = await app_client.post(f"/v1/recruitment-runs/{run_id}/cancel")
    second_cancel_response = await app_client.post(f"/v1/recruitment-runs/{run_id}/cancel")
    stream_response = await app_client.get(f"/v1/recruitment-runs/{run_id}/stream")

    assert cancel_response.status_code == 200
    assert second_cancel_response.status_code == 200
    run = cancel_response.json()["run"]
    assert run["status"] == "canceled"
    assert run["error_code"] == "CANCELED"
    assert stream_response.text.count("event: run.canceled") == 1


async def test_run_start_rejects_oversized_version(app_client: AsyncClient) -> None:
    create_response = await app_client.post(
        "/v1/recruitment-tasks",
        json={"title": "Oversized version"},
    )
    task_id = create_response.json()["task"]["task_id"]

    response = await app_client.post(
        f"/v1/recruitment-tasks/{task_id}/runs",
        json={"prompt_version": "x" * 81},
    )

    assert response.status_code == 422


async def test_unknown_recruitment_run_returns_not_found(app_client: AsyncClient) -> None:
    response = await app_client.get("/v1/recruitment-runs/run_missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RUN_NOT_FOUND"


async def test_recruitment_runs_available_on_legacy_prefix(app_client: AsyncClient) -> None:
    create_response = await app_client.post(
        "/api/recruitment/v1/recruitment-tasks",
        json={"title": "Legacy run"},
    )
    task_id = create_response.json()["task"]["task_id"]

    response = await app_client.post(
        f"/api/recruitment/v1/recruitment-tasks/{task_id}/runs",
        json={},
    )

    assert response.status_code == 202
    assert response.json()["run"]["task_id"] == task_id
