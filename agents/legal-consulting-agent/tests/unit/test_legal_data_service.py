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
    ConsultationRecord,
    Feedback,
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
        self.consultation_records: list[ConsultationRecord] = []
        self.feedbacks: list[Feedback] = []
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

    async def get_message_for_session(
        self,
        *,
        message_public_id: str,
        session_id: int,
        role: MessageRole,
    ) -> LegalMessage | None:
        return next(
            (
                message
                for message in self.messages
                if message.public_id == message_public_id
                and message.session_id == session_id
                and message.role is role
            ),
            None,
        )

    async def create_consultation_record(
        self,
        record: ConsultationRecord,
    ) -> ConsultationRecord:
        persisted = ConsultationRecord(
            id=40,
            public_id=record.public_id,
            user_id=record.user_id,
            session_id=record.session_id,
            category_id=record.category_id,
            question_message_id=record.question_message_id,
            answer_message_id=record.answer_message_id,
            summary=record.summary,
            citations=record.citations,
            high_risk=record.high_risk,
            disclaimer=record.disclaimer,
        )
        self.consultation_records.append(persisted)
        return persisted

    async def create_feedback(self, feedback: Feedback) -> Feedback:
        persisted = Feedback(
            id=50,
            message_id=feedback.message_id,
            user_id=feedback.user_id,
            rating=feedback.rating,
            comment=feedback.comment,
        )
        self.feedbacks.append(persisted)
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


@pytest.mark.asyncio
async def test_create_agent_run_requires_user_owned_session() -> None:
    repo = FakeLegalDataRepository()
    repo.session = LegalSession(
        id=10,
        public_id="thread-public-id",
        user_id=2,
        category_id=2,
        title=None,
        status=SessionStatus.ACTIVE,
        last_message_at=None,
    )
    service = LegalDataService(repo)

    with pytest.raises(LegalDataNotFoundError):
        await service.create_agent_run(
            thread_id="thread-public-id",
            user_id=1,
            workflow_version="legal-v1",
            prompt_version="legal_generation:v1",
            started_at=datetime(2026, 7, 5, 12, 0, 0),
        )

    assert repo.agent_runs == []


@pytest.mark.asyncio
async def test_create_consultation_record_uses_owned_message_pair() -> None:
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
    repo.messages = [
        LegalMessage(
            id=11,
            public_id="question-public-id",
            session_id=10,
            role=MessageRole.USER,
            content="公司单方面调岗，我可以拒绝吗？",
            citations=None,
            high_risk=False,
            prompt_version=None,
        ),
        LegalMessage(
            id=12,
            public_id="answer-public-id",
            session_id=10,
            role=MessageRole.ASSISTANT,
            content="需要结合劳动合同约定判断。",
            citations=[{"material_id": "material-1"}],
            high_risk=True,
            prompt_version="legal_generation:v1",
        ),
    ]
    service = LegalDataService(repo)

    record = await service.create_consultation_record(
        user_public_id="user-public-id",
        session_public_id="thread-public-id",
        question_message_public_id="question-public-id",
        answer_message_public_id="answer-public-id",
        summary="劳动合同调岗争议",
        disclaimer="本回答仅供参考，不构成正式法律意见。",
    )

    assert record.id == 40
    assert record.user_id == 1
    assert record.category_id == 2
    assert record.question_message_id == 11
    assert record.answer_message_id == 12
    assert record.citations == [{"material_id": "material-1"}]
    assert record.high_risk is True


@pytest.mark.asyncio
async def test_create_consultation_record_rejects_cross_session_or_wrong_role() -> None:
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
    repo.messages = [
        LegalMessage(
            id=11,
            public_id="question-public-id",
            session_id=99,
            role=MessageRole.USER,
            content="其他会话的问题",
            citations=None,
            high_risk=False,
            prompt_version=None,
        ),
        LegalMessage(
            id=12,
            public_id="answer-public-id",
            session_id=10,
            role=MessageRole.USER,
            content="角色错误的回答",
            citations=None,
            high_risk=False,
            prompt_version=None,
        ),
    ]
    service = LegalDataService(repo)

    with pytest.raises(LegalDataNotFoundError):
        await service.create_consultation_record(
            user_public_id="user-public-id",
            session_public_id="thread-public-id",
            question_message_public_id="question-public-id",
            answer_message_public_id="answer-public-id",
            summary="无效记录",
            disclaimer="本回答仅供参考。",
        )

    assert repo.consultation_records == []


@pytest.mark.asyncio
async def test_create_feedback_uses_owned_assistant_message() -> None:
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
    repo.messages = [
        LegalMessage(
            id=12,
            public_id="answer-public-id",
            session_id=10,
            role=MessageRole.ASSISTANT,
            content="需要结合劳动合同约定判断。",
            citations=None,
            high_risk=False,
            prompt_version="legal_generation:v1",
        )
    ]
    service = LegalDataService(repo)

    feedback = await service.create_feedback(
        user_public_id="user-public-id",
        session_public_id="thread-public-id",
        message_public_id="answer-public-id",
        rating=5,
        comment="回答清晰",
    )

    assert feedback.id == 50
    assert feedback.user_id == 1
    assert feedback.message_id == 12
    assert feedback.rating == 5


@pytest.mark.asyncio
async def test_create_feedback_rejects_invalid_rating_before_repository_access() -> None:
    repo = FakeLegalDataRepository()
    service = LegalDataService(repo)

    with pytest.raises(ValueError, match="rating must be between 1 and 5"):
        await service.create_feedback(
            user_public_id="user-public-id",
            session_public_id="thread-public-id",
            message_public_id="answer-public-id",
            rating=6,
            comment=None,
        )

    assert repo.feedbacks == []


@pytest.mark.asyncio
async def test_create_feedback_enforces_user_and_session_ownership() -> None:
    missing_user_repo = FakeLegalDataRepository()
    missing_user_service = LegalDataService(missing_user_repo)

    with pytest.raises(LegalDataNotFoundError):
        await missing_user_service.create_feedback(
            user_public_id="missing-user",
            session_public_id="thread-public-id",
            message_public_id="answer-public-id",
            rating=4,
            comment=None,
        )

    wrong_owner_repo = FakeLegalDataRepository()
    wrong_owner_repo.user = UserMirror(
        id=1,
        public_id="user-public-id",
        email="user@example.test",
        display_name=None,
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    wrong_owner_repo.session = LegalSession(
        id=10,
        public_id="thread-public-id",
        user_id=2,
        category_id=2,
        title=None,
        status=SessionStatus.ACTIVE,
        last_message_at=None,
    )
    wrong_owner_service = LegalDataService(wrong_owner_repo)

    with pytest.raises(LegalDataNotFoundError):
        await wrong_owner_service.create_feedback(
            user_public_id="user-public-id",
            session_public_id="thread-public-id",
            message_public_id="answer-public-id",
            rating=4,
            comment=None,
        )

    assert missing_user_repo.feedbacks == []
    assert wrong_owner_repo.feedbacks == []


@pytest.mark.asyncio
async def test_create_feedback_rejects_user_message() -> None:
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
    repo.messages = [
        LegalMessage(
            id=11,
            public_id="question-public-id",
            session_id=10,
            role=MessageRole.USER,
            content="用户问题",
            citations=None,
            high_risk=False,
            prompt_version=None,
        )
    ]
    service = LegalDataService(repo)

    with pytest.raises(LegalDataNotFoundError):
        await service.create_feedback(
            user_public_id="user-public-id",
            session_public_id="thread-public-id",
            message_public_id="question-public-id",
            rating=4,
            comment=None,
        )

    assert repo.feedbacks == []
