"""LangGraph factory for the recruitment analysis workflow."""

from __future__ import annotations

from collections.abc import Callable

from langgraph.graph import END, StateGraph

from recruitment_assistant_agent.workflows.recruitment_nodes import (
    evidence_match_node,
    fairness_check_node,
    file_safety_node,
    gap_question_gen_node,
    jd_parse_node,
    persist_node,
    resume_parse_node,
    task_route_node,
)
from recruitment_assistant_agent.workflows.recruitment_state import (
    RecruitmentWorkflowState,
    RecruitmentWorkflowUpdate,
)

WorkflowNode = Callable[[RecruitmentWorkflowState], RecruitmentWorkflowUpdate]


def _next_or_end(next_node: str) -> Callable[[RecruitmentWorkflowState], str]:
    def route(state: RecruitmentWorkflowState) -> str:
        if state.get("error_code"):
            return END
        return next_node

    return route


def build_recruitment_workflow_graph(
    *,
    resume_parse_handler: WorkflowNode | None = None,
    jd_parse_handler: WorkflowNode | None = None,
    evidence_match_handler: WorkflowNode | None = None,
    fairness_check_handler: WorkflowNode | None = None,
    gap_question_gen_handler: WorkflowNode | None = None,
) -> object:
    """Build the RECRUIT-240 graph with deterministic first-slice nodes."""

    graph = StateGraph(RecruitmentWorkflowState)
    graph.add_node("file_safety", file_safety_node)
    graph.add_node("task_route", task_route_node)
    graph.add_node("resume_parse", resume_parse_handler or resume_parse_node)  # type: ignore[arg-type]
    graph.add_node("jd_parse", jd_parse_handler or jd_parse_node)  # type: ignore[arg-type]
    graph.add_node("evidence_match", evidence_match_handler or evidence_match_node)  # type: ignore[arg-type]
    graph.add_node("fairness_check", fairness_check_handler or fairness_check_node)  # type: ignore[arg-type]
    graph.add_node("gap_question_gen", gap_question_gen_handler or gap_question_gen_node)  # type: ignore[arg-type]
    graph.add_node("persist", persist_node)

    graph.set_entry_point("file_safety")
    graph.add_conditional_edges("file_safety", _next_or_end("task_route"))
    graph.add_conditional_edges("task_route", _next_or_end("resume_parse"))
    graph.add_conditional_edges("resume_parse", _next_or_end("jd_parse"))
    graph.add_conditional_edges("jd_parse", _next_or_end("evidence_match"))
    graph.add_conditional_edges("evidence_match", _next_or_end("fairness_check"))
    graph.add_conditional_edges("fairness_check", _next_or_end("gap_question_gen"))
    graph.add_conditional_edges("gap_question_gen", _next_or_end("persist"))
    graph.add_edge("persist", END)
    return graph.compile()
