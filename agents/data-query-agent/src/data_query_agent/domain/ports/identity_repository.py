"""Repository port for identity mirrors and query threads."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from data_query_agent.domain.entities.identity import QueryThread, UserMirror, UserRole


class IdentityRepository(Protocol):
    """Persistence boundary for user mirrors and query threads."""

    async def get_user_by_external_subject(self, external_subject: str) -> UserMirror | None:
        """Return a mirrored user by upstream auth subject."""

    async def create_user(
        self,
        *,
        public_id: str,
        external_subject: str,
        role: UserRole,
        display_name: str | None,
    ) -> UserMirror:
        """Create a local user mirror."""

    async def touch_user(self, user_id: int) -> UserMirror:
        """Update last-seen metadata for a mirrored user."""

    async def create_thread(
        self,
        *,
        public_id: str,
        user_id: int,
        title: str | None,
    ) -> QueryThread:
        """Create a query thread owned by one user."""

    async def get_thread_for_user(
        self, *, thread_public_id: str, user_id: int
    ) -> QueryThread | None:
        """Return one thread only when it belongs to the given user."""

    async def list_threads_for_user(
        self, *, user_id: int, limit: int, offset: int
    ) -> Sequence[QueryThread]:
        """List threads owned by one user."""
