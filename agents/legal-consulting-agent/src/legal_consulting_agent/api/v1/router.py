"""Aggregate v1 endpoint routers."""

from __future__ import annotations

from fastapi import APIRouter

from legal_consulting_agent.api.v1.endpoints import health

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["health"])
