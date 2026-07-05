"""Legal workflow run control preview endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from legal_consulting_agent.api.dependencies import (
    CurrentUserPublicIdDep,
    LegalRunControlServiceDep,
)
from legal_consulting_agent.api.v1.schemas.legal_runs import (
    LegalWorkflowRunCancelPreviewEnvelope,
    LegalWorkflowRunCancelPreviewResponse,
    LegalWorkflowRunControlRequest,
    LegalWorkflowRunRetryPreviewEnvelope,
    LegalWorkflowRunRetryPreviewResponse,
    LegalWorkflowRunStatePayload,
)

router = APIRouter()


@router.post(
    "/workflow-runs/cancel-preview",
    response_model=LegalWorkflowRunCancelPreviewEnvelope,
)
async def preview_cancel_workflow_run(
    payload: LegalWorkflowRunControlRequest,
    _user_public_id: CurrentUserPublicIdDep,
    run_control_service: LegalRunControlServiceDep,
) -> LegalWorkflowRunCancelPreviewEnvelope:
    """Preview the workflow state produced by canceling a run."""

    state = run_control_service.preview_cancel(payload.state.to_workflow_state())
    return LegalWorkflowRunCancelPreviewEnvelope(
        data=LegalWorkflowRunCancelPreviewResponse(
            state=LegalWorkflowRunStatePayload.from_workflow_state(state).to_public_dict(),
        )
    )


@router.post(
    "/workflow-runs/retry-preview",
    response_model=LegalWorkflowRunRetryPreviewEnvelope,
)
async def preview_retry_workflow_run(
    payload: LegalWorkflowRunControlRequest,
    _user_public_id: CurrentUserPublicIdDep,
    run_control_service: LegalRunControlServiceDep,
) -> LegalWorkflowRunRetryPreviewEnvelope:
    """Preview the clean workflow state used by a retry request."""

    state = run_control_service.preview_retry(payload.state.to_workflow_state())
    return LegalWorkflowRunRetryPreviewEnvelope(
        data=LegalWorkflowRunRetryPreviewResponse(
            state=LegalWorkflowRunStatePayload.from_workflow_state(state).to_public_dict(),
        )
    )
