"""HTTP middleware: assign request id, basic access log."""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from legal_consulting_agent.core.request_context import REQUEST_ID_KEY, request_context

REQUEST_ID_HEADER = "x-request-id"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Populate request-scoped context with an id for logs and error envelopes."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or _new_request_id()
        current = request_context.get() or {}
        token = request_context.set({**current, REQUEST_ID_KEY: request_id})
        try:
            response = await call_next(request)
        finally:
            request_context.reset(token)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


def _new_request_id() -> str:
    return uuid.uuid4().hex
