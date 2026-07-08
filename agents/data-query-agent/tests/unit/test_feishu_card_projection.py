"""Unit tests for mock Feishu card projection."""

from __future__ import annotations

from data_query_agent.infrastructure.integrations.feishu_cards import FeishuCardProjectionService


def test_text_answer_projects_to_text_card_with_followup_buttons() -> None:
    card = FeishuCardProjectionService().project(
        answer="结论：销售额为 123。",
        followups=("按地区拆分", "看趋势", "对比上期", "看渠道"),
    )

    assert card.card_type == "text"
    assert card.title == "问数结果"
    assert card.elements == ({"type": "markdown", "content": "结论：销售额为 123。"},)
    assert [action["text"] for action in card.actions] == ["按地区拆分", "看趋势", "对比上期"]
    assert card.truncated is False


def test_table_result_projects_to_truncated_table_card() -> None:
    card = FeishuCardProjectionService().project(
        answer="结论：app 渠道销售额最高。",
        query_result={
            "columns": ["channel", "total_sales"],
            "rows": [[f"c{index}", index] for index in range(1, 8)],
        },
        followups=("查看排名前 10",),
    )

    assert card.card_type == "table"
    assert card.title == "问数结果"
    assert card.elements[1]["type"] == "table"
    assert card.elements[1]["columns"] == ("channel", "total_sales")
    assert len(card.elements[1]["rows"]) == 5
    assert card.truncated is True
    assert card.actions == ({"type": "button", "text": "查看排名前 10"},)


def test_chart_semantics_projects_to_chart_card() -> None:
    chart = {
        "type": "line",
        "dataset": {"month": [1, 2], "total_sales": [100, 120]},
        "encoding": {"x": "month", "y": "total_sales"},
    }

    card = FeishuCardProjectionService().project(
        answer="结论：销售额呈上升趋势。",
        query_result={"columns": ["month", "total_sales"], "rows": [[1, 100], [2, 120]]},
        chart=chart,
        followups=("查看同比变化",),
    )

    assert card.card_type == "chart"
    assert card.title == "问数结果"
    assert card.elements[0] == {"type": "markdown", "content": "结论：销售额呈上升趋势。"}
    assert card.elements[1] == {"type": "chart", "chart": chart}
    assert card.truncated is False
