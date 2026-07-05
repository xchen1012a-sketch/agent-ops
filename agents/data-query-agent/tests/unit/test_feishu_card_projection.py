"""Unit tests for mock Feishu card projection."""

from __future__ import annotations

from data_query_agent.infrastructure.integrations.feishu_cards import FeishuCardProjectionService


def test_text_answer_projects_to_text_card_with_followup_buttons() -> None:
    card = FeishuCardProjectionService().project(
        answer="???? 123?",
        followups=("?????", "????", "????", "??"),
    )

    assert card.card_type == "text"
    assert card.elements == ({"type": "markdown", "content": "???? 123?"},)
    assert [action["text"] for action in card.actions] == ["?????", "????", "????"]
    assert card.truncated is False


def test_table_result_projects_to_truncated_table_card() -> None:
    card = FeishuCardProjectionService().project(
        answer="???????",
        query_result={
            "columns": ["channel", "total_sales"],
            "rows": [[f"c{index}", index] for index in range(1, 8)],
        },
        followups=("???????",),
    )

    assert card.card_type == "table"
    assert card.elements[1]["type"] == "table"
    assert card.elements[1]["columns"] == ("channel", "total_sales")
    assert len(card.elements[1]["rows"]) == 5
    assert card.truncated is True
    assert card.actions == ({"type": "button", "text": "???????"},)


def test_chart_semantics_projects_to_chart_card() -> None:
    chart = {
        "type": "line",
        "dataset": {"month": [1, 2], "total_sales": [100, 120]},
        "encoding": {"x": "month", "y": "total_sales"},
    }

    card = FeishuCardProjectionService().project(
        answer="?????",
        query_result={"columns": ["month", "total_sales"], "rows": [[1, 100], [2, 120]]},
        chart=chart,
        followups=("??????",),
    )

    assert card.card_type == "chart"
    assert card.elements[0] == {"type": "markdown", "content": "?????"}
    assert card.elements[1] == {"type": "chart", "chart": chart}
    assert card.truncated is False
