"""Integration tests for health endpoints."""

from __future__ import annotations

from httpx import AsyncClient


async def test_live_returns_ok(app_client: AsyncClient) -> None:
    response = await app_client.get("/v1/health/live")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


async def test_live_available_on_legacy_prefix(app_client: AsyncClient) -> None:
    response = await app_client.get("/api/recruitment/v1/health/live")
    assert response.status_code == 200
