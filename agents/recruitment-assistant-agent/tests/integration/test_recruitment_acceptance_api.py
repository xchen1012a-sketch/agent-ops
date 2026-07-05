"""Acceptance smoke tests for the recruitment MVP API closure."""

from __future__ import annotations

from time import perf_counter

from httpx import AsyncClient


async def test_recruitment_mvp_api_closes_main_flow_under_mock_boundary(
    app_client: AsyncClient,
) -> None:
    started_at = perf_counter()

    create_response = await app_client.post(
        "/v1/recruitment-tasks",
        json={
            "title": "Acceptance backend role",
            "resume_text": "Built Python APIs and supported stakeholders.",
            "jd_text": "Need Python service development and stakeholder communication.",
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["task"]["task_id"]

    run_response = await app_client.post(f"/v1/recruitment-tasks/{task_id}/runs", json={})
    assert run_response.status_code == 202
    run = run_response.json()["run"]
    assert run["status"] == "success"
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

    stream_response = await app_client.get(f"/v1/recruitment-runs/{run['run_id']}/stream")
    assert stream_response.status_code == 200
    assert "event: run.started" in stream_response.text
    assert "event: run.completed" in stream_response.text

    review_response = await app_client.post(
        f"/v1/admin/recruitment-tasks/{task_id}/review",
        json={"review_status": "approved", "review_note": "Acceptance approved."},
    )
    assert review_response.status_code == 200
    assert review_response.json()["review"]["review_status"] == "approved"

    override_response = await app_client.post(
        "/v1/admin/match-results/match_acceptance/override",
        json={
            "field_path": "overall_tier",
            "new_value": "medium",
            "reason": "Acceptance smoke manual review.",
        },
    )
    assert override_response.status_code == 200
    assert override_response.json()["override"]["field_path"] == "overall_tier"

    report_response = await app_client.post(f"/v1/recruitment-tasks/{task_id}/reports")
    assert report_response.status_code == 201
    report_id = report_response.json()["report"]["report_id"]

    detail_response = await app_client.get(f"/v1/recruitment-reports/{report_id}")
    assert detail_response.status_code == 200
    assert "Recruitment Analysis Report" in detail_response.json()["report"]["content_markdown"]

    md_response = await app_client.get(
        f"/v1/recruitment-reports/{report_id}/export", params={"format": "md"}
    )
    pdf_response = await app_client.get(
        f"/v1/recruitment-reports/{report_id}/export", params={"format": "pdf"}
    )
    assert md_response.status_code == 200
    assert pdf_response.status_code == 200
    assert pdf_response.content.startswith(b"%PDF-1.4")

    assert perf_counter() - started_at < 30
