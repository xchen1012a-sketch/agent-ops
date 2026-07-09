"""Business-language interpretation for structured data-query results."""

from __future__ import annotations

from typing import Any

_COLUMN_LABELS = {
    "total_sales": "销售额",
    "actual_amount": "实付金额",
    "total_amount": "订单金额",
    "refund_amount": "退款金额",
    "refund_rate": "退款率",
    "gross_margin": "毛利率",
    "gross_profit": "毛利",
    "profit": "利润",
    "order_count": "订单数",
    "customer_count": "客户数",
    "channel": "渠道",
    "region": "地区",
    "month": "月份",
    "date": "日期",
    "day": "日期",
    "day_type": "日期类型",
    "category": "品类",
    "brand": "品牌",
}

_CURRENCY_COLUMNS = frozenset(
    {
        "total_sales",
        "actual_amount",
        "total_amount",
        "refund_amount",
        "gross_profit",
        "profit",
        "cost",
    }
)
_RATE_COLUMNS = frozenset({"refund_rate", "gross_margin", "conversion", "retention", "churn"})
_COUNT_COLUMNS = frozenset({"order_count", "customer_count", "count"})
_TREND_COLUMNS = frozenset({"month", "date", "day", "period", "day_type"})


class ResultInterpretationService:
    """Turn validated query output into concise user-facing business language."""

    def interpret(
        self,
        *,
        question: str,
        query_result: dict[str, Any],
        followups: tuple[str, ...] = (),
    ) -> str:
        """Build a readable answer without exposing SQL or audit internals."""
        columns = _columns(query_result)
        rows = _rows(query_result)
        if not rows:
            return _empty_answer(followups)

        row_count = _row_count(query_result, rows)
        if len(columns) == 1 and len(rows) == 1:
            answer = _single_metric_answer(
                question=question,
                column=columns[0],
                value=rows[0][0] if rows[0] else None,
                row_count=row_count,
                followups=followups,
            )
        elif len(columns) >= 2:
            answer = _dimension_metric_answer(
                dimension=columns[0],
                metric=columns[1],
                rows=rows,
                row_count=row_count,
                followups=followups,
            )
        else:
            answer = _generic_answer(row_count=row_count, followups=followups)
        return answer


def _single_metric_answer(
    *,
    question: str,
    column: str,
    value: Any,
    row_count: int,
    followups: tuple[str, ...],
) -> str:
    metric = _label(column)
    period = _period_hint(question)
    formatted_value = _format_metric(column, value)
    lines = [
        f"结论：{period}{metric}为 **{formatted_value}**。",
        "",
        f"- 口径：按当前数据目录中的「{metric}」汇总，返回 {row_count} 行结果。",
    ]
    suggestion = _suggestion(followups)
    if suggestion:
        lines.append(f"- 建议：{suggestion}")
    return "\n".join(lines)


def _dimension_metric_answer(
    *,
    dimension: str,
    metric: str,
    rows: tuple[tuple[Any, ...], ...],
    row_count: int,
    followups: tuple[str, ...],
) -> str:
    dimension_label = _label(dimension)
    metric_label = _label(metric)
    numeric_rows = [row for row in rows if len(row) > 1 and isinstance(row[1], int | float)]

    if numeric_rows:
        top = max(numeric_rows, key=lambda row: float(row[1]))
        top_dimension = _format_dimension(top[0])
        top_value = _format_metric(metric, top[1])
        if dimension in _TREND_COLUMNS and len(numeric_rows) >= 2:
            first = numeric_rows[0]
            latest = numeric_rows[-1]
            conclusion = (
                f"结论：{metric_label}从 { _format_dimension(first[0]) } 的 "
                f"**{_format_metric(metric, first[1])}** 变化到 "
                f"{ _format_dimension(latest[0]) } 的 **{_format_metric(metric, latest[1])}**。"
            )
        else:
            conclusion = (
                f"结论：按{dimension_label}看，{top_dimension}的{metric_label}最高，"
                f"为 **{top_value}**。"
            )
    else:
        conclusion = f"结论：已按{dimension_label}整理出{metric_label}明细。"

    lines = [
        conclusion,
        "",
        f"- 口径：结果按「{dimension_label}」拆分「{metric_label}」，返回 {row_count} 行。",
    ]
    suggestion = _suggestion(followups)
    if suggestion:
        lines.append(f"- 建议：{suggestion}")
    return "\n".join(lines)


def _empty_answer(followups: tuple[str, ...]) -> str:
    lines = ["结论：当前没有查到可用结果。", "", "- 口径：查询已完成，但结果集为空。"]
    suggestion = _suggestion(followups)
    if suggestion:
        lines.append(f"- 建议：{suggestion}")
    return "\n".join(lines)


def _generic_answer(*, row_count: int, followups: tuple[str, ...]) -> str:
    lines = [
        f"结论：已查到 {row_count} 行结果，关键明细已整理在下方表格。",
        "",
        "- 口径：本次回答仅基于查询返回的数据，不额外推断未返回的指标。",
    ]
    suggestion = _suggestion(followups)
    if suggestion:
        lines.append(f"- 建议：{suggestion}")
    return "\n".join(lines)


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
        elif isinstance(row, tuple):
            rows.append(row)
    return tuple(rows)


def _row_count(query_result: dict[str, Any], rows: tuple[tuple[Any, ...], ...]) -> int:
    value = query_result.get("row_count")
    return value if isinstance(value, int) and value >= 0 else len(rows)


def _label(column: str) -> str:
    return _COLUMN_LABELS.get(column, column.replace("_", " "))


def _period_hint(question: str) -> str:
    for token in ("上个月", "本月", "这个月", "上周", "本周", "昨天", "今天", "今年", "去年"):
        if token in question:
            return token
    return "本次查询的"


def _format_metric(column: str, value: Any) -> str:
    if value is None:
        return "无数据"
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, int | float):
        if column in _RATE_COLUMNS:
            rate = value * 100 if -1 <= value <= 1 else value
            return f"{_format_number(rate)}%"
        unit = ""
        if column in _CURRENCY_COLUMNS:
            unit = " 元"
        elif column in _COUNT_COLUMNS:
            unit = ""
        return f"{_format_number(value)}{unit}"
    return str(value)


def _format_number(value: int | float) -> str:
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def _format_dimension(value: Any) -> str:
    if value is None:
        return "未分组"
    return str(value)


def _suggestion(followups: tuple[str, ...]) -> str:
    usable = [item.strip() for item in followups if item.strip()]
    if not usable:
        usable = ["按地区拆分看看", "查看最近 12 个月趋势", "对比上期变化"]
    return "可以继续问：" + "、".join(f"「{item}」" for item in usable[:3]) + "。"
