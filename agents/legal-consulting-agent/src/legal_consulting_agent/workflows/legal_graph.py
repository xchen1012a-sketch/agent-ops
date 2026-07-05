"""LangGraph factory for the legal consultation workflow."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from legal_consulting_agent.workflows.legal_nodes import (
    citation_check_node,
    classification_node,
    context_build_node,
    generation_node,
    input_safety_node,
    persist_node,
    retrieval_node,
    risk_check_node,
)
from legal_consulting_agent.workflows.legal_state import LegalWorkflowState


def build_legal_workflow_graph() -> object:
    """Build the LEGAL-140 graph with deterministic first-slice nodes."""

    graph = StateGraph(LegalWorkflowState)
    graph.add_node("input_safety", input_safety_node)
    graph.add_node("classification", classification_node)
    graph.add_node("context_build", context_build_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("generation", generation_node)
    graph.add_node("citation_check", citation_check_node)
    graph.add_node("risk_check", risk_check_node)
    graph.add_node("persist", persist_node)

    graph.set_entry_point("input_safety")
    graph.add_edge("input_safety", "classification")
    graph.add_edge("classification", "context_build")
    graph.add_edge("context_build", "retrieval")
    graph.add_edge("retrieval", "generation")
    graph.add_edge("generation", "citation_check")
    graph.add_edge("citation_check", "risk_check")
    graph.add_edge("risk_check", "persist")
    graph.add_edge("persist", END)
    return graph.compile()
