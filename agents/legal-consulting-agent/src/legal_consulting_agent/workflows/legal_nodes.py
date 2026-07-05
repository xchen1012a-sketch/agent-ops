"""Pure LEGAL-140 workflow nodes with external services behind mock boundaries."""

from __future__ import annotations

import re

from legal_consulting_agent.workflows.legal_state import (
    Citation,
    LegalEntityHints,
    LegalWorkflowState,
    LegalWorkflowUpdate,
    RetrievalChunk,
)

NON_LEGAL_MESSAGE = "非法律问题，请提供与法律相关的咨询。"
NO_SOURCE_DISCLAIMER = "本回答未在知识库中找到对应依据，仅供参考。"
PROMPT_INJECTION_PATTERNS = (
    "ignore previous instructions",
    "output secrets",
    "system prompt",
    "泄露密钥",
    "输出密钥",
)
HIGH_RISK_KEYWORDS = ("自杀", "轻生", "人身安全", "家暴", "紧急")
STATUTE_PATTERN = re.compile(r"第[一二三四五六七八九十百零\d]+条")


def _trace(state: LegalWorkflowState, node_name: str) -> list[str]:
    return [*state.get("node_trace", []), node_name]


def input_safety_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
    """Normalize user input and block prompt-injection style instructions."""

    question = state["question"].strip()
    lowered = question.lower()
    blocked = not question or any(pattern in lowered for pattern in PROMPT_INJECTION_PATTERNS)
    if blocked:
        return {
            "safe_question": None,
            "is_safe": False,
            "error_code": "INPUT_BLOCKED",
            "node_trace": _trace(state, "input_safety"),
        }
    return {
        "safe_question": question,
        "is_safe": True,
        "error_code": None,
        "node_trace": _trace(state, "input_safety"),
    }


def classification_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
    """Classify a safe legal question without calling an LLM in the first slice."""

    if not state.get("is_safe", False):
        return {"node_trace": _trace(state, "classification")}

    question = state.get("safe_question") or ""
    category = "other"
    intent = "识别为非法律或无法归类的问题"
    if any(keyword in question for keyword in ("劳动", "合同", "公司", "调岗", "辞退")):
        category = "civil_labor"
        intent = "询问劳动合同或用工争议"
    elif any(keyword in question for keyword in ("离婚", "抚养", "婚姻")):
        category = "family"
        intent = "询问婚姻家庭争议"
    elif any(keyword in question for keyword in ("犯罪", "刑事", "拘留")):
        category = "criminal"
        intent = "询问刑事法律风险"
    elif any(keyword in question for keyword in ("起诉", "官司", "赔偿")):
        category = "contract"
        intent = "询问争议解决路径"

    entities: LegalEntityHints = {
        "statute_numbers": STATUTE_PATTERN.findall(question),
        "statute_names": [name for name in ("劳动合同法", "民法典") if name in question],
        "case_keywords": [word for word in ("调岗", "离婚", "赔偿", "合同") if word in question],
    }
    return {
        "category": category,
        "intent": intent,
        "legal_entities": entities,
        "node_trace": _trace(state, "classification"),
    }


def context_build_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
    """Build a deterministic context window for the mock workflow boundary."""

    existing_context = state.get("context_messages", [])
    return {
        "context_messages": existing_context[-6:],
        "node_trace": _trace(state, "context_build"),
    }


def retrieval_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
    """Return adapter-provided chunks or an explicit no-source path.

    Real BGE/Qdrant retrieval is intentionally not called in this slice. Later
    slices can replace ``mock_chunks`` with an adapter result while preserving
    this node contract.
    """

    if state.get("error_code"):
        return {"node_trace": _trace(state, "retrieval")}
    chunks = state.get("mock_chunks", [])
    return {
        "chunks": chunks,
        "node_trace": _trace(state, "retrieval"),
    }


def _citation_from_chunk(chunk: RetrievalChunk) -> Citation:
    return {
        "source": chunk["source_name"],
        "section": chunk["source_section"],
        "snippet": chunk["snippet"],
    }


def generation_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
    """Generate a deterministic draft without calling DeepSeek."""

    if state.get("error_code"):
        return {"node_trace": _trace(state, "generation")}

    question = state.get("safe_question") or ""
    category = state.get("category")
    chunks = state.get("chunks", [])
    if category == "other":
        return {
            "answer_draft": NON_LEGAL_MESSAGE,
            "citations": [],
            "node_trace": _trace(state, "generation"),
        }
    if not chunks:
        return {
            "answer_draft": f"针对“{question}”，需要结合事实和适用法律进一步判断。{NO_SOURCE_DISCLAIMER}",
            "citations": [],
            "node_trace": _trace(state, "generation"),
        }

    first_chunk = chunks[0]
    citation = _citation_from_chunk(first_chunk)
    return {
        "answer_draft": (
            f"针对“{question}”，可先参考{citation['source']} {citation['section']}："
            f"{citation['snippet']} 本回答仅供参考，不构成正式法律意见。"
        ),
        "citations": [citation],
        "node_trace": _trace(state, "generation"),
    }


def citation_check_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
    """Ensure generated citations are backed by retrieved chunks."""

    if state.get("error_code"):
        return {"node_trace": _trace(state, "citation_check")}

    citations = state.get("citations", [])
    chunks = state.get("chunks", [])
    source_keys = {
        (chunk["source_name"], chunk["source_section"], chunk["snippet"]) for chunk in chunks
    }
    invalid = [
        citation
        for citation in citations
        if (citation["source"], citation["section"], citation["snippet"]) not in source_keys
    ]
    if invalid:
        return {
            "validated_answer": None,
            "error_code": "CITATION_INVALID",
            "node_trace": _trace(state, "citation_check"),
        }
    return {
        "validated_answer": state.get("answer_draft"),
        "node_trace": _trace(state, "citation_check"),
    }


def risk_check_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
    """Mark high-risk questions for later human-review queue integration."""

    if state.get("error_code"):
        return {"node_trace": _trace(state, "risk_check")}

    text = f"{state.get('safe_question') or ''} {state.get('validated_answer') or ''}"
    high_risk = any(keyword in text for keyword in HIGH_RISK_KEYWORDS)
    return {
        "high_risk": high_risk,
        "risk_reason": "personal_safety" if high_risk else None,
        "node_trace": _trace(state, "risk_check"),
    }


def persist_node(state: LegalWorkflowState) -> LegalWorkflowUpdate:
    """Expose the persistence boundary without writing to the database yet."""

    if state.get("error_code"):
        return {"node_trace": _trace(state, "persist")}
    if state.get("simulate_db_unavailable", False):
        return {
            "message_id": None,
            "error_code": "DB_UNAVAILABLE",
            "node_trace": _trace(state, "persist"),
        }
    return {
        "message_id": state.get("message_id"),
        "node_trace": _trace(state, "persist"),
    }
