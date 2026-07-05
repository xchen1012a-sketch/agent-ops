"""Mock Feishu card projection for data-query results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

MAX_TABLE_ROWS = 5


@dataclass(frozen=True, slots=True)
class FeishuCardProjection:
    """Frontend-independent Feishu card payload projection."""

    card_type: Literal["text", "table", "chart"]
    title: str
    elements: tuple[dict[str, Any], ...]
    actions: tuple[dict[str, str], ...]
    truncated: bool = False


class FeishuCardProjectionService:
    """Convert answer/result/chart semantics to mock Feishu card structures."""

    def project(
        self,
        *,
        answer: str,
        query_result: dict[str, Any] | None = None,
        chart: dict[str, Any] | None = None,
        followups: tuple[str, ...] = (),
    ) -> FeishuCardProjection:
        """Create a Feishu-safe card projection without calling Feishu APIs."""
        actions = tuple({"type": "button", "text": text} for text in followups[:3])
        if chart is not None:
            return FeishuCardProjection(
                card_type="chart",
                title="??????",
                elements=(
                    {"type": "markdown", "content": answer},
                    {"type": "chart", "chart": chart},
                ),
                actions=actions,
            )
        columns = _columns(query_result)
        rows = _rows(query_result)
        if columns and rows:
            visible_rows = rows[:MAX_TABLE_ROWS]
            return FeishuCardProjection(
                card_type="table",
                title="??????",
                elements=(
                    {"type": "markdown", "content": answer},
                    {"type": "table", "columns": columns, "rows": visible_rows},
                ),
                actions=actions,
                truncated=len(rows) > MAX_TABLE_ROWS,
            )
        return FeishuCardProjection(
            card_type="text",
            title="??????",
            elements=({"type": "markdown", "content": answer},),
            actions=actions,
        )


def _columns(query_result: dict[str, Any] | None) -> tuple[str, ...]:
    if query_result is None:
        return ()
    value = query_result.get("columns")
    if not isinstance(value, list):
        return ()
    return tuple(column for column in value if isinstance(column, str) and column)


def _rows(query_result: dict[str, Any] | None) -> tuple[tuple[Any, ...], ...]:
    if query_result is None:
        return ()
    value = query_result.get("rows")
    if not isinstance(value, list):
        return ()
    rows: list[tuple[Any, ...]] = []
    for row in value:
        if isinstance(row, list):
            rows.append(tuple(row))
    return tuple(rows)
