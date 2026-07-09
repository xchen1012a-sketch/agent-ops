"""Feishu webhook routes (reserved for future webhook mode)."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/feishu", tags=["feishu"])

# Webhook mode will be implemented in a future iteration.
