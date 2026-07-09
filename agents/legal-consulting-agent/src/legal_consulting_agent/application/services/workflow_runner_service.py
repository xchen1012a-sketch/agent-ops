"""Application runner for deterministic LEGAL-140 workflow slices."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import cast

from legal_consulting_agent.application.services.workflow_audit_service import (
    LegalWorkflowAuditService,
)
from legal_consulting_agent.workflows.legal_nodes import (
    citation_check_node,
    classification_node,
    context_build_node,
    generation_node,
    input_safety_node,
    persist_node,
    retrieval_node,
    risk_check_node,
)
from legal_consulting_agent.workflows.legal_state import LegalWorkflowState, LegalWorkflowUpdate

WorkflowNode = Callable[[LegalWorkflowState], LegalWorkflowUpdate]


@dataclass(frozen=True, slots=True)
class WorkflowNodeSpec:
    """A named workflow node callable used by the application runner."""

    name: str
    handler: WorkflowNode


@dataclass(frozen=True, slots=True)
class WorkflowRunResult:
    """Result returned by a deterministic runner invocation."""

    run_id: int
    state: LegalWorkflowState
    stopped_at_node: str | None


DEFAULT_WORKFLOW_NODES: tuple[WorkflowNodeSpec, ...] = (
    WorkflowNodeSpec("input_safety", input_safety_node),
    WorkflowNodeSpec("classification", classification_node),
    WorkflowNodeSpec("context_build", context_build_node),
    WorkflowNodeSpec("retrieval", retrieval_node),
    WorkflowNodeSpec("generation", generation_node),
    WorkflowNodeSpec("citation_check", citation_check_node),
    WorkflowNodeSpec("risk_check", risk_check_node),
    WorkflowNodeSpec("persist", persist_node),
)


def merge_workflow_update(
    state: LegalWorkflowState,
    update: LegalWorkflowUpdate,
) -> LegalWorkflowState:
    """Merge a node update into state without mutating the caller's object."""

    return cast(LegalWorkflowState, {**state, **update})


def prepare_retry_state(state: LegalWorkflowState) -> LegalWorkflowState:
    """Create a clean retry state preserving caller input and adapter fixtures."""

    retry_state = dict(state)
    retry_state.pop("error_code", None)
    retry_state.pop("message_id", None)
    retry_state["node_trace"] = []
    return cast(LegalWorkflowState, retry_state)


def mark_canceled(state: LegalWorkflowState) -> LegalWorkflowState:
    """Mark a workflow state as canceled without running more nodes."""

    return merge_workflow_update(state, {"error_code": "CANCELED"})


class LegalWorkflowRunnerService:
    """Run pure workflow nodes sequentially and record audit boundaries."""

    def __init__(
        self,
        *,
        audit_service: LegalWorkflowAuditService,
        nodes: tuple[WorkflowNodeSpec, ...] = DEFAULT_WORKFLOW_NODES,
        now: Callable[[], datetime] = datetime.utcnow,
    ) -> None:
        self._audit_service = audit_service
        self._nodes = nodes
        self._now = now

    async def run_once(
        self,
        state: LegalWorkflowState,
        *,
        cancel_requested: bool = False,
    ) -> WorkflowRunResult:
        """Run nodes in order, stop on first error, and write node audit records."""

        run = await self._audit_service.start_run(
            state=state,
            started_at=self._now(),
        )
        if run.id is None:
            raise ValueError("agent run id is required before workflow execution")

        current_state = mark_canceled(state) if cancel_requested else dict(state)
        stopped_at_node: str | None = None
        if cancel_requested:
            return WorkflowRunResult(
                run_id=run.id,
                state=cast(LegalWorkflowState, current_state),
                stopped_at_node=None,
            )

        for node in self._nodes:
            started_at = self._now()
            await self._audit_service.record_node_started(
                run_id=run.id,
                node_name=node.name,
                started_at=started_at,
            )
            current_state = merge_workflow_update(
                cast(LegalWorkflowState, current_state),
                node.handler(cast(LegalWorkflowState, current_state)),
            )
            await self._audit_service.record_node_finished(
                run_id=run.id,
                node_name=node.name,
                state=current_state,
                started_at=started_at,
                finished_at=self._now(),
            )
            if current_state.get("error_code") is not None:
                stopped_at_node = node.name
                break

        return WorkflowRunResult(
            run_id=run.id,
            state=cast(LegalWorkflowState, current_state),
            stopped_at_node=stopped_at_node,
        )
