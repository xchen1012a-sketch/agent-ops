"""Unit tests for LEGAL-130 application services."""

from __future__ import annotations

from datetime import datetime

import pytest

from legal_consulting_agent.application.services import (
    LegalDataNotFoundError,
    LegalDataService,
)
from legal_consulting_agent.domain.entities.legal_data import (
    AgentRun,
    LegalCategory,
    LegalMessage,
    LegalSession,
    NodeRun,
    UserMirror,
)
from legal_consulting_agent.domain.value_objects.legal_enums import (
    MessageRole,
    RunStatus,
    SessionStatus,
    UserRole,
    UserStatus,
)


class FakeLegalDataRepository:
    """In-memory repository test double that never commits transactions."""

    def __init__(self) -> None:
        self.user: UserMirror | None = None
        self.category: LegalCategory | None = None
        self.session: LegalSession | None = None
        self.messages: list[LegalMessage] = []
        self.agent_runs: list[AgentRun] = []
        self.node_runs: list[NodeRun] = []

    async def upsert_user_mirror(self, user: UserMirror) -> UserMirror:
        self.user = UserMirror(
            id=1,
            public_id=user.public_id,
            email=user.email,
            display_name=user.display_name,
            role=user.role,
            status=user.status,
        )
        return self.user

    async def get_user_by_public_id(self, public_id: str) -> UserMirror | None:
        if self.user is None or self.user.public_id != public_id:
            return None
        return self.user

    async def get_category_by_code(self, code: str) -> LegalCategory | None:
        if self.category is None or self.category.code != code:
            return None
        return self.category

    async def create_session(self, session: LegalSession) -> LegalSession:
        self.session = LegalSession(
            id=10,
            public_id=session.public_id,
            user_id=session.user_id,
            category_id=session.category_id,
            title=session.title,
            status=session.status,
            last_message_at=session.last_message_at,
        )
        return self.session

    async def get_session_for_user(
        self,
        *,
        session_public_id: str,
        user_id: int,
    ) -> LegalSession | None:
        if (
            self.session is None
            or self.session.public_id != session_public_id
            or self.session.user_id != user_id
        ):
            return None
        return self.session

    async def append_message(self, message: LegalMessage) -> LegalMessage:
        persisted = LegalMessage(
            id=len(self.messages) + 1,
            public_id=message.public_id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            citations=message.citations,
            high_risk=message.high_risk,
            prompt_version=message.prompt_version,
        )
        self.messages.append(persisted)
        return persisted

    async def create_agent_run(self, run: AgentRun) -> AgentRun:
        persisted = AgentRun(
            id=20,
            public_id=run.public_id,
            thread_id=run.thread_id,
            user_id=run.user_id,
            workflow_version=run.workflow_version,
            prompt_version=run.prompt_version,
            status=run.status,
            retry_count=run.retry_count,
            error_code=run.error_code,
            error_summary=run.error_summary,
            started_at=run.started_at,
            finished_at=run.finished_at,
            duration_ms=run.duration_ms,
        )
        self.agent_runs.append(persisted)
        return persisted

    async def create_node_run(self, node_run: NodeRun) -> NodeRun:
        persisted = NodeRun(
            id=30,
            run_id=node_run.run_id,
            node_name=node_run.node_name,
            status=node_run.status,
            duration_ms=node_run.duration_ms,
            error_code=node_run.error_code,
            metadata=node_run.metadata,
            started_at=node_run.started_at,
            finished_at=node_run.finished_at,
        )
        self.node_runs.append(persisted)
        return persisted


@pytest.mark.asyncio
async def test_sync_user_mirror_does_not_require_password() -> None:
    repo = FakeLegalDataRepository()
    service = LegalDataService(repo)

    user = await service.sync_user_mirror(
        public_id="user-public-id",
        email="user@example.test",
        display_name="User",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )

    assert user.id == 1
    assert user.public_id == "user-public-id"
    assert user.role is UserRole.USER


@pytest.mark.asyncio
async def test_create_session_requires_existing_user_and_category() -> None:
    repo = FakeLegalDataRepository()
    service = LegalDataService(repo)

    with pytest.raises(LegalDataNotFoundError):
        await service.create_session(
            user_public_id="missing",
            category_code="civil_labor",
            title="劳动合同",
        )


@pytest.mark.asyncio
async def test_create_session_uses_existing_user_and_category() -> None:
    repo = FakeLegalDataRepository()
    repo.user = UserMirror(
        id=1,
        public_id="user-public-id",
        email="user@example.test",
        display_name=None,
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    repo.category = LegalCategory(
        id=2,
        public_id="category-public-id",
        code="civil_labor",
        display_name="劳动争议",
        description=None,
        sort_order=0,
    )
    service = LegalDataService(repo)

    session = await service.create_session(
        user_public_id="user-public-id",
        category_code="civil_labor",
        title="劳动合同",
    )

    assert session.id == 10
    assert session.user_id == 1
    assert session.category_id == 2
    assert session.status is SessionStatus.ACTIVE


@pytest.mark.asyncio
async def test_append_message_enforces_session_ownership() -> None:
    repo = FakeLegalDataRepository()
    repo.user = UserMirror(
        id=1,
        public_id="user-public-id",
        email="user@example.test",
        display_name=None,
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    repo.session = LegalSession(
        id=10,
        public_id="thread-public-id",
        user_id=1,
        category_id=2,
        title=None,
        status=SessionStatus.ACTIVE,
        last_message_at=None,
    )
    service = LegalDataService(repo)

    message = await service.append_message(
        user_public_id="user-public-id",
        session_public_id="thread-public-id",
        role=MessageRole.USER,
        content="公司单方面调岗，我可以拒绝吗？",
    )

    assert message.session_id == 10
    assert message.role is MessageRole.USER


@pytest.mark.asyncio
async def test_create_run_and_node_audit_records() -> None:
    repo = FakeLegalDataRepository()
    service = LegalDataService(repo)
    started_at = datetime(2026, 7, 5, 12, 0, 0)

    run = await service.create_agent_run(
        thread_id="thread-public-id",
        user_id=1,
        workflow_version="legal-v1",
        prompt_version="legal_generation:v1",
        started_at=started_at,
    )
    node = await service.create_node_run(
        run_id=run.id or 0,
        node_name="input_safety",
        status=RunStatus.PENDING,
        started_at=started_at,
        metadata={"input_length": 18},
    )

    assert run.status is RunStatus.PENDING
    assert node.run_id == 20
    assert node.metadata == {"input_length": 18}
