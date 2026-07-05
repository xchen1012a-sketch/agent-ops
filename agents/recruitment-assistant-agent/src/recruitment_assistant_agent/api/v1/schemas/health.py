"""Health endpoint schemas."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    db_ok: bool
    engine_ready: bool
    error: str | None = None
