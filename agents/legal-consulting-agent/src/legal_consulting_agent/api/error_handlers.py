"""HTTP exception handlers producing the unified error envelope."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from legal_consulting_agent.core.errors import AppError, build_error_envelope
from legal_consulting_agent.core.request_context import REQUEST_ID_KEY, request_context


def register_error_handlers(app: FastAPI) -> None:
    """Register domain and fallback exception handlers on the FastAPI app."""

    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content=build_error_envelope(
                request_id=_current_request_id(),
                code=exc.code,
                message=exc.message,
                retryable=exc.retryable,
                details=exc.details,
            ),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled.exception", error_type=type(exc).__name__)
        return JSONResponse(
            status_code=500,
            content=build_error_envelope(
                request_id=_current_request_id(),
                code="INTERNAL_ERROR",
                message="Internal server error",
                retryable=False,
            ),
        )


def _current_request_id() -> str:
    value = request_context.get(REQUEST_ID_KEY)
    return value if isinstance(value, str) and value else "unknown"
