"""Integration tests for recruitment task MVP endpoints."""

from __future__ import annotations

from httpx import AsyncClient


async def test_create_and_get_recruitment_task(app_client: AsyncClient) -> None:
    response = await app_client.post(
        "/v1/recruitment-tasks",
        json={
            "title": "Backend Engineer review",
            "priority": "normal",
            "resume_text": "Built Python APIs.",
            "jd_text": "Need Python and Kubernetes.",
        },
        headers={"x-request-id": "req-test-1"},
    )

    assert response.status_code == 201
    body = response.json()
    task = body["task"]
    assert body["request_id"] == "req-test-1"
    assert task["task_id"].startswith("task_")
    assert task["status"] == "uploaded"
    assert task["review_status"] == "pending"
    assert task["material_summary"]["has_resume"] is True
    assert task["material_summary"]["has_jd"] is True

    detail_response = await app_client.get(f"/v1/recruitment-tasks/{task['task_id']}")

    assert detail_response.status_code == 200
    detail = detail_response.json()["task"]
    assert detail["title"] == "Backend Engineer review"
    assert len(detail["materials"]) == 2
    assert {material["kind"] for material in detail["materials"]} == {"resume", "jd"}
    assert detail["analysis"]["rule_version"] == "recruitment_mvp:v1"
    assert detail["analysis"]["match_score"] > 0
    assert detail["analysis"]["matched_keywords"] == ["python"]
    assert "kubernetes" in detail["analysis"]["missing_keywords"]
    assert detail["analysis"]["interview_questions"]


async def test_list_recruitment_tasks_supports_status_filter(app_client: AsyncClient) -> None:
    first = await app_client.post(
        "/v1/recruitment-tasks",
        json={"title": "First", "resume_text": "A", "jd_text": "B"},
    )
    second = await app_client.post(
        "/v1/recruitment-tasks",
        json={"title": "Second"},
    )

    assert first.status_code == 201
    assert second.status_code == 201

    response = await app_client.get("/v1/recruitment-tasks", params={"status": "uploaded"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2
    assert all(item["status"] == "uploaded" for item in body["items"])


async def test_delete_recruitment_task_hides_task(app_client: AsyncClient) -> None:
    create_response = await app_client.post(
        "/v1/recruitment-tasks",
        json={"title": "Delete me"},
    )
    task_id = create_response.json()["task"]["task_id"]

    delete_response = await app_client.delete(f"/v1/recruitment-tasks/{task_id}")
    get_response = await app_client.get(f"/v1/recruitment-tasks/{task_id}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "TASK_NOT_FOUND"


async def test_recruitment_tasks_available_on_legacy_prefix(app_client: AsyncClient) -> None:
    response = await app_client.post(
        "/api/recruitment/v1/recruitment-tasks",
        json={"title": "Legacy prefix"},
    )

    assert response.status_code == 201
