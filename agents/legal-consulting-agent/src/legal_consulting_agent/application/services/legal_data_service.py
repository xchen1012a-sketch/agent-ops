"""Application use cases for LEGAL-130 identity and data records."""

from __future__ import annotations

from datetime import datetime
from pathlib import PurePosixPath
from string import hexdigits
from typing import Any
from uuid import uuid4

from legal_consulting_agent.core.errors import AppError, ForbiddenError
from legal_consulting_agent.domain.entities.legal_data import (
    AgentRun,
    ConsultationRecord,
    Feedback,
    HighRiskReview,
    KnowledgeMaterial,
    LegalMessage,
    LegalSession,
    NodeRun,
    PromptVersion,
    UserMirror,
)
from legal_consulting_agent.domain.ports.legal_data_repository import LegalDataRepository
from legal_consulting_agent.domain.value_objects.legal_enums import (
    MaterialStatus,
    MessageRole,
    PromptStatus,
    ReviewStatus,
    RunStatus,
    SessionStatus,
    UserRole,
    UserStatus,
)


class LegalDataNotFoundError(AppError):
    """Raised when a required legal data record is absent."""

    code = "LEGAL_DATA_NOT_FOUND"
    http_status = 404


def _validate_relative_posix_key(value: str, *, field_name: str) -> None:
    key_path = PurePosixPath(value)
    if (
        not value
        or key_path.is_absolute()
        or ".." in key_path.parts
        or "\\" in value
        or ":" in value
    ):
        raise ValueError(f"{field_name} must be a safe relative POSIX key")


class LegalDataService:
    """Coordinate LEGAL-130 use cases without owning transaction commits."""

    def __init__(self, repository: LegalDataRepository) -> None:
        self._repository = repository

    async def get_user_mirror(self, public_id: str) -> UserMirror:
        """Return a local user mirror by public ID."""

        user = await self._repository.get_user_by_public_id(public_id)
        if user is None or user.id is None:
            raise LegalDataNotFoundError("User mirror not found")
        return user

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

    async def list_session_messages(
        self,
        *,
        user_public_id: str,
        session_public_id: str,
        limit: int,
        offset: int,
    ) -> list[LegalMessage]:
        """List messages for a user-owned session with bounded pagination."""

        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        if offset < 0:
            raise ValueError("offset must be greater than or equal to 0")
        user = await self.get_user_mirror(user_public_id)
        return await self._repository.list_messages_for_user_session(
            session_public_id=session_public_id,
            user_id=user.id or 0,
            limit=limit,
            offset=offset,
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

    async def create_high_risk_review(
        self,
        *,
        user_public_id: str,
        session_public_id: str,
        message_public_id: str,
        reason: str,
    ) -> HighRiskReview:
        """Queue a high-risk assistant message for later human review."""
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
        if not message.high_risk:
            raise ValueError("message is not marked high risk")

        return await self._repository.create_high_risk_review(
            HighRiskReview(
                message_id=message.id,
                user_id=user.id,
                reason=reason,
                status=ReviewStatus.PENDING,
                reviewed_by=None,
                resolution=None,
                reviewed_at=None,
            )
        )

    async def create_prompt_version(
        self,
        *,
        creator_public_id: str,
        prompt_name: str,
        version: str,
        template_key: str,
        variables: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> PromptVersion:
        """Create draft Prompt metadata for an administrator."""
        creator = await self._repository.get_user_by_public_id(creator_public_id)
        if creator is None or creator.id is None:
            raise LegalDataNotFoundError("User mirror not found")
        if creator.role is not UserRole.ADMIN:
            raise ForbiddenError("Administrator role required")

        _validate_relative_posix_key(template_key, field_name="template_key")

        return await self._repository.create_prompt_version(
            PromptVersion(
                prompt_name=prompt_name,
                version=version,
                template_key=template_key,
                variables=variables,
                output_schema=output_schema,
                status=PromptStatus.DRAFT,
                created_by=creator.id,
            )
        )

    async def create_knowledge_material(
        self,
        *,
        uploader_public_id: str,
        category_code: str | None,
        title: str,
        source_name: str,
        source_section: str | None,
        file_hash: str,
        file_key: str,
    ) -> KnowledgeMaterial:
        """Create indexing metadata without reading or writing source content."""
        uploader = await self._repository.get_user_by_public_id(uploader_public_id)
        if uploader is None or uploader.id is None:
            raise LegalDataNotFoundError("User mirror not found")
        if uploader.role is not UserRole.ADMIN:
            raise ForbiddenError("Administrator role required")

        category_id: int | None = None
        if category_code is not None:
            category = await self._repository.get_category_by_code(category_code)
            if category is None or category.id is None:
                raise LegalDataNotFoundError("Legal category not found")
            category_id = category.id

        if len(file_hash) != 64 or any(character not in hexdigits for character in file_hash):
            raise ValueError("file_hash must be a SHA-256 hexadecimal digest")
        _validate_relative_posix_key(file_key, field_name="file_key")

        return await self._repository.create_knowledge_material(
            KnowledgeMaterial(
                public_id=str(uuid4()),
                category_id=category_id,
                title=title,
                source_name=source_name,
                source_section=source_section,
                file_hash=file_hash.lower(),
                file_key=file_key,
                chunk_count=0,
                status=MaterialStatus.INDEXING,
                version=1,
                uploaded_by=uploader.id,
            )
        )

    async def create_node_run(
        self,
        *,
        run_id: int,
        node_name: str,
        status: RunStatus,
        started_at: datetime,
        finished_at: datetime | None = None,
        duration_ms: int | None = None,
        error_code: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NodeRun:
        """Create a node run audit record for an existing Agent run."""
        return await self._repository.create_node_run(
            NodeRun(
                run_id=run_id,
                node_name=node_name,
                status=status,
                duration_ms=duration_ms,
                error_code=error_code,
                metadata=metadata,
                started_at=started_at,
                finished_at=finished_at,
            )
        )
