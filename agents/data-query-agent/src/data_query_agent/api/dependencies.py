"""FastAPI dependencies: settings, request-scoped DB session, request id."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends, Header, Request
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from data_query_agent.application.services.agent_api_config import ApiConfigCrypto
from data_query_agent.application.services.audit_service import SqlAuditService
from data_query_agent.application.services.data_catalog_service import DataCatalogService
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
from data_query_agent.application.services.prompt_template_service import PromptTemplateService
from data_query_agent.application.services.run_service import QueryRunTraceService
from data_query_agent.application.services.shop_schema_loader import ShopSchemaLoader
from data_query_agent.application.services.stream_adapter_resolver import (
    resolve_chat_adapter,
    resolve_stream_adapter,
)
from data_query_agent.core.config import Settings, get_settings
from data_query_agent.core.errors import AuthError
from data_query_agent.core.logging import get_logger
from data_query_agent.core.request_context import REQUEST_ID_KEY, request_context
from data_query_agent.domain.ports.llm_adapter import (
    LlmAdapter,
    LlmCompletionRequest,
    LlmCompletionResponse,
    LlmStreamChunk,
)
from data_query_agent.domain.ports.query_adapter import ReadOnlyQueryAdapter
from data_query_agent.infrastructure.db.repositories.agent_api_config import (
    SqlAlchemyAgentApiConfigRepository,
)
from data_query_agent.infrastructure.db.repositories.audit import SqlAlchemySqlAuditRepository
from data_query_agent.infrastructure.db.repositories.identity import SqlAlchemyIdentityRepository
from data_query_agent.infrastructure.db.repositories.run import SqlAlchemyRunRepository
from data_query_agent.infrastructure.db.session import get_session_factory
from data_query_agent.infrastructure.db.sqlalchemy_query_adapter import (
    SqlAlchemyReadOnlyQueryAdapter,
)
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


async def get_feishu_webhook_deps(
    settings: SettingsDep,
    repo: AgentApiConfigRepoDep,
    crypto: AgentApiConfigCryptoDep,
) -> FeishuWebhookDeps:
    """Assemble webhook collaborators from the latest enabled feishu config row.

    FEISHU-300: 配置从 ``agent_api_config`` 表的「最新启用 feishu 行」读取，
    而非环境变量。``FEISHU_ENABLED`` 保留为应急 kill switch（默认 false）。
    Webhook 调用频率低，直接每次查 DB；新增/更新配置后无需重启或失效缓存。
    """
    if not settings.feishu_enabled:
        return FeishuWebhookDeps(enabled=False, processor=None, dispatch=None)

    entity = await repo.get_latest_enabled_feishu_config()
    if entity is None or not entity.api_key_encrypted or not entity.extra:
        return FeishuWebhookDeps(enabled=False, processor=None, dispatch=None)

    app_id = str(entity.extra.get("app_id") or "")
    verification_token = str(entity.extra.get("verification_token") or "")
    encrypt_key = str(entity.extra.get("encrypt_key") or "")
    if not app_id or not verification_token:
        return FeishuWebhookDeps(enabled=False, processor=None, dispatch=None)

    app_secret = crypto.decrypt(entity.api_key_encrypted)
    client_config = FeishuClientConfig(
        api_base=entity.base_url or settings.feishu_api_base,
        app_id=app_id,
        app_secret=SecretStr(app_secret),
        timeout_seconds=entity.timeout_seconds or settings.feishu_timeout_seconds,
        token_cache_ttl_seconds=settings.feishu_token_cache_ttl_seconds,
    )
    processor = FeishuWebhookProcessor(
        encrypt_key=encrypt_key,
        verification_token=verification_token,
        dedup=_build_feishu_dedup(settings),
    )
    client = FeishuClient(
        config=client_config,
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


async def get_chat_llm_adapter(
    subject: CurrentSubjectDep,
    repo: AgentApiConfigRepoDep,
    settings: SettingsDep,
) -> LlmAdapter:
    """Resolve the non-streaming LLM adapter used for NL2SQL / interpret prompts.

    This path drives executable SQL generation, so it resolves lazily. Boundary
    replies such as greetings should not fail just because the account has not
    configured a real model key.
    """
    return _LazyChatLlmAdapter(subject=subject, repo=repo, settings=settings)


class _LazyChatLlmAdapter:
    """Resolve the real chat adapter only when a model call is actually needed."""

    def __init__(
        self,
        *,
        subject: str,
        repo: SqlAlchemyAgentApiConfigRepository,
        settings: Settings,
    ) -> None:
        self._subject = subject
        self._repo = repo
        self._settings = settings
        self._adapter: LlmAdapter | None = None

    async def _resolve(self) -> LlmAdapter:
        if self._adapter is None:
            self._adapter = await resolve_chat_adapter(
                subject=self._subject,
                reader=self._repo,
                settings=self._settings,
            )
        return self._adapter

    async def complete(self, request: LlmCompletionRequest) -> LlmCompletionResponse:
        adapter = await self._resolve()
        return await adapter.complete(request)

    async def stream(self, request: LlmCompletionRequest) -> AsyncIterator[LlmStreamChunk]:
        adapter = await self._resolve()
        async for chunk in adapter.stream(request):
            yield chunk


def get_prompt_template_service() -> PromptTemplateService:
    """Return the singleton prompt template service."""
    return _prompt_template_service


def get_query_adapter(settings: SettingsDep) -> ReadOnlyQueryAdapter:
    """Return the shop_db read-only query adapter (cached per URL)."""
    return SqlAlchemyReadOnlyQueryAdapter(read_url=settings.shop_db_read_url)


def get_shop_schema_loader(settings: SettingsDep) -> ShopSchemaLoader:
    """Return the shop_db schema loader bound to the SQL whitelist."""
    return ShopSchemaLoader(
        schema_path=settings.shop_schema_path,
        whitelist=DataCatalogService().load_sql_whitelist(),
    )


def get_data_catalog_service() -> DataCatalogService:
    """Return the data catalog service (whitelist + fixtures)."""
    return DataCatalogService()


_prompt_template_service = PromptTemplateService()


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
ChatLlmAdapterDep = Annotated[LlmAdapter, Depends(get_chat_llm_adapter)]
PromptTemplateServiceDep = Annotated[PromptTemplateService, Depends(get_prompt_template_service)]
QueryAdapterDep = Annotated[ReadOnlyQueryAdapter, Depends(get_query_adapter)]
ShopSchemaLoaderDep = Annotated[ShopSchemaLoader, Depends(get_shop_schema_loader)]
DataCatalogServiceDep = Annotated[DataCatalogService, Depends(get_data_catalog_service)]
