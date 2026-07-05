"""Unit tests for identity and thread application service."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import pytest

from data_query_agent.application.services.identity_service import IdentityThreadService
from data_query_agent.domain.entities.identity import (
    MessageRole,
    QueryThread,
    ThreadMessage,
    ThreadStatus,
    UserMirror,
    UserRole,
)


class FakeIdentityRepository:
    """In-memory identity repository for service tests."""

    def __init__(self) -> None:
        self.users_by_subject: dict[str, UserMirror] = {}
        self.threads_by_public_id: dict[str, QueryThread] = {}
        self.messages_by_public_id: dict[str, ThreadMessage] = {}
        self.next_user_id = 1
        self.next_thread_id = 1
        self.next_message_id = 1
        self.touch_count = 0

    async def get_user_by_external_subject(self, external_subject: str) -> UserMirror | None:
        return self.users_by_subject.get(external_subject)

    async def create_user(
        self,
        *,
        public_id: str,
        external_subject: str,
        role: UserRole,
        display_name: str | None,
    ) -> UserMirror:
        now = datetime.now(UTC).replace(tzinfo=None)
        user = UserMirror(
            id=self.next_user_id,
            public_id=public_id,
            external_subject=external_subject,
            role=role,
            display_name=display_name,
            created_at=now,
            updated_at=now,
            last_seen_at=now,
        )
        self.next_user_id += 1
        self.users_by_subject[external_subject] = user
        return user

    async def touch_user(self, user_id: int) -> UserMirror:
        self.touch_count += 1
        for subject, user in self.users_by_subject.items():
            if user.id == user_id:
                touched = UserMirror(
                    id=user.id,
                    public_id=user.public_id,
                    external_subject=user.external_subject,
                    role=user.role,
                    display_name=user.display_name,
                    created_at=user.created_at,
                    updated_at=datetime.now(UTC).replace(tzinfo=None),
                    last_seen_at=datetime.now(UTC).replace(tzinfo=None),
                )
                self.users_by_subject[subject] = touched
                return touched
        raise LookupError(user_id)

    async def create_thread(
        self,
        *,
        public_id: str,
        user_id: int,
        title: str | None,
    ) -> QueryThread:
        now = datetime.now(UTC).replace(tzinfo=None)
        thread = QueryThread(
            id=self.next_thread_id,
            public_id=public_id,
            user_id=user_id,
            title=title,
            status=ThreadStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        self.next_thread_id += 1
        self.threads_by_public_id[public_id] = thread
        return thread

    async def get_thread_for_user(
        self,
        *,
        thread_public_id: str,
        user_id: int,
    ) -> QueryThread | None:
        thread = self.threads_by_public_id.get(thread_public_id)
        if thread is None or thread.user_id != user_id:
            return None
        return thread

    async def list_threads_for_user(
        self,
        *,
        user_id: int,
        limit: int,
        offset: int,
    ) -> Sequence[QueryThread]:
        owned = [
            thread for thread in self.threads_by_public_id.values() if thread.user_id == user_id
        ]
        return tuple(owned[offset : offset + limit])

    async def create_message(
        self,
        *,
        public_id: str,
        thread_id: int,
        user_id: int,
        role: MessageRole,
        content: str,
    ) -> ThreadMessage:
        message = ThreadMessage(
            id=self.next_message_id,
            public_id=public_id,
            thread_id=thread_id,
            user_id=user_id,
            role=role,
            content=content,
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
        self.next_message_id += 1
        self.messages_by_public_id[public_id] = message
        return message

    async def list_messages_for_thread(
        self,
        *,
        thread_id: int,
        user_id: int,
        limit: int,
        offset: int,
    ) -> Sequence[ThreadMessage]:
        owned = [
            message
            for message in self.messages_by_public_id.values()
            if message.thread_id == thread_id and message.user_id == user_id
        ]
        return tuple(owned[offset : offset + limit])


@pytest.mark.asyncio
async def test_get_or_create_user_creates_new_mirror() -> None:
    repository = FakeIdentityRepository()
    service = IdentityThreadService(repository)

    user = await service.get_or_create_user(
        external_subject="auth-user-1",
        display_name="Analyst",
    )

    assert user.id == 1
    assert user.external_subject == "auth-user-1"
    assert user.role is UserRole.USER
    assert user.display_name == "Analyst"


@pytest.mark.asyncio
async def test_get_or_create_user_touches_existing_mirror() -> None:
    repository = FakeIdentityRepository()
    service = IdentityThreadService(repository)

    first_user = await service.get_or_create_user(external_subject="auth-user-1")
    second_user = await service.get_or_create_user(external_subject="auth-user-1")

    assert second_user.id == first_user.id
    assert repository.touch_count == 1


@pytest.mark.asyncio
async def test_create_thread_for_subject_assigns_user_ownership() -> None:
    service = IdentityThreadService(FakeIdentityRepository())

    thread = await service.create_thread_for_subject(
        external_subject="auth-user-1",
        title="Sales question",
    )

    assert thread.user_id == 1
    assert thread.title == "Sales question"
    assert thread.status is ThreadStatus.ACTIVE


@pytest.mark.asyncio
async def test_get_owned_thread_blocks_cross_user_access() -> None:
    repository = FakeIdentityRepository()
    service = IdentityThreadService(repository)

    thread = await service.create_thread_for_subject(
        external_subject="owner",
        title="Owned thread",
    )
    await service.get_or_create_user(external_subject="other")

    owned = await service.get_owned_thread(
        thread_public_id=thread.public_id,
        external_subject="owner",
    )
    blocked = await service.get_owned_thread(
        thread_public_id=thread.public_id,
        external_subject="other",
    )

    assert owned == thread
    assert blocked is None


@pytest.mark.asyncio
async def test_create_message_for_subject_persists_owned_thread_message() -> None:
    service = IdentityThreadService(FakeIdentityRepository())
    thread = await service.create_thread_for_subject(
        external_subject="owner",
        title="Owned thread",
    )

    message = await service.create_message_for_subject(
        external_subject="owner",
        thread_public_id=thread.public_id,
        role=MessageRole.USER,
        content="上个月总销售额多少",
    )

    assert message.thread_id == thread.id
    assert message.user_id == thread.user_id
    assert message.role is MessageRole.USER
    assert message.content == "上个月总销售额多少"


@pytest.mark.asyncio
async def test_create_message_for_subject_blocks_cross_user_thread() -> None:
    repository = FakeIdentityRepository()
    service = IdentityThreadService(repository)
    thread = await service.create_thread_for_subject(
        external_subject="owner",
        title="Owned thread",
    )
    await service.get_or_create_user(external_subject="other")

    with pytest.raises(PermissionError):
        await service.create_message_for_subject(
            external_subject="other",
            thread_public_id=thread.public_id,
            role=MessageRole.USER,
            content="should be blocked",
        )


@pytest.mark.asyncio
async def test_list_messages_for_subject_keeps_thread_ownership() -> None:
    service = IdentityThreadService(FakeIdentityRepository())
    thread = await service.create_thread_for_subject(
        external_subject="owner",
        title="Owned thread",
    )
    first = await service.create_message_for_subject(
        external_subject="owner",
        thread_public_id=thread.public_id,
        role=MessageRole.USER,
        content="question",
    )
    second = await service.create_message_for_subject(
        external_subject="owner",
        thread_public_id=thread.public_id,
        role=MessageRole.ASSISTANT,
        content="answer",
    )

    messages = await service.list_messages_for_subject(
        external_subject="owner",
        thread_public_id=thread.public_id,
    )
    blocked = await service.list_messages_for_subject(
        external_subject="other",
        thread_public_id=thread.public_id,
    )

    assert messages == (first, second)
    assert blocked == ()
