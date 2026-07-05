"""Integration tests for recruitment report MVP endpoints."""

from __future__ import annotations

from httpx import AsyncClient


async def _approved_task_id(app_client: AsyncClient) -> str:
    create_response = await app_client.post(
        "/v1/recruitment-tasks",
        json={"title": "Report task", "resume_text": "Python", "jd_text": "FastAPI"},
    )
    task_id = create_response.json()["task"]["task_id"]
    run_response = await app_client.post(f"/v1/recruitment-tasks/{task_id}/runs", json={})
    assert run_response.status_code == 202
    review_response = await app_client.post(
        f"/v1/admin/recruitment-tasks/{task_id}/review",
        json={"review_status": "approved", "review_note": "Approved for report."},
    )
    assert review_response.status_code == 200
    return task_id


async def test_create_report_requires_admin_approval(app_client: AsyncClient) -> None:
    create_response = await app_client.post(
        "/v1/recruitment-tasks",
        json={"title": "Needs review"},
    )
    task_id = create_response.json()["task"]["task_id"]

    response = await app_client.post(f"/v1/recruitment-tasks/{task_id}/reports")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "REVIEW_REQUIRED"


async def test_create_and_get_recruitment_report(app_client: AsyncClient) -> None:
    task_id = await _approved_task_id(app_client)

    create_response = await app_client.post(
        f"/v1/recruitment-tasks/{task_id}/reports",
        headers={"x-request-id": "req-report"},
    )

    assert create_response.status_code == 201
    body = create_response.json()
    report = body["report"]
    assert body["request_id"] == "req-report"
    assert report["report_id"].startswith("report_")
    assert report["task_id"] == task_id
    assert report["status"] == "ready"
    assert report["format_available"] == ["md", "pdf"]

    detail_response = await app_client.get(f"/v1/recruitment-reports/{report['report_id']}")

    assert detail_response.status_code == 200
    detail = detail_response.json()["report"]
    assert detail["report_id"] == report["report_id"]
    assert "# Recruitment Analysis Report" in detail["content_markdown"]


async def test_export_recruitment_report_as_markdown_and_pdf(app_client: AsyncClient) -> None:
    task_id = await _approved_task_id(app_client)
    create_response = await app_client.post(f"/v1/recruitment-tasks/{task_id}/reports")
    report_id = create_response.json()["report"]["report_id"]

    md_response = await app_client.get(
        f"/v1/recruitment-reports/{report_id}/export", params={"format": "md"}
    )
    pdf_response = await app_client.get(
        f"/v1/recruitment-reports/{report_id}/export", params={"format": "pdf"}
    )

    assert md_response.status_code == 200
    assert md_response.headers["content-type"].startswith("text/markdown")
    assert "Recruitment Analysis Report" in md_response.text
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert pdf_response.content.startswith(b"%PDF-1.4")


async def test_unknown_recruitment_report_returns_not_found(app_client: AsyncClient) -> None:
    response = await app_client.get("/v1/recruitment-reports/report_missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "REPORT_NOT_FOUND"


async def test_reports_available_on_legacy_prefix(app_client: AsyncClient) -> None:
    create_response = await app_client.post(
        "/api/recruitment/v1/recruitment-tasks",
        json={"title": "Legacy report"},
    )
    task_id = create_response.json()["task"]["task_id"]
    review_response = await app_client.post(
        f"/api/recruitment/v1/admin/recruitment-tasks/{task_id}/review",
        json={"review_status": "approved"},
    )
    assert review_response.status_code == 200

    response = await app_client.post(f"/api/recruitment/v1/recruitment-tasks/{task_id}/reports")

    assert response.status_code == 201
    assert response.json()["report"]["task_id"] == task_id
