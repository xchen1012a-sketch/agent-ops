"""State schema for the legal consultation workflow.

This module intentionally contains only typed state contracts. Nodes and
adapters must depend on this schema rather than passing unstructured dicts.
"""

from __future__ import annotations

from typing import Required, TypedDict


class LegalEntityHints(TypedDict, total=False):
    """Structured legal entity hints produced by classification."""

    statute_numbers: list[str]
    statute_names: list[str]
    case_keywords: list[str]


class RetrievalChunk(TypedDict, total=False):
    """A retrieval result that is safe to expose as a citation source."""

    snippet: Required[str]
    source_name: Required[str]
    source_section: Required[str]
    material_id: Required[int]
    dense_score: float
    sparse_score: float
    rerank_score: float


class Citation(TypedDict):
    """Citation format returned by the answer generation path."""

    source: str
    section: str
    snippet: str


class LegalWorkflowState(TypedDict, total=False):
    """LangGraph state for LEGAL-140.

    The first LEGAL-140 slice keeps external services behind mock boundaries:
    no DeepSeek, Qdrant, BGE, Redis, or database side effects are triggered by
    these fields alone.
    """

    thread_id: Required[str]
    user_id: Required[int]
    question: Required[str]
    prompt_version: Required[str]
    workflow_version: Required[str]

    safe_question: str | None
    is_safe: bool
    category: str | None
    intent: str | None
    legal_entities: LegalEntityHints
    response_tier: str | None
    offtopic_streak: int
    boundary_message: str | None
    context_messages: list[dict[str, str]]
    chunks: list[RetrievalChunk]
    answer_draft: str | None
    citations: list[Citation]
    validated_answer: str | None
    high_risk: bool
    risk_reason: str | None
    message_id: int | None
    error_code: str | None
    node_trace: list[str]

    # Test-only / adapter boundary inputs. Production callers should provide
    # these through explicit adapters in later slices, not from HTTP payloads.
    mock_chunks: list[RetrievalChunk]
    simulate_db_unavailable: bool


class LegalWorkflowUpdate(TypedDict, total=False):
    """Partial state update returned by a workflow node."""

    safe_question: str | None
    is_safe: bool
    category: str | None
    intent: str | None
    legal_entities: LegalEntityHints
    response_tier: str | None
    offtopic_streak: int
    boundary_message: str | None
    context_messages: list[dict[str, str]]
    chunks: list[RetrievalChunk]
    answer_draft: str | None
    citations: list[Citation]
    validated_answer: str | None
    high_risk: bool
    risk_reason: str | None
    message_id: int | None
    error_code: str | None
    node_trace: list[str]
