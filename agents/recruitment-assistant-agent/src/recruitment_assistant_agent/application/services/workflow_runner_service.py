"""Application runner for deterministic RECRUIT-240 workflow slices."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import cast

from recruitment_assistant_agent.application.services.workflow_audit_service import (
    UNKNOWN_WORKFLOW_ERROR,
    RecruitmentWorkflowAuditService,
)
from recruitment_assistant_agent.workflows.recruitment_nodes import (
    evidence_match_node,
    fairness_check_node,
    file_safety_node,
    gap_question_gen_node,
    jd_parse_node,
    persist_node,
    resume_parse_node,
    task_route_node,
)
from recruitment_assistant_agent.workflows.recruitment_state import (
    RecruitmentWorkflowState,
    RecruitmentWorkflowUpdate,
)

WorkflowNode = Callable[[RecruitmentWorkflowState], RecruitmentWorkflowUpdate]


@dataclass(frozen=True, slots=True)
class WorkflowNodeSpec:
    """A named workflow node callable used by the application runner."""

    name: str
    handler: WorkflowNode


@dataclass(frozen=True, slots=True)
class WorkflowRunResult:
    """Result returned by a deterministic runner invocation."""

    run_id: int
    state: RecruitmentWorkflowState
    stopped_at_node: str | None


DEFAULT_WORKFLOW_NODES: tuple[WorkflowNodeSpec, ...] = (
    WorkflowNodeSpec("file_safety", file_safety_node),
    WorkflowNodeSpec("task_route", task_route_node),
    WorkflowNodeSpec("resume_parse", resume_parse_node),
    WorkflowNodeSpec("jd_parse", jd_parse_node),
    WorkflowNodeSpec("evidence_match", evidence_match_node),
    WorkflowNodeSpec("fairness_check", fairness_check_node),
    WorkflowNodeSpec("gap_question_gen", gap_question_gen_node),
    WorkflowNodeSpec("persist", persist_node),
)


def merge_workflow_update(
    state: RecruitmentWorkflowState,
    update: RecruitmentWorkflowUpdate,
) -> RecruitmentWorkflowState:
    """Merge a node update into state without mutating the caller's object."""

    return cast(RecruitmentWorkflowState, {**state, **update})


def prepare_retry_state(state: RecruitmentWorkflowState) -> RecruitmentWorkflowState:
    """Create a clean retry state preserving caller input and adapter fixtures."""

    retry_state = dict(state)
    retry_state.pop("error_code", None)
    retry_state["node_trace"] = []
    return cast(RecruitmentWorkflowState, retry_state)


def mark_canceled(state: RecruitmentWorkflowState) -> RecruitmentWorkflowState:
    """Mark a workflow state as canceled without running more nodes."""

    return merge_workflow_update(state, {"error_code": "CANCELED", "persisted": False})


class RecruitmentWorkflowRunnerService:
    """Run pure workflow nodes sequentially and record audit boundaries."""

    def __init__(
        self,
        *,
        audit_service: RecruitmentWorkflowAuditService,
        nodes: tuple[WorkflowNodeSpec, ...] = DEFAULT_WORKFLOW_NODES,
        now: Callable[[], datetime] = datetime.utcnow,
    ) -> None:
        self._audit_service = audit_service
        self._nodes = nodes
        self._now = now

    async def run_once(
        self,
        state: RecruitmentWorkflowState,
        *,
        user_public_id: str,
        cancel_requested: bool = False,
    ) -> WorkflowRunResult:
        """Run nodes in order, stop on first error, and write node audit records."""

        run_started_at = self._now()
        run = await self._audit_service.start_run(
            user_public_id=user_public_id,
            state=state,
            started_at=run_started_at,
        )
        if run.id is None:
            raise ValueError("agent run id is required before workflow execution")

        if cancel_requested:
            canceled_state = mark_canceled(state)
            await self._audit_service.finish_run(
                run=run,
                state=canceled_state,
                started_at=run_started_at,
                finished_at=self._now(),
            )
            return WorkflowRunResult(
                run_id=run.id,
                state=canceled_state,
                stopped_at_node=None,
            )

        current_state = cast(RecruitmentWorkflowState, dict(state))
        stopped_at_node: str | None = None
        for node in self._nodes:
            started_at = self._now()
            node_run = await self._audit_service.record_node_started(
                run_id=run.id,
                node_name=node.name,
                started_at=started_at,
            )
            try:
                current_state = merge_workflow_update(
                    current_state,
                    node.handler(current_state),
                )
            except Exception:
                current_state = merge_workflow_update(
                    current_state,
                    cast(
                        RecruitmentWorkflowUpdate,
                        {"error_code": UNKNOWN_WORKFLOW_ERROR, "persisted": False},
                    ),
                )
                await self._audit_service.record_node_finished(
                    node_run=node_run,
                    state=current_state,
                    finished_at=self._now(),
                )
                stopped_at_node = node.name
                break
            await self._audit_service.record_node_finished(
                node_run=node_run,
                state=current_state,
                finished_at=self._now(),
            )
            if current_state.get("error_code") is not None:
                stopped_at_node = node.name
                break

        await self._audit_service.finish_run(
            run=run,
            state=current_state,
            started_at=run_started_at,
            finished_at=self._now(),
        )
        return WorkflowRunResult(
            run_id=run.id,
            state=current_state,
            stopped_at_node=stopped_at_node,
        )
