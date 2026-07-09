"""DTOs for legal workflow run control preview APIs."""

from __future__ import annotations

from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field

from legal_consulting_agent.workflows.legal_state import LegalWorkflowState


class LegalWorkflowRunStatePayload(BaseModel):
    """Serializable subset of workflow state accepted by control preview endpoints."""

    model_config = ConfigDict(str_strip_whitespace=True)

    thread_id: str = Field(min_length=1, max_length=128)
    user_id: int = Field(gt=0)
    question: str = Field(min_length=1, max_length=4000)
    prompt_version: str = Field(min_length=1, max_length=128)
    workflow_version: str = Field(min_length=1, max_length=128)
    error_code: str | None = Field(default=None, max_length=64)
    message_id: int | None = Field(default=None, gt=0)
    node_trace: list[str] = Field(default_factory=list, max_length=32)
    category: str | None = Field(default=None, max_length=64)
    high_risk: bool | None = None
    risk_reason: str | None = Field(default=None, max_length=1000)

    def to_workflow_state(self) -> LegalWorkflowState:
        """Convert the public preview payload into an internal workflow state."""

        state: LegalWorkflowState = {
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "question": self.question,
            "prompt_version": self.prompt_version,
            "workflow_version": self.workflow_version,
            "node_trace": list(self.node_trace),
        }
        if self.error_code is not None:
            state["error_code"] = self.error_code
        if self.message_id is not None:
            state["message_id"] = self.message_id
        if self.category is not None:
            state["category"] = self.category
        if self.high_risk is not None:
            state["high_risk"] = self.high_risk
        if self.risk_reason is not None:
            state["risk_reason"] = self.risk_reason
        return state

    @classmethod
    def from_workflow_state(
        cls,
        state: LegalWorkflowState,
    ) -> LegalWorkflowRunStatePayload:
        """Build a public preview payload from internal workflow state."""

        return cls(
            thread_id=state["thread_id"],
            user_id=state["user_id"],
            question=state["question"],
            prompt_version=state["prompt_version"],
            workflow_version=state["workflow_version"],
            error_code=state.get("error_code"),
            message_id=state.get("message_id"),
            node_trace=list(state.get("node_trace") or []),
            category=state.get("category"),
            high_risk=state.get("high_risk"),
            risk_reason=state.get("risk_reason"),
        )

    def to_public_dict(self) -> dict[str, object]:
        """Return a JSON-ready state projection, omitting cleared optional fields."""

        return cast(dict[str, object], self.model_dump(exclude_none=True, mode="json"))


class LegalWorkflowRunControlRequest(BaseModel):
    """Request body for workflow run control preview endpoints."""

    state: LegalWorkflowRunStatePayload


class LegalWorkflowRunCancelPreviewResponse(BaseModel):
    """Response data for a cancel preview."""

    operation: Literal["cancel_preview"] = "cancel_preview"
    state: dict[str, object]


class LegalWorkflowRunRetryPreviewResponse(BaseModel):
    """Response data for a retry preview."""

    operation: Literal["retry_preview"] = "retry_preview"
    state: dict[str, object]


class LegalWorkflowRunCancelPreviewEnvelope(BaseModel):
    """Success envelope for cancel preview."""

    data: LegalWorkflowRunCancelPreviewResponse
    error: Literal[None] = None


class LegalWorkflowRunRetryPreviewEnvelope(BaseModel):
    """Success envelope for retry preview."""

    data: LegalWorkflowRunRetryPreviewResponse
    error: Literal[None] = None
