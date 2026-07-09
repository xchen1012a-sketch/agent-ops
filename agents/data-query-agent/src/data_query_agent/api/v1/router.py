"""Aggregate v1 endpoint routers."""

from __future__ import annotations

from fastapi import APIRouter

from data_query_agent.api.v1.endpoints import (
    admin_api_config,
    feishu_events,
    feishu_webhook,
    health,
    query_history,
    runs,
    threads,
)

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(threads.router, prefix="/threads", tags=["threads"])
router.include_router(runs.router, tags=["runs"])
router.include_router(query_history.router, tags=["query-history"])
router.include_router(feishu_events.router, tags=["feishu-events"])
router.include_router(feishu_webhook.router, tags=["feishu-webhook"])
router.include_router(admin_api_config.router, tags=["admin-api-config"])
