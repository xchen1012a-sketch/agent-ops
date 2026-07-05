"""Application service for user mirrors and query threads."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import uuid4

from data_query_agent.domain.entities.identity import (
    MessageRole,
    QueryThread,
    ThreadMessage,
    UserMirror,
    UserRole,
)
from data_query_agent.domain.ports.identity_repository import IdentityRepository


class IdentityThreadService:
    """Use cases for user mirror bootstrap and thread ownership checks."""

    def __init__(self, repository: IdentityRepository) -> None:
        self._repository = repository

    async def get_or_create_user(
        self,
        *,
        external_subject: str,
        role: UserRole = UserRole.USER,
        display_name: str | None = None,
    ) -> UserMirror:
        """Return an existing local mirror or create one from auth subject."""
        existing = await self._repository.get_user_by_external_subject(external_subject)
        if existing is not None:
            if existing.id is None:
                raise ValueError("persisted user mirror must have an id")
            return await self._repository.touch_user(existing.id)

        return await self._repository.create_user(
            public_id=str(uuid4()),
            external_subject=external_subject,
            role=role,
            display_name=display_name,
        )

    async def create_thread_for_subject(
        self,
        *,
        external_subject: str,
        title: str | None,
        role: UserRole = UserRole.USER,
        display_name: str | None = None,
    ) -> QueryThread:
        """Create a query thread for the authenticated upstream subject."""
        user = await self.get_or_create_user(
            external_subject=external_subject,
            role=role,
            display_name=display_name,
        )
        if user.id is None:
            raise ValueError("persisted user mirror must have an id")
        return await self._repository.create_thread(
            public_id=str(uuid4()),
            user_id=user.id,
            title=title,
        )

    async def get_owned_thread(
        self,
        *,
        thread_public_id: str,
        external_subject: str,
    ) -> QueryThread | None:
        """Return a thread only when it belongs to the authenticated subject."""
        user = await self._repository.get_user_by_external_subject(external_subject)
        if user is None:
            return None
        if user.id is None:
            raise ValueError("persisted user mirror must have an id")
        return await self._repository.get_thread_for_user(
            thread_public_id=thread_public_id,
            user_id=user.id,
        )

    async def list_owned_threads(
        self,
        *,
        external_subject: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[QueryThread]:
        """List threads for one authenticated upstream subject."""
        user = await self._repository.get_user_by_external_subject(external_subject)
        if user is None:
            return ()
        if user.id is None:
            raise ValueError("persisted user mirror must have an id")
        return await self._repository.list_threads_for_user(
            user_id=user.id,
            limit=limit,
            offset=offset,
        )

    async def create_message_for_subject(
        self,
        *,
        external_subject: str,
        thread_public_id: str,
        role: MessageRole,
        content: str,
    ) -> ThreadMessage:
        """Create a message only when the thread belongs to the subject."""
        thread = await self.get_owned_thread(
            thread_public_id=thread_public_id,
            external_subject=external_subject,
        )
        if thread is None:
            raise PermissionError("thread not found or not owned by subject")
        if thread.id is None:
            raise ValueError("persisted thread must have an id")
        return await self._repository.create_message(
            public_id=str(uuid4()),
            thread_id=thread.id,
            user_id=thread.user_id,
            role=role,
            content=content,
        )

    async def list_messages_for_subject(
        self,
        *,
        external_subject: str,
        thread_public_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[ThreadMessage]:
        """List messages only when the thread belongs to the subject."""
        thread = await self.get_owned_thread(
            thread_public_id=thread_public_id,
            external_subject=external_subject,
        )
        if thread is None:
            return ()
        if thread.id is None:
            raise ValueError("persisted thread must have an id")
        return await self._repository.list_messages_for_thread(
            thread_id=thread.id,
            user_id=thread.user_id,
            limit=limit,
            offset=offset,
        )
