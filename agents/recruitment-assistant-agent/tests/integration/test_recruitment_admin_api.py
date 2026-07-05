"""Integration tests for recruitment admin MVP endpoints."""

from __future__ import annotations

from httpx import AsyncClient


async def test_admin_task_detail_includes_latest_run(app_client: AsyncClient) -> None:
    create_response = await app_client.post(
        "/v1/recruitment-tasks",
        json={"title": "Admin detail", "resume_text": "Python", "jd_text": "FastAPI"},
    )
    task_id = create_response.json()["task"]["task_id"]
    run_response = await app_client.post(f"/v1/recruitment-tasks/{task_id}/runs", json={})
    run_id = run_response.json()["run"]["run_id"]

    response = await app_client.get(
        f"/v1/admin/recruitment-tasks/{task_id}",
        headers={"x-request-id": "req-admin-detail"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["request_id"] == "req-admin-detail"
    assert body["task"]["task_id"] == task_id
    assert body["latest_run"]["run_id"] == run_id
    assert body["review"] is None


async def test_admin_review_updates_task_review_status(app_client: AsyncClient) -> None:
    create_response = await app_client.post(
        "/v1/recruitment-tasks",
        json={"title": "Review me"},
    )
    task_id = create_response.json()["task"]["task_id"]

    review_response = await app_client.post(
        f"/v1/admin/recruitment-tasks/{task_id}/review",
        json={"review_status": "approved", "review_note": "Ready for interview."},
        headers={"x-request-id": "req-review"},
    )
    detail_response = await app_client.get(f"/v1/admin/recruitment-tasks/{task_id}")

    assert review_response.status_code == 200
    body = review_response.json()
    assert body["request_id"] == "req-review"
    assert body["review"]["review_status"] == "approved"
    assert body["review"]["reviewed_by"] == "admin_mvp"
    assert detail_response.json()["task"]["review_status"] == "approved"
    assert detail_response.json()["review"]["review_note"] == "Ready for interview."


async def test_admin_manual_override_records_supported_field(app_client: AsyncClient) -> None:
    response = await app_client.post(
        "/v1/admin/match-results/match_demo/override",
        json={
            "field_path": "match_items[1].match_status",
            "new_value": "partial",
            "reason": "Candidate mentioned Kubernetes operations.",
        },
    )

    assert response.status_code == 200
    override = response.json()["override"]
    assert override["override_id"].startswith("override_")
    assert override["match_result_id"] == "match_demo"
    assert override["field_path"] == "match_items[1].match_status"
    assert override["old_value"] is None
    assert override["new_value"] == "partial"


async def test_admin_manual_override_rejects_unsupported_field(app_client: AsyncClient) -> None:
    response = await app_client.post(
        "/v1/admin/match-results/match_demo/override",
        json={
            "field_path": "candidate.age",
            "new_value": "30",
            "reason": "Not allowed.",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INPUT_BLOCKED"


async def test_admin_endpoints_available_on_legacy_prefix(app_client: AsyncClient) -> None:
    create_response = await app_client.post(
        "/api/recruitment/v1/recruitment-tasks",
        json={"title": "Legacy admin"},
    )
    task_id = create_response.json()["task"]["task_id"]

    response = await app_client.post(
        f"/api/recruitment/v1/admin/recruitment-tasks/{task_id}/review",
        json={"review_status": "changes_requested"},
    )

    assert response.status_code == 200
    assert response.json()["review"]["review_status"] == "changes_requested"
