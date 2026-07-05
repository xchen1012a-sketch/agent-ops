"""Application service for mapping workflow execution to audit records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from legal_consulting_agent.application.services.legal_data_service import LegalDataService
from legal_consulting_agent.domain.entities.legal_data import AgentRun, NodeRun
from legal_consulting_agent.domain.value_objects.legal_enums import RunStatus
from legal_consulting_agent.workflows.legal_state import LegalWorkflowState

RETRYABLE_WORKFLOW_ERRORS = frozenset(
    {
        "CLASSIFY_FAILED",
        "RETRIEVAL_FAILED",
        "LLM_TIMEOUT",
        "DB_UNAVAILABLE",
        "RATE_LIMITED",
    }
)


@dataclass(frozen=True, slots=True)
class WorkflowErrorMapping:
    """Stable mapping from workflow error code to audit status."""

    status: RunStatus
    retryable: bool


def map_workflow_error(error_code: str | None) -> WorkflowErrorMapping:
    """Map workflow error codes to retry-aware audit status."""

    if error_code is None:
        return WorkflowErrorMapping(status=RunStatus.SUCCESS, retryable=False)
    if error_code in RETRYABLE_WORKFLOW_ERRORS:
        return WorkflowErrorMapping(status=RunStatus.RETRYING, retryable=True)
    return WorkflowErrorMapping(status=RunStatus.FAILED, retryable=False)


def calculate_duration_ms(started_at: datetime, finished_at: datetime) -> int:
    """Return a non-negative millisecond duration for audit records."""

    duration = int((finished_at - started_at).total_seconds() * 1000)
    return max(duration, 0)


def build_node_finish_metadata(
    *,
    state: LegalWorkflowState,
    node_name: str,
    retryable: bool,
) -> dict[str, object]:
    """Build compact node metadata without storing full prompts or raw context."""

    metadata: dict[str, object] = {
        "event": "finished",
        "node_name": node_name,
        "retryable": retryable,
    }
    if "category" in state and state["category"] is not None:
        metadata["category"] = state["category"]
    if "chunks" in state:
        metadata["chunks_count"] = len(state["chunks"])
    if "high_risk" in state:
        metadata["high_risk"] = state["high_risk"]
    return metadata


class LegalWorkflowAuditService:
    """Write retry-aware workflow audit records through existing data services."""

    def __init__(self, legal_data_service: LegalDataService) -> None:
        self._legal_data_service = legal_data_service

    async def start_run(
        self,
        *,
        state: LegalWorkflowState,
        started_at: datetime,
    ) -> AgentRun:
        """Create the initial Agent run audit record."""

        return await self._legal_data_service.create_agent_run(
            thread_id=state["thread_id"],
            user_id=state["user_id"],
            workflow_version=state["workflow_version"],
            prompt_version=state["prompt_version"],
            started_at=started_at,
        )

    async def record_node_started(
        self,
        *,
        run_id: int,
        node_name: str,
        started_at: datetime,
    ) -> NodeRun:
        """Record that a workflow node started execution."""

        return await self._legal_data_service.create_node_run(
            run_id=run_id,
            node_name=node_name,
            status=RunStatus.RUNNING,
            started_at=started_at,
            metadata={"event": "started", "node_name": node_name},
        )

    async def record_node_finished(
        self,
        *,
        run_id: int,
        node_name: str,
        state: LegalWorkflowState,
        started_at: datetime,
        finished_at: datetime,
    ) -> NodeRun:
        """Record the final retry-aware status for a workflow node."""

        error_code = state.get("error_code")
        mapping = map_workflow_error(error_code)
        return await self._legal_data_service.create_node_run(
            run_id=run_id,
            node_name=node_name,
            status=mapping.status,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=calculate_duration_ms(started_at, finished_at),
            error_code=error_code,
            metadata=build_node_finish_metadata(
                state=state,
                node_name=node_name,
                retryable=mapping.retryable,
            ),
        )
