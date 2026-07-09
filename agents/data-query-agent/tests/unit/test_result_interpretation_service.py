"""Unit tests for business-language result interpretation."""

from __future__ import annotations

from data_query_agent.application.services.result_interpretation_service import (
    ResultInterpretationService,
)


def test_interprets_single_sales_metric_as_business_answer() -> None:
    answer = ResultInterpretationService().interpret(
        question="上个月的销售额是多少？",
        query_result={"columns": ["total_sales"], "rows": [[505845231.58]], "row_count": 1},
        followups=("按地区拆分看看", "查看最近 12 个月趋势"),
    )

    assert "上个月销售额" in answer
    assert "505,845,231.58 元" in answer
    assert "口径" in answer
    assert "按地区拆分看看" in answer


def test_interprets_dimension_metric_result_with_top_item() -> None:
    answer = ResultInterpretationService().interpret(
        question="各渠道销售额排行",
        query_result={
            "columns": ["channel", "total_sales"],
            "rows": [["app", 70000.0], ["web", 53456.78]],
            "row_count": 2,
        },
    )

    assert "按渠道看" in answer
    assert "app的销售额最高" in answer
    assert "70,000 元" in answer


def test_interprets_empty_result_without_placeholder() -> None:
    answer = ResultInterpretationService().interpret(
        question="上个月销售额",
        query_result={"columns": ["total_sales"], "rows": [], "row_count": 0},
    )

    assert "当前没有查到可用结果" in answer
    assert "查询结果已生成" not in answer
