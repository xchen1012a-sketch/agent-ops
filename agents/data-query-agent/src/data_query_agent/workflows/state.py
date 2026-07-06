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
    intent_confidence: Literal["high", "low"]
    response_tier: Literal["in_scope", "anchor_light", "redirect_firm", "refuse_adversarial"]
    offtopic_streak: int
    refusal_reason: str
    schema_context: str
    generated_sql: str
    fixture_case_id: str
    policy_allowed: bool
    policy_error_code: str
    query_result: dict[str, Any]
    answer: str
    chart: object
    followups: object
    llm_output: dict[str, Any]
    node_trace: list[NodeTrace]
