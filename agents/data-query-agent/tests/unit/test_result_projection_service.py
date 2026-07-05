"""Unit tests for result chart and follow-up projection."""

from __future__ import annotations

from data_query_agent.application.services.result_projection_service import ResultProjectionService
from data_query_agent.workflows.nodes import interpret_node


def test_single_value_result_has_no_chart_but_has_followups() -> None:
    projection = ResultProjectionService().project(
        question="?????????",
        query_result={"columns": ["total_sales"], "rows": [[123456.78]]},
    )

    assert projection.chart is None
    assert projection.followups == (
        "???????",
        "???? 12 ????",
        "???????",
    )


def test_trend_result_returns_line_chart_semantics() -> None:
    projection = ResultProjectionService().project(
        question="??????????",
        query_result={
            "columns": ["month", "total_sales"],
            "rows": [[1, 10000.0], [2, 12000.0], [3, 15000.0]],
        },
    )

    assert projection.chart is not None
    assert projection.chart.type == "line"
    assert projection.chart.dataset == {
        "month": [1, 2, 3],
        "total_sales": [10000.0, 12000.0, 15000.0],
    }
    assert projection.chart.encoding == {"x": "month", "y": "total_sales"}
    assert "??" in projection.followups[1]


def test_ranking_result_returns_bar_chart_semantics() -> None:
    projection = ResultProjectionService().project(
        question="????????",
        query_result={
            "columns": ["channel", "total_sales"],
            "rows": [["app", 70000.0], ["web", 53456.78]],
        },
    )

    assert projection.chart is not None
    assert projection.chart.type == "bar"
    assert projection.chart.dataset == {
        "channel": ["app", "web"],
        "total_sales": [70000.0, 53456.78],
    }
    assert projection.chart.encoding == {"x": "channel", "y": "total_sales"}


def test_interpret_node_writes_chart_and_followups_to_state() -> None:
    state = interpret_node(
        {
            "question": "??????????",
            "query_result": {
                "columns": ["month", "total_sales"],
                "rows": [[1, 10000.0], [2, 12000.0]],
            },
        }
    )

    assert state["chart"] == {
        "type": "line",
        "dataset": {"month": [1, 2], "total_sales": [10000.0, 12000.0]},
        "encoding": {"x": "month", "y": "total_sales"},
    }
    assert state["followups"]
    assert state["node_trace"][-1] == {"node_name": "interpret", "status": "completed"}
