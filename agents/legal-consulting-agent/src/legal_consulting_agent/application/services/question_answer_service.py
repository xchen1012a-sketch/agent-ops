"""Application service for deterministic legal question answering API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast

from legal_consulting_agent.application.services.legal_data_service import LegalDataService
from legal_consulting_agent.core.errors import AppError, InputBlockedError
from legal_consulting_agent.domain.entities.legal_data import LegalMessage
from legal_consulting_agent.domain.value_objects.legal_enums import MessageRole
from legal_consulting_agent.workflows import build_legal_workflow_graph
from legal_consulting_agent.workflows.legal_nodes import CONTEXT_WINDOW_MESSAGES
from legal_consulting_agent.workflows.legal_state import Citation, LegalWorkflowState

DEFAULT_LEGAL_WORKFLOW_VERSION = "legal_workflow:deterministic-v1"
DEFAULT_LEGAL_PROMPT_VERSION = "deterministic:v1"


class LegalWorkflowGraph(Protocol):
    """Minimal graph contract used by the question answer service."""

    def invoke(self, state: LegalWorkflowState) -> object:
        """Execute a workflow and return the merged state."""


@dataclass(frozen=True, slots=True)
class LegalQuestionAnswerResult:
    """Persisted question/answer pair and workflow projection."""

    question_message: LegalMessage
    answer_message: LegalMessage
    answer: str
    citations: list[Citation]
    high_risk: bool
    risk_reason: str | None
    category: str | None
    node_trace: list[str]


class LegalWorkflowExecutionError(AppError):
    """Raised when the deterministic workflow returns an unsupported error."""

    code = "LEGAL_WORKFLOW_FAILED"
    http_status = 422


class LegalQuestionAnswerService:
    """Coordinate message persistence and local deterministic workflow execution."""

    def __init__(
        self,
        *,
        legal_data_service: LegalDataService,
        workflow_graph: LegalWorkflowGraph | None = None,
    ) -> None:
        self._legal_data_service = legal_data_service
        self._workflow_graph = workflow_graph or cast(
            LegalWorkflowGraph, build_legal_workflow_graph()
        )

    async def answer_question(
        self,
        *,
        user_public_id: str,
        session_public_id: str,
        question: str,
    ) -> LegalQuestionAnswerResult:
        """Persist a user question, run the local workflow, and persist the answer."""

        user = await self._legal_data_service.get_user_mirror(user_public_id)
        # Claude-style memory: load prior turns (before appending the new question)
        # so the workflow generates with real multi-turn context.
        history = await self._legal_data_service.list_recent_session_messages(
            user_public_id=user_public_id,
            session_public_id=session_public_id,
            limit=CONTEXT_WINDOW_MESSAGES,
        )
        context_messages = [
            {"role": message.role.value, "content": message.content} for message in history
        ]
        question_message = await self._legal_data_service.append_message(
            user_public_id=user_public_id,
            session_public_id=session_public_id,
            role=MessageRole.USER,
            content=question,
        )
        workflow_state = self._invoke_workflow(
            user_id=user.id or 0,
            session_public_id=session_public_id,
            question=question,
            context_messages=context_messages,
        )
        answer = workflow_state.get("validated_answer") or workflow_state.get("answer_draft")
        if not answer:
            raise LegalWorkflowExecutionError(
                "Legal workflow did not produce an answer",
                details={"error_code": workflow_state.get("error_code")},
            )
        citations = workflow_state.get("citations", [])
        citation_payload = [dict(citation) for citation in citations]
        high_risk = workflow_state.get("high_risk", False)
        answer_message = await self._legal_data_service.append_message(
            user_public_id=user_public_id,
            session_public_id=session_public_id,
            role=MessageRole.ASSISTANT,
            content=answer,
            citations=citation_payload,
            high_risk=high_risk,
            prompt_version=DEFAULT_LEGAL_PROMPT_VERSION,
        )
        return LegalQuestionAnswerResult(
            question_message=question_message,
            answer_message=answer_message,
            answer=answer,
            citations=list(citations),
            high_risk=high_risk,
            risk_reason=workflow_state.get("risk_reason"),
            category=workflow_state.get("category"),
            node_trace=workflow_state.get("node_trace", []),
        )

    def _invoke_workflow(
        self,
        *,
        user_id: int,
        session_public_id: str,
        question: str,
        context_messages: list[dict[str, str]] | None = None,
    ) -> LegalWorkflowState:
        state: LegalWorkflowState = {
            "thread_id": session_public_id,
            "user_id": user_id,
            "question": question,
            "prompt_version": DEFAULT_LEGAL_PROMPT_VERSION,
            "workflow_version": DEFAULT_LEGAL_WORKFLOW_VERSION,
            "context_messages": context_messages or [],
            "node_trace": [],
        }
        result = cast(LegalWorkflowState, self._workflow_graph.invoke(state))
        error_code = result.get("error_code")
        if error_code == "INPUT_BLOCKED":
            raise InputBlockedError("Question was blocked by input safety checks")
        if error_code:
            raise LegalWorkflowExecutionError(
                "Legal workflow failed",
                details={"error_code": error_code},
            )
        return result
