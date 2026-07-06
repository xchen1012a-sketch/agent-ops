"""Unit tests for the RECRUIT-240 application runner boundary."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from recruitment_assistant_agent.application.services import (
    RecruitDataService,
    RecruitmentWorkflowAuditService,
    RecruitmentWorkflowRunnerService,
    WorkflowNodeSpec,
    mark_canceled,
    prepare_retry_state,
)
from recruitment_assistant_agent.domain.value_objects.recruit_enums import RunStatus
from recruitment_assistant_agent.workflows.recruitment_state import (
    RecruitmentWorkflowState,
    RecruitmentWorkflowUpdate,
)
from tests.unit.test_workflow_audit_service import FakeAuditRepository


class FixedClock:
    """Deterministic monotonic clock for runner tests."""

    def __init__(self) -> None:
        self._current = datetime(2026, 7, 5, 15, 0, 0)

    def __call__(self) -> datetime:
        value = self._current
        self._current = self._current + timedelta(milliseconds=10)
        return value


def base_state() -> RecruitmentWorkflowState:
    return {
        "thread_id": "task-public-1",
        "user_id": 1,
        "task_id": 10,
        "material_kind": "resume_jd",
        "prompt_version": "recruitment_workflow:v1",
        "workflow_version": "recruitment_workflow:v1",
    }


def state_with_mock_inputs() -> RecruitmentWorkflowState:
    state = base_state()
    state["mock_resume"] = {
        "summary": "Python backend engineer.",
        "skills": [
            {"skill_name": "Python", "evidence_snippet": "Built Python services."},
        ],
        "experiences": [],
        "educations": [],
        "soft_skills": [],
    }
    state["mock_jd"] = {
        "requirements": [
            {"requirement_type": "must_have", "text": "Python service development"},
            {"requirement_type": "nice_to_have", "text": "Kubernetes operations"},
        ]
    }
    return state


def build_runner(repo: FakeAuditRepository) -> RecruitmentWorkflowRunnerService:
    return RecruitmentWorkflowRunnerService(
        audit_service=RecruitmentWorkflowAuditService(RecruitDataService(repo)),
        now=FixedClock(),
    )


@pytest.mark.asyncio
async def test_runner_executes_nodes_in_order_and_records_audits() -> None:
    repo = FakeAuditRepository()
    runner = build_runner(repo)

    result = await runner.run_once(state_with_mock_inputs(), user_public_id="user-public-1")

    assert result.stopped_at_node is None
    assert result.state["error_code"] is None
    assert result.state["persisted"] is True
    assert repo.agent_runs[0].status is RunStatus.SUCCESS
    assert result.state["node_trace"] == [
        "file_safety",
        "task_route",
        "resume_parse",
        "jd_parse",
        "evidence_match",
        "fairness_check",
        "gap_question_gen",
        "persist",
    ]
    assert len(repo.node_runs) == 8
    assert [node.status for node in repo.node_runs] == [RunStatus.SUCCESS] * 8


@pytest.mark.asyncio
async def test_runner_redacts_sensitive_field_and_completes() -> None:
    repo = FakeAuditRepository()
    runner = build_runner(repo)
    state = state_with_mock_inputs()
    state["mock_resume"]["gender"] = "redacted"

    result = await runner.run_once(state, user_public_id="user-public-1")

    # Choice B: the protected attribute is stripped and the run completes on a
    # fair payload, with the redaction recorded for audit — no hard stop.
    assert result.stopped_at_node is None
    assert result.state["error_code"] is None
    assert result.state["persisted"] is True
    assert result.state["fairness_passed"] is True
    assert result.state["fairness_violation_details"] == ["gender"]
    assert "gender" not in result.state["resume_structure"]
    assert repo.agent_runs[0].status is RunStatus.SUCCESS
    assert len(repo.node_runs) == 8
    assert [node.status for node in repo.node_runs] == [RunStatus.SUCCESS] * 8
    fairness_run = repo.node_runs[5]
    assert fairness_run.metadata["node_name"] == "fairness_check"
    assert fairness_run.metadata["has_fairness_violation"] is True


@pytest.mark.asyncio
async def test_runner_records_retryable_persist_failure() -> None:
    repo = FakeAuditRepository()
    runner = build_runner(repo)
    state = state_with_mock_inputs()
    state["simulate_db_unavailable"] = True

    result = await runner.run_once(state, user_public_id="user-public-1")

    assert result.stopped_at_node == "persist"
    assert result.state["error_code"] == "DB_UNAVAILABLE"
    assert repo.agent_runs[0].status is RunStatus.RETRYING
    assert repo.agent_runs[0].error_code == "DB_UNAVAILABLE"
    assert repo.node_runs[-1].node_name == "persist"
    assert repo.node_runs[-1].status is RunStatus.RETRYING
    assert repo.node_runs[-1].error_code == "DB_UNAVAILABLE"
    assert repo.node_runs[-1].metadata == {
        "event": "finished",
        "node_name": "persist",
        "retryable": True,
        "has_overall_tier": True,
        "match_items_count": 2,
        "gaps_count": 1,
        "has_fairness_violation": False,
    }


@pytest.mark.asyncio
async def test_runner_cancel_entry_does_not_execute_nodes() -> None:
    repo = FakeAuditRepository()
    runner = build_runner(repo)

    result = await runner.run_once(
        state_with_mock_inputs(),
        user_public_id="user-public-1",
        cancel_requested=True,
    )

    assert result.stopped_at_node is None
    assert result.state["error_code"] == "CANCELED"
    assert result.state["persisted"] is False
    assert repo.agent_runs[0].status is RunStatus.CANCELED
    assert repo.agent_runs[0].error_code == "CANCELED"
    assert repo.node_runs == []


@pytest.mark.asyncio
async def test_runner_records_sanitized_failure_when_node_raises() -> None:
    def raising_node(state: RecruitmentWorkflowState) -> RecruitmentWorkflowUpdate:
        raise RuntimeError("raw candidate gender leaked")

    repo = FakeAuditRepository()
    runner = RecruitmentWorkflowRunnerService(
        audit_service=RecruitmentWorkflowAuditService(RecruitDataService(repo)),
        nodes=(WorkflowNodeSpec("explode", raising_node),),
        now=FixedClock(),
    )

    result = await runner.run_once(base_state(), user_public_id="user-public-1")

    assert result.stopped_at_node == "explode"
    assert result.state["error_code"] == "UNKNOWN_WORKFLOW_ERROR"
    assert result.state["persisted"] is False
    assert repo.agent_runs[0].status is RunStatus.FAILED
    assert repo.agent_runs[0].error_code == "UNKNOWN_WORKFLOW_ERROR"
    assert [node.status for node in repo.node_runs] == [RunStatus.FAILED]
    assert repo.node_runs[-1].error_code == "UNKNOWN_WORKFLOW_ERROR"
    assert "gender" not in str(repo.node_runs[-1].metadata)


def test_retry_and_cancel_state_helpers() -> None:
    failed_state = state_with_mock_inputs()
    failed_state["error_code"] = "DB_UNAVAILABLE"
    failed_state["node_trace"] = ["persist"]

    retry_state = prepare_retry_state(failed_state)
    canceled_state = mark_canceled(failed_state)

    assert "error_code" not in retry_state
    assert retry_state["node_trace"] == []
    assert canceled_state["error_code"] == "CANCELED"
    assert canceled_state["persisted"] is False
