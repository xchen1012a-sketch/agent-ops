"""Application service for workflow run control state projections."""

from __future__ import annotations

from legal_consulting_agent.application.services.workflow_runner_service import (
    mark_canceled,
    prepare_retry_state,
)
from legal_consulting_agent.workflows.legal_state import LegalWorkflowState


class LegalRunControlService:
    """Project workflow run control actions without touching task queues or DB state."""

    def preview_cancel(self, state: LegalWorkflowState) -> LegalWorkflowState:
        """Return the state projection produced by a cancel request."""

        return mark_canceled(state)

    def preview_retry(self, state: LegalWorkflowState) -> LegalWorkflowState:
        """Return the state projection used to retry a failed workflow run."""

        return prepare_retry_state(state)
