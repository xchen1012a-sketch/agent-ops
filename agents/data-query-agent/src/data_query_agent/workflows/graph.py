"""LangGraph factory for deterministic data-query workflow."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from data_query_agent.workflows.nodes import (
    input_validation_node,
    intent_classify_node,
    interpret_node,
    persist_audit_node,
    polite_refusal_node,
    query_execute_node,
    result_validate_node,
    route_after_intent,
    schema_retrieval_node,
    sql_generate_node,
    sql_policy_check_node,
)
from data_query_agent.workflows.state import DataQueryState


def create_data_query_graph() -> object:
    """Create a compiled deterministic data-query graph."""
    graph = StateGraph(DataQueryState)
    graph.add_node("input_validation", input_validation_node)
    graph.add_node("intent_classify", intent_classify_node)
    graph.add_node("schema_retrieval", schema_retrieval_node)
    graph.add_node("sql_generate", sql_generate_node)
    graph.add_node("sql_policy_check", sql_policy_check_node)
    graph.add_node("query_execute", query_execute_node)
    graph.add_node("result_validate", result_validate_node)
    graph.add_node("interpret", interpret_node)
    graph.add_node("persist_audit", persist_audit_node)
    graph.add_node("polite_refusal", polite_refusal_node)

    graph.set_entry_point("input_validation")
    graph.add_edge("input_validation", "intent_classify")
    graph.add_conditional_edges(
        "intent_classify",
        route_after_intent,
        {
            "schema_retrieval": "schema_retrieval",
            "polite_refusal": "polite_refusal",
        },
    )
    graph.add_edge("schema_retrieval", "sql_generate")
    graph.add_edge("sql_generate", "sql_policy_check")
    graph.add_edge("sql_policy_check", "query_execute")
    graph.add_edge("query_execute", "result_validate")
    graph.add_edge("result_validate", "interpret")
    graph.add_edge("interpret", "persist_audit")
    graph.add_edge("persist_audit", END)
    graph.add_edge("polite_refusal", END)
    return graph.compile()
