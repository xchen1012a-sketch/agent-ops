"""Current-user endpoints for the agent API config center (CONFIG-100)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from recruitment_assistant_agent.api.dependencies import (
    AgentApiConfigCryptoDep,
    AgentApiConfigRepoDep,
    CurrentUserPublicIdDep,
)
from recruitment_assistant_agent.api.v1.schemas.agent_api_config import (
    AgentApiConfigEnvelope,
    AgentApiConfigListData,
    AgentApiConfigListEnvelope,
    AgentApiConfigUpdate,
    AgentApiConfigView,
)
from recruitment_assistant_agent.core.errors import ConfigNotFoundError

router = APIRouter()

_API_TYPE_DEFAULTS = {
    "deepseek": "DeepSeek LLM（必需）",
    "ocr": "OCR（扫描简历/JD 可选）",
}
_ALLOWED_API_TYPES = frozenset(_API_TYPE_DEFAULTS)


def _to_view(entity) -> AgentApiConfigView:  # type: ignore[no-untyped-def]
    return AgentApiConfigView(
        user_public_id=entity.user_public_id,
        api_type=entity.api_type,
        display_name=entity.display_name,
        base_url=entity.base_url,
        model=entity.model,
        api_key_hint=entity.api_key_hint,
        timeout_seconds=entity.timeout_seconds,
        max_retries=entity.max_retries,
        enabled=entity.enabled,
        extra=entity.extra,
        updated_by=entity.updated_by,
        updated_at=entity.updated_at,
    )


def _empty_view(user_public_id: str, api_type: str) -> AgentApiConfigView:
    return AgentApiConfigView(
        user_public_id=user_public_id,
        api_type=api_type,
        display_name=_API_TYPE_DEFAULTS[api_type],
        base_url=None,
        model=None,
        api_key_hint=None,
        timeout_seconds=None,
        max_retries=None,
        enabled=False,
        extra=None,
        updated_by=user_public_id,
        updated_at=datetime.now(UTC),
    )


@router.get(
    "/me/api-config",
    response_model=AgentApiConfigListEnvelope,
)
async def list_api_configs(
    user_public_id: CurrentUserPublicIdDep,
    repo: AgentApiConfigRepoDep,
) -> AgentApiConfigListEnvelope:
    """List upstream API dependencies configured by the current user."""

    items = await repo.list_for_user(user_public_id)
    views = {_item.api_type: _to_view(_item) for _item in items}
    for api_type in _API_TYPE_DEFAULTS:
        views.setdefault(api_type, _empty_view(user_public_id, api_type))
    return AgentApiConfigListEnvelope(data=AgentApiConfigListData(items=list(views.values())))


@router.get(
    "/me/api-config/{api_type}",
    response_model=AgentApiConfigEnvelope,
)
async def get_api_config(
    api_type: str,
    user_public_id: CurrentUserPublicIdDep,
    repo: AgentApiConfigRepoDep,
) -> AgentApiConfigEnvelope:
    """Fetch one current-user API dependency by api_type."""

    if api_type not in _ALLOWED_API_TYPES:
        raise ConfigNotFoundError(f"unknown api_type: {api_type}")
    entity = await repo.get_by_type(user_public_id, api_type)
    if entity is None:
        raise ConfigNotFoundError(f"api_type not configured: {api_type}")
    return AgentApiConfigEnvelope(data=_to_view(entity))


@router.put(
    "/me/api-config/{api_type}",
    response_model=AgentApiConfigEnvelope,
)
async def update_api_config(
    api_type: str,
    payload: AgentApiConfigUpdate,
    user_public_id: CurrentUserPublicIdDep,
    repo: AgentApiConfigRepoDep,
    crypto: AgentApiConfigCryptoDep,
) -> AgentApiConfigEnvelope:
    """Create or update a current-user API dependency.

    `api_key` is encrypted at write time; only the masked hint is returned.
    An empty `api_key` keeps the existing encrypted value unchanged.
    """

    if api_type not in _ALLOWED_API_TYPES:
        raise ConfigNotFoundError(f"unknown api_type: {api_type}")

    existing = await repo.get_by_type(user_public_id, api_type)
    api_key_encrypted = existing.api_key_encrypted if existing is not None else None
    api_key_hint = existing.api_key_hint if existing is not None else None

    if payload.api_key:
        api_key_encrypted = crypto.encrypt(payload.api_key)
        api_key_hint = crypto.hint(payload.api_key)

    entity = await repo.upsert(
        user_public_id=user_public_id,
        api_type=api_type,
        display_name=payload.display_name,
        base_url=payload.base_url,
        model=payload.model,
        api_key_encrypted=api_key_encrypted,
        api_key_hint=api_key_hint,
        timeout_seconds=payload.timeout_seconds,
        max_retries=payload.max_retries,
        enabled=payload.enabled,
        extra=payload.extra,
        updated_by=user_public_id,
    )
    return AgentApiConfigEnvelope(data=_to_view(entity))
