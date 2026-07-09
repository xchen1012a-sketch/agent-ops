"""Application service for mapping recruitment workflow execution to audit records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from recruitment_assistant_agent.application.services.recruit_data_service import RecruitDataService
from recruitment_assistant_agent.domain.entities.recruit_data import AgentRun, NodeRun
from recruitment_assistant_agent.domain.value_objects.recruit_enums import RunStatus
from recruitment_assistant_agent.workflows.recruitment_state import RecruitmentWorkflowState

RETRYABLE_WORKFLOW_ERRORS = frozenset(
    {
        "PARSE_FAILED",
        "LLM_TIMEOUT",
        "DB_UNAVAILABLE",
        "RATE_LIMITED",
    }
)
TERMINAL_WORKFLOW_ERRORS = frozenset(
    {
        "CANCELED",
        "UNSUPPORTED_MATERIAL_KIND",
        "FILE_UNSAFE",
        "FAIRNESS_VIOLATION",
        "FILE_INFECTED",
    }
)
UNKNOWN_WORKFLOW_ERROR = "UNKNOWN_WORKFLOW_ERROR"


@dataclass(frozen=True, slots=True)
class WorkflowErrorMapping:
    """Stable mapping from workflow error code to audit status."""

    status: RunStatus
    retryable: bool


def map_workflow_error(error_code: str | None) -> WorkflowErrorMapping:
    """Map workflow error codes to retry-aware audit status."""

    if error_code is None:
        return WorkflowErrorMapping(status=RunStatus.SUCCESS, retryable=False)
    if error_code == "CANCELED":
        return WorkflowErrorMapping(status=RunStatus.CANCELED, retryable=False)
    if error_code in RETRYABLE_WORKFLOW_ERRORS:
        return WorkflowErrorMapping(status=RunStatus.RETRYING, retryable=True)
    return WorkflowErrorMapping(status=RunStatus.FAILED, retryable=False)


def sanitize_workflow_error_code(error_code: str | None) -> str | None:
    """Return only allowlisted workflow error codes for persistence."""

    if error_code is None:
        return None
    if error_code in RETRYABLE_WORKFLOW_ERRORS or error_code in TERMINAL_WORKFLOW_ERRORS:
        return error_code
    return UNKNOWN_WORKFLOW_ERROR


def calculate_duration_ms(started_at: datetime, finished_at: datetime) -> int:
    """Return a non-negative millisecond duration for audit records."""

    duration = int((finished_at - started_at).total_seconds() * 1000)
    return max(duration, 0)


def build_node_finish_metadata(
    *,
    state: RecruitmentWorkflowState,
    node_name: str,
    retryable: bool,
) -> dict[str, object]:
    """Build compact node metadata without storing resumes, JD text, or prompts."""

    metadata: dict[str, object] = {
        "event": "finished",
        "node_name": node_name,
        "retryable": retryable,
    }
    if state.get("overall_tier") is not None:
        metadata["has_overall_tier"] = True
    if "match_items" in state:
        metadata["match_items_count"] = len(state["match_items"])
    if "gaps" in state:
        metadata["gaps_count"] = len(state["gaps"])
    if "fairness_violation_details" in state:
        metadata["has_fairness_violation"] = bool(state["fairness_violation_details"])
    return metadata


class RecruitmentWorkflowAuditService:
    """Write retry-aware workflow audit records through existing data services."""

    def __init__(self, recruit_data_service: RecruitDataService) -> None:
        self._recruit_data_service = recruit_data_service

    async def start_run(
        self,
        *,
        user_public_id: str,
        state: RecruitmentWorkflowState,
        started_at: datetime,
    ) -> AgentRun:
        """Create the initial Agent run audit record for a user-owned task."""

        return await self._recruit_data_service.create_agent_run(
            user_public_id=user_public_id,
            task_public_id=state["thread_id"],
            workflow_version=state["workflow_version"],
            prompt_version=state["prompt_version"],
            started_at=started_at,
        )

    async def finish_run(
        self,
        *,
        run: AgentRun,
        state: RecruitmentWorkflowState,
        started_at: datetime,
        finished_at: datetime,
    ) -> AgentRun:
        """Persist the final retry-aware status for an Agent run."""

        error_code = sanitize_workflow_error_code(state.get("error_code"))
        mapping = map_workflow_error(error_code)
        return await self._recruit_data_service.finish_agent_run(
            run=run,
            status=mapping.status,
            finished_at=finished_at,
            duration_ms=calculate_duration_ms(started_at, finished_at),
            error_code=error_code,
        )

    async def record_node_started(
        self,
        *,
        run_id: int,
        node_name: str,
        started_at: datetime,
    ) -> NodeRun:
        """Record that a workflow node started execution."""

        return await self._recruit_data_service.create_node_run(
            run_id=run_id,
            node_name=node_name,
            status=RunStatus.RUNNING,
            started_at=started_at,
            metadata={"event": "started", "node_name": node_name},
        )

    async def record_node_finished(
        self,
        *,
        node_run: NodeRun,
        state: RecruitmentWorkflowState,
        finished_at: datetime,
    ) -> NodeRun:
        """Record the final retry-aware status for a workflow node."""

        error_code = sanitize_workflow_error_code(state.get("error_code"))
        mapping = map_workflow_error(error_code)
        return await self._recruit_data_service.finish_node_run(
            node_run=node_run,
            status=mapping.status,
            finished_at=finished_at,
            duration_ms=calculate_duration_ms(node_run.started_at, finished_at),
            error_code=error_code,
            metadata=build_node_finish_metadata(
                state=state,
                node_name=node_run.node_name,
                retryable=mapping.retryable,
            ),
        )
