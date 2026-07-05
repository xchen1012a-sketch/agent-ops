"""State schema for deterministic data-query workflow slices."""

from __future__ import annotations

from typing import Any, Literal, TypedDict


class NodeTrace(TypedDict):
    """Minimal in-memory node trace emitted by deterministic workflow nodes."""

    node_name: str
    status: Literal["started", "completed", "failed", "skipped"]


class DataQueryState(TypedDict, total=False):
    """LangGraph state for data-query workflow execution."""

    question: str
    intent: Literal["data_query", "non_data"]
    refusal_reason: str
    schema_context: str
    generated_sql: str
    policy_allowed: bool
    policy_error_code: str
    query_result: dict[str, Any]
    answer: str
    chart: object
    followups: object
    llm_output: dict[str, Any]
    node_trace: list[NodeTrace]
