"""Aggregate v1 endpoint routers."""

from __future__ import annotations

from fastapi import APIRouter

from data_query_agent.api.v1.endpoints import health, threads

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(threads.router, prefix="/threads", tags=["threads"])
