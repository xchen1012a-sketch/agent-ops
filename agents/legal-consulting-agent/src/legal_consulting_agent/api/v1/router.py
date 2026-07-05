"""Aggregate v1 endpoint routers."""

from __future__ import annotations

from fastapi import APIRouter

from legal_consulting_agent.api.v1.endpoints import (
    health,
    legal_messages,
    legal_questions,
    legal_sessions,
)

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(legal_sessions.router, tags=["legal-sessions"])
router.include_router(legal_questions.router, tags=["legal-questions"])
router.include_router(legal_messages.router, tags=["legal-messages"])
