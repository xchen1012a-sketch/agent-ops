"""Aggregate v1 endpoint routers."""

from __future__ import annotations

from fastapi import APIRouter

from recruitment_assistant_agent.api.v1.endpoints import (
    admin_api_config,
    health,
    recruitment_admin,
    recruitment_reports,
    recruitment_runs,
    recruitment_tasks,
)

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(recruitment_tasks.router, tags=["recruitment-tasks"])
router.include_router(recruitment_runs.router, tags=["recruitment-runs"])
router.include_router(recruitment_admin.router, tags=["recruitment-admin"])
router.include_router(recruitment_reports.router, tags=["recruitment-reports"])
router.include_router(admin_api_config.router, tags=["admin-api-config"])
