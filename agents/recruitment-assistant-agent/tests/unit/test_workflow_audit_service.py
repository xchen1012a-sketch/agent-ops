"""Unit tests for recruitment workflow audit status mapping."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from recruitment_assistant_agent.application.services import (
    RecruitDataService,
    RecruitmentWorkflowAuditService,
    map_workflow_error,
)
from recruitment_assistant_agent.domain.entities.recruit_data import (
    AgentRun,
    NodeRun,
    RecruitTask,
    UserMirror,
)
from recruitment_assistant_agent.domain.value_objects.recruit_enums import (
    ReviewStatus,
    RunStatus,
    TaskPriority,
    TaskStatus,
    UserRole,
    UserStatus,
)
from recruitment_assistant_agent.workflows.recruitment_state import RecruitmentWorkflowState


class FakeAuditRepository:
    """Minimal repository double for workflow audit tests."""

    def __init__(self) -> None:
        self.user = UserMirror(
            id=1,
            public_id="user-public-1",
            email="user@example.com",
            display_name="Recruiter",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        self.task = RecruitTask(
            id=10,
            public_id="task-public-1",
            user_id=1,
            title="Backend Engineer",
            status=TaskStatus.UPLOADED,
            priority=TaskPriority.NORMAL,
            review_status=ReviewStatus.PENDING,
            reviewed_by=None,
            reviewed_at=None,
        )
        self.agent_runs: list[AgentRun] = []
        self.node_runs: list[NodeRun] = []

    async def get_user_by_public_id(self, public_id: str) -> UserMirror | None:
        if public_id == self.user.public_id:
            return self.user
        return None

    async def get_task_for_user(
        self,
        *,
        task_public_id: str,
        user_id: int,
    ) -> RecruitTask | None:
        if self.task.public_id == task_public_id and self.task.user_id == user_id:
            return self.task
        return None

    async def create_agent_run(self, run: AgentRun) -> AgentRun:
        persisted = AgentRun(
            id=len(self.agent_runs) + 1,
            public_id=run.public_id,
            thread_id=run.thread_id,
            user_id=run.user_id,
            workflow_version=run.workflow_version,
            prompt_version=run.prompt_version,
            status=run.status,
            retry_count=run.retry_count,
            error_code=run.error_code,
            error_summary=run.error_summary,
            started_at=run.started_at,
            finished_at=run.finished_at,
            duration_ms=run.duration_ms,
        )
        self.agent_runs.append(persisted)
        return persisted

    async def update_agent_run(self, run: AgentRun) -> AgentRun:
        persisted = AgentRun(
            id=run.id,
            public_id=run.public_id,
            thread_id=run.thread_id,
            user_id=run.user_id,
            workflow_version=run.workflow_version,
            prompt_version=run.prompt_version,
            status=run.status,
            retry_count=run.retry_count,
            error_code=run.error_code,
            error_summary=run.error_summary,
            started_at=run.started_at,
            finished_at=run.finished_at,
            duration_ms=run.duration_ms,
        )
        self.agent_runs[(run.id or 1) - 1] = persisted
        return persisted

    async def create_node_run(self, node_run: NodeRun) -> NodeRun:
        persisted = NodeRun(
            id=len(self.node_runs) + 1,
            run_id=node_run.run_id,
            node_name=node_run.node_name,
            status=node_run.status,
            duration_ms=node_run.duration_ms,
            error_code=node_run.error_code,
            metadata=node_run.metadata,
            started_at=node_run.started_at,
            finished_at=node_run.finished_at,
        )
        self.node_runs.append(persisted)
        return persisted

    async def update_node_run(self, node_run: NodeRun) -> NodeRun:
        persisted = NodeRun(
            id=node_run.id,
            run_id=node_run.run_id,
            node_name=node_run.node_name,
            status=node_run.status,
            duration_ms=node_run.duration_ms,
            error_code=node_run.error_code,
            metadata=node_run.metadata,
            started_at=node_run.started_at,
            finished_at=node_run.finished_at,
        )
        self.node_runs[(node_run.id or 1) - 1] = persisted
        return persisted


def base_state() -> RecruitmentWorkflowState:
    return {
        "thread_id": "task-public-1",
        "user_id": 1,
        "task_id": 10,
        "material_kind": "resume_jd",
        "prompt_version": "recruitment_workflow:v1",
        "workflow_version": "recruitment_workflow:v1",
    }


async def started_node(
    audit_service: RecruitmentWorkflowAuditService,
    *,
    node_name: str,
    started_at: datetime,
) -> NodeRun:
    return await audit_service.record_node_started(
        run_id=1,
        node_name=node_name,
        started_at=started_at,
    )


def test_map_workflow_error_marks_retryable_errors_as_retrying() -> None:
    mapping = map_workflow_error("PARSE_FAILED")

    assert mapping.status is RunStatus.RETRYING
    assert mapping.retryable is True


def test_map_workflow_error_marks_non_retryable_errors_as_failed() -> None:
    mapping = map_workflow_error("FAIRNESS_VIOLATION")

    assert mapping.status is RunStatus.FAILED
    assert mapping.retryable is False


def test_map_workflow_error_marks_success_and_canceled() -> None:
    success = map_workflow_error(None)
    canceled = map_workflow_error("CANCELED")

    assert success.status is RunStatus.SUCCESS
    assert success.retryable is False
    assert canceled.status is RunStatus.CANCELED
    assert canceled.retryable is False


@pytest.mark.asyncio
async def test_audit_service_creates_run_and_node_start_record() -> None:
    repo = FakeAuditRepository()
    audit_service = RecruitmentWorkflowAuditService(RecruitDataService(repo))
    started_at = datetime(2026, 7, 5, 14, 0, 0)

    run = await audit_service.start_run(
        user_public_id="user-public-1",
        state=base_state(),
        started_at=started_at,
    )
    node = await audit_service.record_node_started(
        run_id=run.id or 0,
        node_name="resume_parse",
        started_at=started_at,
    )

    assert run.status is RunStatus.PENDING
    assert run.thread_id == "task-public-1"
    assert node.status is RunStatus.RUNNING
    assert node.metadata == {"event": "started", "node_name": "resume_parse"}


@pytest.mark.asyncio
async def test_audit_service_records_successful_node_finish_metadata() -> None:
    repo = FakeAuditRepository()
    audit_service = RecruitmentWorkflowAuditService(RecruitDataService(repo))
    state = base_state()
    state["overall_tier"] = "medium"
    state["match_items"] = [
        {"requirement": "Python", "match_status": "match", "evidence_snippet": "Python services."}
    ]
    state["gaps"] = []
    started_at = datetime(2026, 7, 5, 14, 0, 0)
    finished_at = started_at + timedelta(milliseconds=25)

    node_run = await started_node(
        audit_service,
        node_name="evidence_match",
        started_at=started_at,
    )
    node = await audit_service.record_node_finished(
        node_run=node_run,
        state=state,
        finished_at=finished_at,
    )

    assert node.status is RunStatus.SUCCESS
    assert node.error_code is None
    assert node.duration_ms == 25
    assert node.metadata == {
        "event": "finished",
        "node_name": "evidence_match",
        "retryable": False,
        "has_overall_tier": True,
        "match_items_count": 1,
        "gaps_count": 0,
    }


@pytest.mark.asyncio
async def test_audit_service_records_retryable_failure() -> None:
    repo = FakeAuditRepository()
    audit_service = RecruitmentWorkflowAuditService(RecruitDataService(repo))
    state = base_state()
    state["error_code"] = "DB_UNAVAILABLE"
    started_at = datetime(2026, 7, 5, 14, 0, 0)

    node_run = await started_node(
        audit_service,
        node_name="persist",
        started_at=started_at,
    )
    node = await audit_service.record_node_finished(
        node_run=node_run,
        state=state,
        finished_at=started_at,
    )

    assert node.status is RunStatus.RETRYING
    assert node.error_code == "DB_UNAVAILABLE"
    assert node.metadata == {
        "event": "finished",
        "node_name": "persist",
        "retryable": True,
    }


@pytest.mark.asyncio
async def test_audit_service_records_fairness_failure_without_sensitive_values() -> None:
    repo = FakeAuditRepository()
    audit_service = RecruitmentWorkflowAuditService(RecruitDataService(repo))
    state = base_state()
    state["error_code"] = "FAIRNESS_VIOLATION"
    state["fairness_violation_details"] = ["gender"]
    started_at = datetime(2026, 7, 5, 14, 0, 0)

    node_run = await started_node(
        audit_service,
        node_name="fairness_check",
        started_at=started_at,
    )
    node = await audit_service.record_node_finished(
        node_run=node_run,
        state=state,
        finished_at=started_at,
    )

    assert node.status is RunStatus.FAILED
    assert node.error_code == "FAIRNESS_VIOLATION"
    assert node.metadata == {
        "event": "finished",
        "node_name": "fairness_check",
        "retryable": False,
        "has_fairness_violation": True,
    }


@pytest.mark.asyncio
async def test_audit_service_sanitizes_unknown_error_code() -> None:
    repo = FakeAuditRepository()
    audit_service = RecruitmentWorkflowAuditService(RecruitDataService(repo))
    state = base_state()
    state["error_code"] = "candidate gender leaked in adapter exception"
    started_at = datetime(2026, 7, 5, 14, 0, 0)

    node_run = await started_node(
        audit_service,
        node_name="resume_parse",
        started_at=started_at,
    )
    node = await audit_service.record_node_finished(
        node_run=node_run,
        state=state,
        finished_at=started_at,
    )

    assert node.status is RunStatus.FAILED
    assert node.error_code == "UNKNOWN_WORKFLOW_ERROR"
    assert node.metadata == {
        "event": "finished",
        "node_name": "resume_parse",
        "retryable": False,
    }
