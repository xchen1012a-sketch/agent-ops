"""Unit tests for workflow audit status mapping."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from legal_consulting_agent.application.services import (
    LegalDataService,
    LegalWorkflowAuditService,
    map_workflow_error,
)
from legal_consulting_agent.domain.entities.legal_data import AgentRun, LegalSession, NodeRun
from legal_consulting_agent.domain.value_objects.legal_enums import RunStatus, SessionStatus
from legal_consulting_agent.workflows.legal_state import LegalWorkflowState


class FakeAuditRepository:
    """Minimal repository double for workflow audit tests."""

    def __init__(self) -> None:
        self.session = LegalSession(
            id=10,
            public_id="thread-public-id",
            user_id=1,
            category_id=2,
            title=None,
            status=SessionStatus.ACTIVE,
            last_message_at=None,
        )
        self.agent_runs: list[AgentRun] = []
        self.node_runs: list[NodeRun] = []

    async def get_session_for_user(
        self,
        *,
        session_public_id: str,
        user_id: int,
    ) -> LegalSession | None:
        if self.session.public_id == session_public_id and self.session.user_id == user_id:
            return self.session
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


def base_state() -> LegalWorkflowState:
    return {
        "thread_id": "thread-public-id",
        "user_id": 1,
        "question": "公司单方面调岗，我可以拒绝吗？",
        "prompt_version": "legal_generation:v1",
        "workflow_version": "legal_workflow:v1",
    }


def test_map_workflow_error_marks_retryable_errors_as_retrying() -> None:
    mapping = map_workflow_error("RETRIEVAL_FAILED")

    assert mapping.status is RunStatus.RETRYING
    assert mapping.retryable is True


def test_map_workflow_error_marks_non_retryable_errors_as_failed() -> None:
    mapping = map_workflow_error("INPUT_BLOCKED")

    assert mapping.status is RunStatus.FAILED
    assert mapping.retryable is False


@pytest.mark.asyncio
async def test_audit_service_creates_run_and_node_start_record() -> None:
    repo = FakeAuditRepository()
    audit_service = LegalWorkflowAuditService(LegalDataService(repo))
    started_at = datetime(2026, 7, 5, 13, 0, 0)

    run = await audit_service.start_run(state=base_state(), started_at=started_at)
    node = await audit_service.record_node_started(
        run_id=run.id or 0,
        node_name="retrieval",
        started_at=started_at,
    )

    assert run.status is RunStatus.PENDING
    assert node.status is RunStatus.RUNNING
    assert node.metadata == {"event": "started", "node_name": "retrieval"}


@pytest.mark.asyncio
async def test_audit_service_records_successful_node_finish() -> None:
    repo = FakeAuditRepository()
    audit_service = LegalWorkflowAuditService(LegalDataService(repo))
    state = base_state()
    state["category"] = "civil_labor"
    state["chunks"] = []
    started_at = datetime(2026, 7, 5, 13, 0, 0)
    finished_at = started_at + timedelta(milliseconds=25)

    node = await audit_service.record_node_finished(
        run_id=1,
        node_name="retrieval",
        state=state,
        started_at=started_at,
        finished_at=finished_at,
    )

    assert node.status is RunStatus.SUCCESS
    assert node.error_code is None
    assert node.duration_ms == 25
    assert node.metadata == {
        "event": "finished",
        "node_name": "retrieval",
        "retryable": False,
        "category": "civil_labor",
        "chunks_count": 0,
    }


@pytest.mark.asyncio
async def test_audit_service_records_retryable_failure() -> None:
    repo = FakeAuditRepository()
    audit_service = LegalWorkflowAuditService(LegalDataService(repo))
    state = base_state()
    state["error_code"] = "DB_UNAVAILABLE"
    started_at = datetime(2026, 7, 5, 13, 0, 0)

    node = await audit_service.record_node_finished(
        run_id=1,
        node_name="persist",
        state=state,
        started_at=started_at,
        finished_at=started_at,
    )

    assert node.status is RunStatus.RETRYING
    assert node.error_code == "DB_UNAVAILABLE"
    assert node.metadata == {
        "event": "finished",
        "node_name": "persist",
        "retryable": True,
    }
