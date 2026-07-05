"""Aggregate v1 endpoint routers."""

from __future__ import annotations

from fastapi import APIRouter

from legal_consulting_agent.api.v1.endpoints import (
    health,
    legal_consultation_records,
    legal_feedbacks,
    legal_messages,
    legal_questions,
    legal_reports,
    legal_reviews,
    legal_runs,
    legal_sessions,
)

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(legal_consultation_records.router, tags=["legal-consultation-records"])
router.include_router(legal_sessions.router, tags=["legal-sessions"])
router.include_router(legal_questions.router, tags=["legal-questions"])
router.include_router(legal_messages.router, tags=["legal-messages"])
router.include_router(legal_feedbacks.router, tags=["legal-feedbacks"])
router.include_router(legal_reviews.router, tags=["legal-reviews"])
router.include_router(legal_reports.router, tags=["legal-reports"])
router.include_router(legal_runs.router, tags=["legal-runs"])
