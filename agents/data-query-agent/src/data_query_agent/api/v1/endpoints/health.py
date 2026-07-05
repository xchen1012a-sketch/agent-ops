"""Health endpoints: liveness and readiness probes."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from data_query_agent.api.dependencies import SessionDep
from data_query_agent.api.v1.schemas.health import HealthResponse, ReadyResponse
from data_query_agent.infrastructure.db.session import is_engine_ready

router = APIRouter()


@router.get("/live", response_model=HealthResponse)
async def live() -> HealthResponse:
    """Liveness probe: process is up; no dependency checks."""
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadyResponse)
async def ready(session: SessionDep) -> ReadyResponse:
    """Readiness probe: ping DB via SELECT 1; report component status."""
    db_ok = True
    db_error: str | None = None
    try:
        await session.execute(text("SELECT 1"))
    except OperationalError as exc:
        db_ok = False
        db_error = str(exc.orig) if exc.orig else "database operational error"
    return ReadyResponse(
        status="ok" if db_ok else "degraded",
        db_ok=db_ok,
        engine_ready=is_engine_ready(),
        error=db_error,
    )
