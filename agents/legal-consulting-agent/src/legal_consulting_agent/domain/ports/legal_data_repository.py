"""Repository port for LEGAL-130 identity and data persistence."""

from __future__ import annotations

from typing import Protocol

from legal_consulting_agent.domain.entities.legal_data import (
    AgentRun,
    LegalCategory,
    LegalMessage,
    LegalSession,
    NodeRun,
    UserMirror,
)


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

    async def append_message(self, message: LegalMessage) -> LegalMessage:
        """Persist one message inside an existing session."""

    async def create_agent_run(self, run: AgentRun) -> AgentRun:
        """Persist an Agent run audit record."""

    async def create_node_run(self, node_run: NodeRun) -> NodeRun:
        """Persist an Agent node audit record."""
