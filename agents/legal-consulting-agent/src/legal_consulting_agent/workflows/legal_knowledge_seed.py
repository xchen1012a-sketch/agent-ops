"""Minimal course-template knowledge seed for the legal MVP.

The seed is deliberately not a statute database. It provides demo-safe
consultation framing when no external retriever is configured, while making
the source status visible to callers and tests.
"""

from __future__ import annotations

from legal_consulting_agent.workflows.legal_state import RetrievalChunk

COURSE_TEMPLATE_SOURCE = "AI法律咨询系统课程模板知识包"
COURSE_TEMPLATE_SOURCE_STATUS = "来源状态：课程模板/待补充法规原文"

_KNOWLEDGE_BY_CATEGORY: dict[str, tuple[int, str, str]] = {
    "civil_labor": (
        -101,
        "劳动用工模板",
        "先确认劳动合同、工资记录、考勤、社保和沟通证据；区分拖欠工资、调岗、辞退、工伤等情形，再给出协商、投诉、仲裁或诉讼路径。",
    ),
    "contract": (
        -102,
        "合同与债务模板",
        "先核对合同主体、标的、付款、违约责任、履行证据和催告记录；再判断继续履行、解除、退款、赔偿或诉讼保全等路径。",
    ),
    "family": (
        -103,
        "婚姻家庭模板",
        "先确认婚姻关系、子女抚养、共同财产、债务、家暴或继承事实；涉及人身安全时优先保留证据并寻求紧急保护。",
    ),
    "criminal": (
        -104,
        "刑事风险模板",
        "先区分是否已被传唤、拘留、立案或取保，梳理涉案事实、证据和金额；刑事风险场景建议尽快联系执业律师。",
    ),
    "general": (
        -199,
        "通用咨询模板",
        "先补充时间、地点、主体、合同或证据、已沟通结果和当前诉求；在事实不完整时只给风险提示和下一步取证建议。",
    ),
}


def course_template_chunk_for_category(category: str | None) -> RetrievalChunk | None:
    """Return one transparent fallback chunk for an in-scope category."""

    if category == "other":
        return None
    material = _KNOWLEDGE_BY_CATEGORY.get(category or "general") or _KNOWLEDGE_BY_CATEGORY[
        "general"
    ]
    material_id, section, snippet = material
    return {
        "source_name": COURSE_TEMPLATE_SOURCE,
        "source_section": f"{section} · {COURSE_TEMPLATE_SOURCE_STATUS}",
        "snippet": snippet,
        "material_id": material_id,
        "dense_score": 0.0,
        "sparse_score": 0.0,
        "rerank_score": 0.0,
    }
