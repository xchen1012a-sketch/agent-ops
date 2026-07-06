"""Repository port for LEGAL-130 identity and data persistence."""

from __future__ import annotations

from typing import Protocol

from legal_consulting_agent.domain.entities.legal_data import (
    AgentRun,
    ConsultationRecord,
    Feedback,
    HighRiskReview,
    KnowledgeMaterial,
    LegalCategory,
    LegalMessage,
    LegalSession,
    NodeRun,
    PromptVersion,
    UserMirror,
)
from legal_consulting_agent.domain.value_objects.legal_enums import MessageRole


class LegalDataRepository(Protocol):
    """Persistence contract used by application services.

    Implementations must not commit transactions; callers own transaction
    boundaries through the active SQLAlchemy session.
    """

    async def upsert_user_mirror(self, user: UserMirror) -> UserMirror:
        """Create or update a user mirror by public ID."""

    async def get_user_by_public_id(self, public_id: str) -> UserMirror | None:
        """Return a user mirror by public ID."""

    async def get_category_by_code(self, code: str) -> LegalCategory | None:
        """Return a legal category by stable category code."""

    async def create_session(self, session: LegalSession) -> LegalSession:
        """Persist a legal consultation session."""

    async def get_session_for_user(
        self,
        *,
        session_public_id: str,
        user_id: int,
    ) -> LegalSession | None:
        """Return a user-owned session or None when absent/unauthorized."""

    async def list_sessions_for_user(
        self,
        *,
        user_id: int,
        limit: int,
        offset: int,
    ) -> list[LegalSession]:
        """Return the user's sessions ordered newest first."""

    async def update_session_title(self, *, session_id: int, title: str) -> LegalSession:
        """Update a session title and return the refreshed session."""

    async def append_message(self, message: LegalMessage) -> LegalMessage:
        """Persist one message inside an existing session."""

    async def get_message_for_session(
        self,
        *,
        message_public_id: str,
        session_id: int,
        role: MessageRole,
    ) -> LegalMessage | None:
        """Return a session message with the required role, or None."""

    async def list_messages_for_user_session(
        self,
        *,
        session_public_id: str,
        user_id: int,
        limit: int,
        offset: int,
    ) -> list[LegalMessage]:
        """Return messages from a user-owned session ordered by id."""

    async def list_recent_messages_for_user_session(
        self,
        *,
        session_public_id: str,
        user_id: int,
        limit: int,
    ) -> list[LegalMessage]:
        """Return the newest ``limit`` messages in chronological order."""

    async def create_consultation_record(
        self,
        record: ConsultationRecord,
    ) -> ConsultationRecord:
        """Persist a completed consultation snapshot."""

    async def get_consultation_record_for_user(
        self,
        *,
        record_public_id: str,
        user_id: int,
    ) -> ConsultationRecord | None:
        """Return a user-owned consultation record, or None."""

    async def list_consultation_records_for_user(
        self,
        *,
        user_id: int,
        limit: int,
        offset: int,
        query: str | None,
    ) -> list[ConsultationRecord]:
        """Return user-owned consultation records ordered by newest first."""

    async def create_feedback(self, feedback: Feedback) -> Feedback:
        """Persist user feedback for an assistant message."""

    async def create_high_risk_review(self, review: HighRiskReview) -> HighRiskReview:
        """Persist a pending high-risk review queue record."""

    async def create_prompt_version(self, prompt: PromptVersion) -> PromptVersion:
        """Persist versioned Prompt metadata."""

    async def create_knowledge_material(
        self,
        material: KnowledgeMaterial,
    ) -> KnowledgeMaterial:
        """Persist legal knowledge material metadata."""

    async def create_agent_run(self, run: AgentRun) -> AgentRun:
        """Persist an Agent run audit record."""

    async def create_node_run(self, node_run: NodeRun) -> NodeRun:
        """Persist an Agent node audit record."""
