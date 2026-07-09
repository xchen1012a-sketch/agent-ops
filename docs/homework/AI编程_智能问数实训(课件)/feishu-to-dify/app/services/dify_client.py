"""Dify workflow API client with SSE streaming support."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Settings
from app.models.schemas import DifyStreamEvent
from app.utils.logging import get_logger

logger = get_logger(__name__)


class DifyClientError(Exception):
    """Raised when Dify API returns an error."""


@dataclass
class WorkflowFinishedResult:
    success: bool
    output: str | None = None
    error: str | None = None


class DifyWorkflowClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._headers = {
            "Authorization": f"Bearer {settings.dify_api_key}",
            "Content-Type": "application/json",
        }

    async def run_stream(
        self,
        query: str,
        user: str,
    ) -> AsyncIterator[DifyStreamEvent]:
        payload = {
            "inputs": {self._settings.dify_input_key: query},
            "response_mode": "streaming",
            "user": user,
        }
        timeout = httpx.Timeout(self._settings.dify_timeout, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                self._settings.dify_workflow_run_url,
                headers=self._headers,
                json=payload,
            ) as response:
                if response.status_code >= 400:
                    body = await response.aread()
                    raise DifyClientError(
                        f"Dify HTTP {response.status_code}: {body.decode('utf-8', errors='ignore')}"
                    )

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if not raw:
                        continue
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        logger.warning("skip invalid sse json: {}", raw[:200])
                        continue

                    event_name = data.get("event", "")
                    if event_name == "ping":
                        continue

                    yield DifyStreamEvent(
                        event=event_name,
                        task_id=data.get("task_id"),
                        workflow_run_id=data.get("workflow_run_id"),
                        data=data.get("data"),
                    )


def extract_text_chunk(event: DifyStreamEvent) -> str | None:
    if event.event != "text_chunk":
        return None
    data = event.data
    if isinstance(data, dict):
        text = data.get("text")
        if isinstance(text, str):
            return text
        nested = data.get("outputs")
        if isinstance(nested, dict):
            for value in nested.values():
                if isinstance(value, str):
                    return value
    return None


def _extract_outputs(outputs: Any) -> str | None:
    if not isinstance(outputs, dict):
        return None
    for key in ("text", "result", "answer", "output"):
        value = outputs.get(key)
        if isinstance(value, str) and value.strip():
            return value
    for value in outputs.values():
        if isinstance(value, str) and value.strip():
            return value
    return None


def parse_workflow_finished(event: DifyStreamEvent) -> WorkflowFinishedResult | None:
    """Parse workflow_finished without raising; failures are returned in the result."""
    if event.event != "workflow_finished":
        return None
    data = event.data
    if not isinstance(data, dict):
        return WorkflowFinishedResult(success=False, error="invalid workflow_finished payload")

    status = data.get("status")
    error = data.get("error") if isinstance(data.get("error"), str) else None
    output = _extract_outputs(data.get("outputs"))

    if output:
        return WorkflowFinishedResult(success=True, output=output)

    if status == "failed":
        return WorkflowFinishedResult(success=False, error=error or "workflow failed")

    if status == "succeeded":
        return WorkflowFinishedResult(success=True, output="")

    return WorkflowFinishedResult(success=False, error=error)


def extract_final_output(event: DifyStreamEvent) -> str | None:
    result = parse_workflow_finished(event)
    if result is None:
        return None
    return result.output if result.success else None


def extract_error_message(event: DifyStreamEvent) -> str | None:
    if event.event != "error":
        return None
    data = event.data
    if isinstance(data, dict):
        for key in ("message", "error", "detail"):
            value = data.get(key)
            if isinstance(value, str) and value:
                return value
    if isinstance(data, str):
        return data
    return "unknown error"


def is_human_input_event(event: DifyStreamEvent) -> bool:
    return event.event in {"workflow_paused", "human_input_required"}
