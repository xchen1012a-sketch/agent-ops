"""Unit tests for deterministic data-query workflow graph."""

from __future__ import annotations

from data_query_agent.workflows.graph import create_data_query_graph
from data_query_agent.workflows.nodes import (
    input_validation_node,
    intent_classify_node,
    query_execute_node,
    schema_retrieval_node,
    sql_generate_node,
    sql_policy_check_node,
)
from data_query_agent.workflows.state import DataQueryState


def test_non_data_question_routes_to_polite_refusal() -> None:
    graph = create_data_query_graph()

    result = graph.invoke({"question": "Write a poem for me"})

    assert result["intent"] == "non_data"
    assert result["answer"] == (
        "I can only answer data questions about orders, sales, refunds, and business metrics."
    )
    assert [trace["node_name"] for trace in result["node_trace"]] == [
        "input_validation",
        "intent_classify",
        "polite_refusal",
    ]


def test_data_question_runs_deterministic_main_path_without_llm_or_db() -> None:
    graph = create_data_query_graph()

    result = graph.invoke({"question": "What are total sales this month?"})

    assert result["intent"] == "data_query"
    assert result["schema_context"] == "wide_order_details, wide_orders"
    assert (
        result["generated_sql"]
        == "SELECT SUM(total_amount) AS total_sales FROM wide_orders LIMIT 100"
    )
    assert result["policy_allowed"] is True
    assert result["query_result"] == {"columns": ["total_sales"], "rows": [[98765.43]]}
    assert result["answer"] == "Query result is 98765.43."
    assert [trace["node_name"] for trace in result["node_trace"]] == [
        "input_validation",
        "intent_classify",
        "schema_retrieval",
        "sql_generate",
        "sql_policy_check",
        "query_execute",
        "result_validate",
        "interpret",
        "persist_audit",
    ]
    assert all(trace["status"] == "completed" for trace in result["node_trace"])


def test_refund_question_uses_refund_deterministic_sql() -> None:
    graph = create_data_query_graph()

    result = graph.invoke({"question": "What is the refund amount?"})

    assert result["generated_sql"] == (
        "SELECT SUM(refund_amount) AS refund_amount "
        "FROM wide_orders WHERE is_refunded = 1 LIMIT 100"
    )
    assert result["query_result"] == {"columns": ["refund_amount"], "rows": [[1234.5]]}


def test_policy_block_skips_query_execution_node() -> None:
    state: DataQueryState = {"question": "sales amount"}
    state = input_validation_node(state)
    state = intent_classify_node(state)
    state = schema_retrieval_node(state)
    state = sql_generate_node(state)
    state["generated_sql"] = "SELECT password FROM wide_orders LIMIT 10"

    checked = sql_policy_check_node(state)
    executed = query_execute_node(checked)

    assert checked["policy_allowed"] is False
    assert checked["policy_error_code"] == "column_not_allowed"
    assert "query_result" not in executed
    assert executed["node_trace"][-1] == {"node_name": "query_execute", "status": "skipped"}
