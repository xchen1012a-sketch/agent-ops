"""Project query results into chart semantics and follow-up questions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

TREND_DIMENSIONS = frozenset({"month", "period", "date", "day", "day_type"})


@dataclass(frozen=True, slots=True)
class ChartProjection:
    """Frontend-safe chart semantics compatible with ECharts-style rendering."""

    type: Literal["line", "bar"]
    dataset: dict[str, list[Any]]
    encoding: dict[str, str]


@dataclass(frozen=True, slots=True)
class ResultProjection:
    """Answer projection with optional chart and follow-up recommendations."""

    chart: ChartProjection | None
    followups: tuple[str, ...]


class ResultProjectionService:
    """Infer chart and follow-up semantics from structured query results."""

    def project(self, *, question: str, query_result: dict[str, Any]) -> ResultProjection:
        """Return chart semantics and follow-ups without exposing SQL details."""
        columns = _columns(query_result)
        rows = _rows(query_result)
        chart = _chart_for_result(columns=columns, rows=rows)
        return ResultProjection(
            chart=chart,
            followups=_followups_for_chart(question=question, chart=chart),
        )


def _chart_for_result(
    *, columns: tuple[str, ...], rows: tuple[tuple[Any, ...], ...]
) -> ChartProjection | None:
    if len(columns) < 2 or len(rows) < 2:
        return None
    dimension = columns[0]
    metric = columns[1]
    if not _looks_numeric_series(rows=rows, metric_index=1):
        return None
    chart_type: Literal["line", "bar"] = "line" if dimension in TREND_DIMENSIONS else "bar"
    return ChartProjection(
        type=chart_type,
        dataset={
            dimension: [row[0] for row in rows],
            metric: [row[1] for row in rows],
        },
        encoding={"x": dimension, "y": metric},
    )


def _followups_for_chart(*, question: str, chart: ChartProjection | None) -> tuple[str, ...]:
    normalized = question.lower()
    if chart is None:
        return (
            "???????",
            "???? 12 ????",
            "???????",
        )
    if chart.type == "line":
        return (
            "?????????",
            "?????????",
            "?????????",
        )
    if "refund" in normalized or "??" in question:
        return (
            "??????????",
            "?????????",
            "????????",
        )
    return (
        "??????????",
        "???????",
        "???????????",
    )


def _columns(query_result: dict[str, Any]) -> tuple[str, ...]:
    value = query_result.get("columns", ())
    if not isinstance(value, list):
        return ()
    return tuple(column for column in value if isinstance(column, str) and column)


def _rows(query_result: dict[str, Any]) -> tuple[tuple[Any, ...], ...]:
    value = query_result.get("rows", ())
    if not isinstance(value, list):
        return ()
    rows: list[tuple[Any, ...]] = []
    for row in value:
        if isinstance(row, list):
            rows.append(tuple(row))
    return tuple(rows)


def _looks_numeric_series(*, rows: tuple[tuple[Any, ...], ...], metric_index: int) -> bool:
    for row in rows:
        if len(row) <= metric_index or not isinstance(row[metric_index], int | float):
            return False
    return True
