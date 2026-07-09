"""FastAPI app for the auth service.

Router is mounted under both `/` (direct access on :8081) and `/api/auth`
(matching the frontend `authApi` baseURL and the vite dev proxy default).
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth_service.api.routes import router
from auth_service.config import get_settings

logger = logging.getLogger("auth_service")


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=logging.INFO)

    app = FastAPI(
        title="auth-service",
        version="0.1.0",
        openapi_url="/openapi.json",
        docs_url="/docs",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.allowed_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    app.include_router(router, prefix="/api/auth")

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "ok"}

    logger.info("auth_service.ready port=%s", settings.service_port)
    return app


app = create_app()
