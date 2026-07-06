"""FastAPI dependencies: settings, request-scoped DB session, request id."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from data_query_agent.application.services.agent_api_config import ApiConfigCrypto
from data_query_agent.application.services.audit_service import SqlAuditService
from data_query_agent.application.services.feishu_bot_service import (
    FeishuBotService,
    FeishuInboundMessage,
    feishu_subject,
)
from data_query_agent.application.services.feishu_webhook_service import (
    FeishuWebhookDeps,
    FeishuWebhookProcessor,
)
from data_query_agent.application.services.identity_service import IdentityThreadService
from data_query_agent.application.services.run_service import QueryRunTraceService
from data_query_agent.application.services.stream_adapter_resolver import resolve_stream_adapter
from data_query_agent.core.config import Settings, get_settings
from data_query_agent.core.errors import AuthError
from data_query_agent.core.logging import get_logger
from data_query_agent.core.request_context import REQUEST_ID_KEY, request_context
from data_query_agent.domain.ports.llm_adapter import LlmAdapter
from data_query_agent.infrastructure.db.repositories.agent_api_config import (
    SqlAlchemyAgentApiConfigRepository,
)
from data_query_agent.infrastructure.db.repositories.audit import SqlAlchemySqlAuditRepository
from data_query_agent.infrastructure.db.repositories.identity import SqlAlchemyIdentityRepository
from data_query_agent.infrastructure.db.repositories.run import SqlAlchemyRunRepository
from data_query_agent.infrastructure.db.session import get_session_factory
from data_query_agent.infrastructure.integrations.feishu_client import (
    FeishuClient,
    FeishuClientConfig,
    FeishuTokenCache,
    InMemoryFeishuTokenCache,
    RedisFeishuTokenCache,
    RedisLike,
)
from data_query_agent.infrastructure.integrations.feishu_event_dedup import (
    FeishuEventDedupStore,
    InMemoryFeishuEventDedupStore,
    RedisFeishuEventDedupStore,
)
from data_query_agent.infrastructure.integrations.feishu_events import FeishuMockEventService


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped async DB session; rollback on unhandled error."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_current_subject(x_user_subject: str | None = Header(default=None)) -> str:
    """Return authenticated upstream subject from gateway-provided header."""
    if x_user_subject is None or not x_user_subject.strip():
        raise AuthError("X-User-Subject header is required")
    return x_user_subject.strip()


def get_agent_api_config_crypto(settings: SettingsDep) -> ApiConfigCrypto:
    """Build the Fernet crypto service from settings."""

    return ApiConfigCrypto(settings.agent_config_encryption_key.get_secret_value())


def get_agent_api_config_repository(session: SessionDep) -> SqlAlchemyAgentApiConfigRepository:
    """Build the agent_api_config repository for the request scope."""

    return SqlAlchemyAgentApiConfigRepository(session)


def get_identity_thread_service(session: SessionDep) -> IdentityThreadService:
    """Build identity/thread service for request-scoped persistence."""
    return IdentityThreadService(SqlAlchemyIdentityRepository(session))


def get_query_run_trace_service(session: SessionDep) -> QueryRunTraceService:
    """Build query run trace service for request-scoped persistence."""
    return QueryRunTraceService(SqlAlchemyRunRepository(session))


def get_sql_audit_service(session: SessionDep) -> SqlAuditService:
    """Build SQL audit service for request-scoped persistence."""
    return SqlAuditService(SqlAlchemySqlAuditRepository(session))


_feishu_mock_event_service = FeishuMockEventService()


def get_feishu_mock_event_service() -> FeishuMockEventService:
    """Return process-local mock Feishu event service for fixture tests."""
    return _feishu_mock_event_service


_logger = get_logger(__name__)
_feishu_token_cache_inmemory = InMemoryFeishuTokenCache()
_feishu_dedup_inmemory = InMemoryFeishuEventDedupStore()
_feishu_redis_client: RedisLike | None = None
_feishu_redis_url: str | None = None


def _get_feishu_redis(settings: Settings) -> RedisLike | None:
    """Return a lazily-built shared redis client, or None when unconfigured.

    多 worker 下 token 缓存与事件去重必须共享；单进程/测试无 Redis 时回退进程内实现。
    """
    global _feishu_redis_client, _feishu_redis_url
    if not settings.redis_url:
        return None
    if _feishu_redis_client is None or _feishu_redis_url != settings.redis_url:
        from redis.asyncio import from_url

        _feishu_redis_client = cast(RedisLike, from_url(settings.redis_url))
        _feishu_redis_url = settings.redis_url
    return _feishu_redis_client


def _build_feishu_token_cache(settings: Settings) -> FeishuTokenCache:
    redis = _get_feishu_redis(settings)
    if redis is not None:
        return RedisFeishuTokenCache(redis)
    return _feishu_token_cache_inmemory


def _build_feishu_dedup(settings: Settings) -> FeishuEventDedupStore:
    redis = _get_feishu_redis(settings)
    if redis is not None:
        return RedisFeishuEventDedupStore(
            redis, ttl_seconds=settings.feishu_event_dedup_ttl_seconds
        )
    return _feishu_dedup_inmemory


async def _persist_feishu_subject(open_id: str) -> None:
    """Best-effort: ensure a subject-scoped user mirror exists for isolation.

    每个飞书用户落一条 subject 隔离锚点；锚点写入失败仅告警，不阻断回复。
    """
    subject = feishu_subject(open_id)
    try:
        factory = get_session_factory()
        async with factory() as session:
            service = IdentityThreadService(SqlAlchemyIdentityRepository(session))
            await service.get_or_create_user(external_subject=subject)
            await session.commit()
    except Exception as exc:
        _logger.warning("feishu.subject_persist_failed", subject=subject, error=str(exc))


def get_feishu_webhook_deps(settings: SettingsDep) -> FeishuWebhookDeps:
    """Assemble webhook collaborators; disabled unless FEISHU_ENABLED=true."""
    if not settings.feishu_enabled:
        return FeishuWebhookDeps(enabled=False, processor=None, dispatch=None)
    processor = FeishuWebhookProcessor(
        encrypt_key=settings.feishu_encrypt_key.get_secret_value(),
        verification_token=settings.feishu_verification_token.get_secret_value(),
        dedup=_build_feishu_dedup(settings),
    )
    client = FeishuClient(
        config=FeishuClientConfig.from_settings(settings),
        token_cache=_build_feishu_token_cache(settings),
    )
    bot = FeishuBotService(client=client)

    async def dispatch(message: FeishuInboundMessage) -> None:
        await _persist_feishu_subject(message.open_id)
        await bot.answer_message(message)

    return FeishuWebhookDeps(enabled=True, processor=processor, dispatch=dispatch)


async def get_llm_stream_adapter(
    subject: CurrentSubjectDep,
    repo: AgentApiConfigRepoDep,
    settings: SettingsDep,
) -> LlmAdapter:
    """Resolve the streaming LLM adapter from the current account's API config.

    CONFIG-200：读该账号的 deepseek 配置，启用且有可解密 key → 真实 DeepSeek 流式；
    否则回退 FakeLlmAdapter（未配置 key 时行为不变）。
    """
    return await resolve_stream_adapter(subject=subject, reader=repo, settings=settings)


def get_request_id(request: Request) -> str:
    """Return the request id assigned by middleware; fall back to header or unknown."""
    value = request_context.get(REQUEST_ID_KEY)
    if isinstance(value, str) and value:
        return value
    return request.headers.get("x-request-id", "unknown")


SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
RequestIdDep = Annotated[str, Depends(get_request_id)]
CurrentSubjectDep = Annotated[str, Depends(get_current_subject)]
AgentApiConfigRepoDep = Annotated[
    SqlAlchemyAgentApiConfigRepository, Depends(get_agent_api_config_repository)
]
AgentApiConfigCryptoDep = Annotated[ApiConfigCrypto, Depends(get_agent_api_config_crypto)]
IdentityThreadServiceDep = Annotated[IdentityThreadService, Depends(get_identity_thread_service)]
QueryRunTraceServiceDep = Annotated[QueryRunTraceService, Depends(get_query_run_trace_service)]
SqlAuditServiceDep = Annotated[SqlAuditService, Depends(get_sql_audit_service)]
FeishuMockEventServiceDep = Annotated[
    FeishuMockEventService, Depends(get_feishu_mock_event_service)
]
FeishuWebhookDepsDep = Annotated[FeishuWebhookDeps, Depends(get_feishu_webhook_deps)]
LlmStreamAdapterDep = Annotated[LlmAdapter, Depends(get_llm_stream_adapter)]
