"""Prompt-backed workflow services for recruitment matching nodes."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import cast

from recruitment_assistant_agent.application.services.resume_parse_prompt_service import (
    TextLLMAdapter,
)
from recruitment_assistant_agent.domain.entities.recruit_data import PromptVersion
from recruitment_assistant_agent.prompts import PromptOutputValidator, PromptTemplateLoader
from recruitment_assistant_agent.workflows.recruitment_nodes import SENSITIVE_ATTRIBUTE_FIELDS
from recruitment_assistant_agent.workflows.recruitment_state import (
    GapHint,
    InterviewQuestionHint,
    JDRequirementHint,
    JDStructuredPayload,
    MatchItemHint,
    RecruitmentWorkflowState,
    RecruitmentWorkflowUpdate,
)


@dataclass(frozen=True, slots=True)
class JDParseResult:
    jd_structure: JDStructuredPayload


@dataclass(frozen=True, slots=True)
class EvidenceMatchResult:
    match_items: list[MatchItemHint]
    overall_tier: str | None


@dataclass(frozen=True, slots=True)
class FairnessCheckResult:
    fairness_passed: bool
    violation_details: list[str]


@dataclass(frozen=True, slots=True)
class GapQuestionResult:
    gaps: list[GapHint]
    interview_questions: list[InterviewQuestionHint]


class _PromptServiceBase:
    def __init__(
        self,
        *,
        prompt: PromptVersion,
        template_loader: PromptTemplateLoader,
        output_validator: PromptOutputValidator,
        llm_adapter: TextLLMAdapter,
    ) -> None:
        self._prompt = prompt
        self._template_loader = template_loader
        self._output_validator = output_validator
        self._llm_adapter = llm_adapter

    def _complete(self, values: dict[str, object]) -> dict[str, object]:
        rendered = self._template_loader.render(
            template_key=self._prompt.template_key,
            variables=self._prompt.variables or {},
            values=values,
        )
        return self._output_validator.validate_json(
            self._llm_adapter.complete(rendered.rendered_text)
        ).value


class JDParsePromptService(_PromptServiceBase):
    def parse(self, jd_text: str) -> JDParseResult:
        data = self._complete({"jd_text": jd_text})
        return JDParseResult(jd_structure=_jd_structure(data))


class EvidenceMatchPromptService(_PromptServiceBase):
    def match(
        self,
        *,
        resume_structure: Mapping[str, object],
        jd_structure: Mapping[str, object],
    ) -> EvidenceMatchResult:
        data = self._complete(
            {
                "resume_structure": resume_structure,
                "jd_structure": jd_structure,
            }
        )
        match_items = _match_items(data.get("match_items"))
        return EvidenceMatchResult(
            match_items=match_items,
            overall_tier=_string_or_none(data.get("overall_tier")),
        )


class FairnessCheckPromptService(_PromptServiceBase):
    def check(
        self,
        *,
        resume_structure: Mapping[str, object],
        jd_structure: Mapping[str, object],
        match_items: Sequence[Mapping[str, object]],
    ) -> FairnessCheckResult:
        data = self._complete(
            {
                "resume_structure": resume_structure,
                "jd_structure": jd_structure,
                "match_items": list(match_items),
            }
        )
        fairness_passed = data.get("fairness_passed") is True
        return FairnessCheckResult(
            fairness_passed=fairness_passed,
            violation_details=_string_list(data.get("violation_details")),
        )


class GapQuestionPromptService(_PromptServiceBase):
    def generate(self, *, match_items: Sequence[Mapping[str, object]]) -> GapQuestionResult:
        data = self._complete({"match_items": list(match_items)})
        return GapQuestionResult(
            gaps=_gap_hints(data.get("gaps")),
            interview_questions=_interview_questions(data.get("interview_questions")),
        )


def make_prompt_jd_parse_node(
    service: JDParsePromptService,
) -> Callable[[RecruitmentWorkflowState], RecruitmentWorkflowUpdate]:
    def prompt_jd_parse_node(state: RecruitmentWorkflowState) -> RecruitmentWorkflowUpdate:
        node_trace = [*state.get("node_trace", []), "jd_parse"]
        if state.get("error_code"):
            return {"node_trace": node_trace}
        try:
            result = service.parse(state.get("mock_jd_text", ""))
        except Exception:
            return _failed_update("PARSE_FAILED", node_trace)
        return {
            "jd_structure": result.jd_structure,
            "task_status": "matching",
            "node_trace": node_trace,
        }

    return prompt_jd_parse_node


def make_prompt_evidence_match_node(
    service: EvidenceMatchPromptService,
) -> Callable[[RecruitmentWorkflowState], RecruitmentWorkflowUpdate]:
    def prompt_evidence_match_node(state: RecruitmentWorkflowState) -> RecruitmentWorkflowUpdate:
        node_trace = [*state.get("node_trace", []), "evidence_match"]
        if state.get("error_code"):
            return {"node_trace": node_trace}
        try:
            result = service.match(
                resume_structure=state.get("resume_structure", {}),
                jd_structure=state.get("jd_structure", {}),
            )
        except Exception:
            return _failed_update("PARSE_FAILED", node_trace)
        return {
            "match_items": result.match_items,
            "overall_tier": result.overall_tier,
            "node_trace": node_trace,
        }

    return prompt_evidence_match_node


def make_prompt_fairness_check_node(
    service: FairnessCheckPromptService,
) -> Callable[[RecruitmentWorkflowState], RecruitmentWorkflowUpdate]:
    def prompt_fairness_check_node(state: RecruitmentWorkflowState) -> RecruitmentWorkflowUpdate:
        node_trace = [*state.get("node_trace", []), "fairness_check"]
        if state.get("error_code"):
            return {"node_trace": node_trace}
        deterministic_violations = sorted(
            _find_sensitive_fields(
                {
                    "resume_structure": state.get("resume_structure", {}),
                    "jd_structure": state.get("jd_structure", {}),
                }
            )
        )
        if deterministic_violations:
            return _fairness_violation_update(deterministic_violations, node_trace)
        try:
            result = service.check(
                resume_structure=state.get("resume_structure", {}),
                jd_structure=state.get("jd_structure", {}),
                match_items=state.get("match_items", []),
            )
        except Exception:
            return _failed_update("PARSE_FAILED", node_trace)
        if not result.fairness_passed:
            return _fairness_violation_update(result.violation_details, node_trace)
        return {
            "fairness_passed": True,
            "fairness_violation_details": [],
            "node_trace": node_trace,
        }

    return prompt_fairness_check_node


def make_prompt_gap_question_node(
    service: GapQuestionPromptService,
) -> Callable[[RecruitmentWorkflowState], RecruitmentWorkflowUpdate]:
    def prompt_gap_question_node(state: RecruitmentWorkflowState) -> RecruitmentWorkflowUpdate:
        node_trace = [*state.get("node_trace", []), "gap_question_gen"]
        if state.get("error_code"):
            return {"node_trace": node_trace}
        try:
            result = service.generate(match_items=state.get("match_items", []))
        except Exception:
            return _failed_update("PARSE_FAILED", node_trace)
        return {
            "gaps": result.gaps,
            "interview_questions": result.interview_questions,
            "task_status": "ready_to_persist",
            "node_trace": node_trace,
        }

    return prompt_gap_question_node


def _failed_update(error_code: str, node_trace: list[str]) -> RecruitmentWorkflowUpdate:
    return {
        "task_status": "failed",
        "persisted": False,
        "error_code": error_code,
        "node_trace": node_trace,
    }


def _fairness_violation_update(
    violation_details: list[str],
    node_trace: list[str],
) -> RecruitmentWorkflowUpdate:
    return {
        "fairness_passed": False,
        "fairness_violation_details": violation_details,
        "task_status": "failed",
        "persisted": False,
        "error_code": "FAIRNESS_VIOLATION",
        "node_trace": node_trace,
    }


def _find_sensitive_fields(value: object) -> set[str]:
    if isinstance(value, Mapping):
        found = {key for key in value if key in SENSITIVE_ATTRIBUTE_FIELDS}
        for nested_value in value.values():
            found.update(_find_sensitive_fields(nested_value))
        return found
    if isinstance(value, list):
        list_found: set[str] = set()
        for item in value:
            list_found.update(_find_sensitive_fields(item))
        return list_found
    return set()


def _jd_structure(value: Mapping[str, object]) -> JDStructuredPayload:
    return {
        "job_title": _string_or_none(value.get("job_title")),
        "summary": _string_or_none(value.get("summary")),
        "requirements": _requirements(value.get("requirements")),
    }


def _requirements(value: object) -> list[JDRequirementHint]:
    if not isinstance(value, list):
        return []
    requirements: list[JDRequirementHint] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        requirement_type = item.get("requirement_type")
        text = item.get("text")
        if requirement_type not in {"must_have", "nice_to_have"} or not isinstance(text, str):
            continue
        requirements.append(
            {
                "requirement_type": cast(str, requirement_type),
                "text": text,
                "category": _string_or_none(item.get("category")),
                "weight_hint": _float_or_none(item.get("weight_hint")),
            }
        )
    return requirements


def _match_items(value: object) -> list[MatchItemHint]:
    if not isinstance(value, list):
        return []
    items: list[MatchItemHint] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        requirement = item.get("requirement")
        match_status = item.get("match_status")
        if match_status not in {"match", "partial", "no_evidence"} or not isinstance(
            requirement, str
        ):
            continue
        match_item: MatchItemHint = {
            "requirement": requirement,
            "match_status": cast(str, match_status),
            "skill_category": _string_or_none(item.get("skill_category")),
        }
        evidence = _string_or_none(item.get("evidence_snippet"))
        if evidence is not None and match_status != "no_evidence":
            match_item["evidence_snippet"] = evidence
        items.append(match_item)
    return items


def _gap_hints(value: object) -> list[GapHint]:
    if not isinstance(value, list):
        return []
    gaps: list[GapHint] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        gap_description = item.get("gap_description")
        if not isinstance(gap_description, str):
            continue
        gaps.append(
            {
                "gap_description": gap_description,
                "suggested_question": _string_or_none(item.get("suggested_question")),
            }
        )
    return gaps


def _interview_questions(value: object) -> list[InterviewQuestionHint]:
    if not isinstance(value, list):
        return []
    questions: list[InterviewQuestionHint] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        question_text = item.get("question_text")
        category = item.get("category")
        if not isinstance(question_text, str) or not isinstance(category, str):
            continue
        questions.append(
            {
                "question_text": question_text,
                "category": category,
                "difficulty": _string_or_none(item.get("difficulty")),
            }
        )
    return questions


def _string_or_none(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _float_or_none(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None
