"""Application use cases for LEGAL-130 identity and data records."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from legal_consulting_agent.core.errors import AppError
from legal_consulting_agent.domain.entities.legal_data import (
    AgentRun,
    ConsultationRecord,
    Feedback,
    LegalMessage,
    LegalSession,
    NodeRun,
    UserMirror,
)
from legal_consulting_agent.domain.ports.legal_data_repository import LegalDataRepository
from legal_consulting_agent.domain.value_objects.legal_enums import (
    MessageRole,
    RunStatus,
    SessionStatus,
    UserRole,
    UserStatus,
)


class LegalDataNotFoundError(AppError):
    """Raised when a required legal data record is absent."""

    code = "LEGAL_DATA_NOT_FOUND"
    http_status = 404


class LegalDataService:
    """Coordinate LEGAL-130 use cases without owning transaction commits."""

    def __init__(self, repository: LegalDataRepository) -> None:
        self._repository = repository

    async def sync_user_mirror(
        self,
        *,
        public_id: str,
        email: str,
        display_name: str | None,
        role: UserRole,
        status: UserStatus = UserStatus.ACTIVE,
    ) -> UserMirror:
        """Create or update the local user mirror from trusted JWT claims."""
        return await self._repository.upsert_user_mirror(
            UserMirror(
                public_id=public_id,
                email=email,
                display_name=display_name,
                role=role,
                status=status,
            )
        )

    async def create_session(
        self,
        *,
        user_public_id: str,
        category_code: str,
        title: str | None,
    ) -> LegalSession:
        """Create a legal consultation session for an existing category."""
        user = await self._repository.get_user_by_public_id(user_public_id)
        if user is None or user.id is None:
            raise LegalDataNotFoundError("User mirror not found")

        category = await self._repository.get_category_by_code(category_code)
        if category is None or category.id is None:
            raise LegalDataNotFoundError("Legal category not found")

        return await self._repository.create_session(
            LegalSession(
                public_id=str(uuid4()),
                user_id=user.id,
                category_id=category.id,
                title=title,
                status=SessionStatus.ACTIVE,
                last_message_at=None,
            )
        )

    async def append_message(
        self,
        *,
        user_public_id: str,
        session_public_id: str,
        role: MessageRole,
        content: str,
        citations: list[dict[str, Any]] | None = None,
        high_risk: bool = False,
        prompt_version: str | None = None,
    ) -> LegalMessage:
        """Append a message only when the session belongs to the user."""
        user = await self._repository.get_user_by_public_id(user_public_id)
        if user is None or user.id is None:
            raise LegalDataNotFoundError("User mirror not found")

        session = await self._repository.get_session_for_user(
            session_public_id=session_public_id,
            user_id=user.id,
        )
        if session is None or session.id is None:
            raise LegalDataNotFoundError("Legal session not found")

        return await self._repository.append_message(
            LegalMessage(
                public_id=str(uuid4()),
                session_id=session.id,
                role=role,
                content=content,
                citations=citations,
                high_risk=high_risk,
                prompt_version=prompt_version,
            )
        )

    async def create_agent_run(
        self,
        *,
        thread_id: str,
        user_id: int,
        workflow_version: str,
        prompt_version: str,
        started_at: datetime,
    ) -> AgentRun:
        """Create a pending audit record for a user-owned legal session."""
        session = await self._repository.get_session_for_user(
            session_public_id=thread_id,
            user_id=user_id,
        )
        if session is None:
            raise LegalDataNotFoundError("Legal session not found")

        return await self._repository.create_agent_run(
            AgentRun(
                public_id=str(uuid4()),
                thread_id=thread_id,
                user_id=user_id,
                workflow_version=workflow_version,
                prompt_version=prompt_version,
                status=RunStatus.PENDING,
                retry_count=0,
                error_code=None,
                error_summary=None,
                started_at=started_at,
                finished_at=None,
                duration_ms=None,
            )
        )

    async def create_consultation_record(
        self,
        *,
        user_public_id: str,
        session_public_id: str,
        question_message_public_id: str,
        answer_message_public_id: str,
        summary: str,
        disclaimer: str,
    ) -> ConsultationRecord:
        """Create a snapshot from a user-owned question and answer pair."""
        user = await self._repository.get_user_by_public_id(user_public_id)
        if user is None or user.id is None:
            raise LegalDataNotFoundError("User mirror not found")

        session = await self._repository.get_session_for_user(
            session_public_id=session_public_id,
            user_id=user.id,
        )
        if session is None or session.id is None:
            raise LegalDataNotFoundError("Legal session not found")

        question = await self._repository.get_message_for_session(
            message_public_id=question_message_public_id,
            session_id=session.id,
            role=MessageRole.USER,
        )
        if question is None or question.id is None:
            raise LegalDataNotFoundError("Question message not found")

        answer = await self._repository.get_message_for_session(
            message_public_id=answer_message_public_id,
            session_id=session.id,
            role=MessageRole.ASSISTANT,
        )
        if answer is None or answer.id is None:
            raise LegalDataNotFoundError("Answer message not found")

        return await self._repository.create_consultation_record(
            ConsultationRecord(
                public_id=str(uuid4()),
                user_id=user.id,
                session_id=session.id,
                category_id=session.category_id,
                question_message_id=question.id,
                answer_message_id=answer.id,
                summary=summary,
                citations=answer.citations,
                high_risk=answer.high_risk,
                disclaimer=disclaimer,
            )
        )

    async def create_feedback(
        self,
        *,
        user_public_id: str,
        session_public_id: str,
        message_public_id: str,
        rating: int,
        comment: str | None,
    ) -> Feedback:
        """Save feedback for an assistant message in a user-owned session."""
        if rating < 1 or rating > 5:
            raise ValueError("rating must be between 1 and 5")

        user = await self._repository.get_user_by_public_id(user_public_id)
        if user is None or user.id is None:
            raise LegalDataNotFoundError("User mirror not found")

        session = await self._repository.get_session_for_user(
            session_public_id=session_public_id,
            user_id=user.id,
        )
        if session is None or session.id is None:
            raise LegalDataNotFoundError("Legal session not found")

        message = await self._repository.get_message_for_session(
            message_public_id=message_public_id,
            session_id=session.id,
            role=MessageRole.ASSISTANT,
        )
        if message is None or message.id is None:
            raise LegalDataNotFoundError("Assistant message not found")

        return await self._repository.create_feedback(
            Feedback(
                message_id=message.id,
                user_id=user.id,
                rating=rating,
                comment=comment,
            )
        )

    async def create_node_run(
        self,
        *,
        run_id: int,
        node_name: str,
        status: RunStatus,
        started_at: datetime,
        metadata: dict[str, Any] | None = None,
    ) -> NodeRun:
        """Create a node run audit record for an existing Agent run."""
        return await self._repository.create_node_run(
            NodeRun(
                run_id=run_id,
                node_name=node_name,
                status=status,
                duration_ms=None,
                error_code=None,
                metadata=metadata,
                started_at=started_at,
                finished_at=None,
            )
        )
