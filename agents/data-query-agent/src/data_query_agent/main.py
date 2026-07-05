"""FastAPI application entrypoint for data-query-agent."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from data_query_agent.api.error_handlers import register_error_handlers
from data_query_agent.api.middleware import RequestContextMiddleware
from data_query_agent.api.v1.router import router as v1_router
from data_query_agent.core.config import get_settings
from data_query_agent.core.logging import configure_logging, get_logger
from data_query_agent.infrastructure.db.session import (
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
        title="data-query-agent",
        version="0.1.0",
        lifespan=lifespan,
        openapi_url="/openapi.json",
        docs_url="/docs",
    )
    app.add_middleware(RequestContextMiddleware)
    app.include_router(v1_router, prefix="/v1")
    app.include_router(v1_router, prefix="/api/data/v1")
    register_error_handlers(app)
    return app


app = create_app()
