"""Deterministic data-query workflow nodes."""

from __future__ import annotations

from typing import Any, Literal

from data_query_agent.application.services.data_catalog_service import DataCatalogService
from data_query_agent.application.services.result_projection_service import ResultProjectionService
from data_query_agent.domain.policies.sql_ast import SqlAstPolicyValidator
from data_query_agent.workflows.state import DataQueryState, NodeTrace

_DATA_KEYWORDS = (
    "sales",
    "order",
    "orders",
    "amount",
    "refund",
    "margin",
    "customer",
    "region",
    "trend",
)


def input_validation_node(state: DataQueryState) -> DataQueryState:
    """Normalize and validate the incoming question."""
    question = state.get("question", "").strip()
    next_state: DataQueryState = {**state, "question": question}
    return _with_trace(next_state, "input_validation", "completed")


def intent_classify_node(state: DataQueryState) -> DataQueryState:
    """Classify whether the question is a data query."""
    question = state.get("question", "")
    intent: Literal["data_query", "non_data"] = (
        "data_query" if _is_data_question(question) else "non_data"
    )
    next_state: DataQueryState = {**state, "intent": intent}
    if intent == "non_data":
        next_state["refusal_reason"] = "question is outside data-query scope"
    return _with_trace(next_state, "intent_classify", "completed")


def schema_retrieval_node(state: DataQueryState) -> DataQueryState:
    """Attach deterministic schema context from versioned catalog sources."""
    catalog = DataCatalogService().load_schema_catalog()
    table_names = ", ".join(sorted(catalog.table_names()))
    next_state: DataQueryState = {**state, "schema_context": table_names}
    return _with_trace(next_state, "schema_retrieval", "completed")


def sql_generate_node(state: DataQueryState) -> DataQueryState:
    """Generate deterministic SQL without calling an LLM."""
    question = state.get("question", "").lower()
    if "refund" in question:
        sql = (
            "SELECT SUM(refund_amount) AS refund_amount "
            "FROM wide_orders WHERE is_refunded = 1 LIMIT 100"
        )
    else:
        sql = "SELECT SUM(total_amount) AS total_sales FROM wide_orders LIMIT 100"
    next_state: DataQueryState = {**state, "generated_sql": sql}
    return _with_trace(next_state, "sql_generate", "completed")


def sql_policy_check_node(state: DataQueryState) -> DataQueryState:
    """Validate generated SQL against AST and whitelist policy."""
    whitelist = DataCatalogService().load_sql_whitelist()
    result = SqlAstPolicyValidator(whitelist=whitelist).validate(state.get("generated_sql", ""))
    next_state: DataQueryState = {**state, "policy_allowed": result.is_allowed}
    if not result.is_allowed and result.first_violation is not None:
        next_state["policy_error_code"] = result.first_violation.code.value
    return _with_trace(next_state, "sql_policy_check", "completed")


def query_execute_node(state: DataQueryState) -> DataQueryState:
    """Return a deterministic fake query result without opening a database connection."""
    if not state.get("policy_allowed", False):
        return _with_trace(state, "query_execute", "skipped")
    sql = state.get("generated_sql", "")
    if "refund_amount" in sql:
        result: dict[str, Any] = {"columns": ["refund_amount"], "rows": [[1234.5]]}
    else:
        result = {"columns": ["total_sales"], "rows": [[98765.43]]}
    next_state: DataQueryState = {**state, "query_result": result}
    return _with_trace(next_state, "query_execute", "completed")


def result_validate_node(state: DataQueryState) -> DataQueryState:
    """Validate deterministic result presence for the main path."""
    if "query_result" not in state:
        return _with_trace(state, "result_validate", "skipped")
    return _with_trace(state, "result_validate", "completed")


def interpret_node(state: DataQueryState) -> DataQueryState:
    """Produce deterministic interpretation with chart and follow-up semantics."""
    result = state.get("query_result", {})
    rows = result.get("rows", []) if isinstance(result, dict) else []
    value = rows[0][0] if rows else None
    answer = f"Query result is {value}." if value is not None else "No result found."
    projection = (
        ResultProjectionService().project(
            question=state.get("question", ""),
            query_result=result,
        )
        if isinstance(result, dict)
        else None
    )
    next_state: DataQueryState = {**state, "answer": answer}
    if projection is not None:
        if projection.chart is not None:
            next_state["chart"] = {
                "type": projection.chart.type,
                "dataset": projection.chart.dataset,
                "encoding": projection.chart.encoding,
            }
        next_state["followups"] = list(projection.followups)
    return _with_trace(next_state, "interpret", "completed")


def persist_audit_node(state: DataQueryState) -> DataQueryState:
    """Mark audit persistence boundary without touching a database."""
    return _with_trace(state, "persist_audit", "completed")


def polite_refusal_node(state: DataQueryState) -> DataQueryState:
    """Return a polite refusal for non-data questions."""
    next_state: DataQueryState = {
        **state,
        "answer": "I can only answer data questions about orders, sales, refunds, and business metrics.",
    }
    return _with_trace(next_state, "polite_refusal", "completed")


def route_after_intent(state: DataQueryState) -> str:
    """Route non-data questions to refusal and data questions to the main path."""
    return "polite_refusal" if state.get("intent") == "non_data" else "schema_retrieval"


def _is_data_question(question: str) -> bool:
    normalized = question.lower()
    return any(keyword in normalized for keyword in _DATA_KEYWORDS)


def _with_trace(
    state: DataQueryState,
    node_name: str,
    status: Literal["started", "completed", "failed", "skipped"],
) -> DataQueryState:
    trace = list(state.get("node_trace", []))
    trace.append(NodeTrace(node_name=node_name, status=status))
    return {**state, "node_trace": trace}
