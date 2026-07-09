"""FastAPI application entrypoint for legal-consulting-agent."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from legal_consulting_agent.api.error_handlers import register_error_handlers
from legal_consulting_agent.api.middleware import RequestContextMiddleware
from legal_consulting_agent.api.v1.router import router as v1_router
from legal_consulting_agent.core.config import get_settings
from legal_consulting_agent.core.logging import configure_logging, get_logger
from legal_consulting_agent.infrastructure.db.session import (
    close_db_engine,
    init_db_engine,
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings)
    logger = get_logger(__name__)
    logger.info(
        "application.starting",
        app=settings.app_name,
        env=settings.app_env,
        port=settings.app_port,
    )
    settings.validate_required()
    await init_db_engine(settings)
    try:
        yield
    finally:
        await close_db_engine()
        logger.info("application.stopped", app=settings.app_name)


def create_app() -> FastAPI:
    app = FastAPI(
        title="legal-consulting-agent",
        version="0.1.0",
        lifespan=lifespan,
        openapi_url="/openapi.json",
        docs_url="/docs",
    )
    app.add_middleware(RequestContextMiddleware)
    app.include_router(v1_router, prefix="/v1")
    app.include_router(v1_router, prefix="/api/legal/v1")
    register_error_handlers(app)
    return app


app = create_app()
