"""Prompt-backed resume parsing service with injectable LLM adapter."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol, cast

from recruitment_assistant_agent.domain.entities.recruit_data import PromptVersion
from recruitment_assistant_agent.prompts import (
    PromptOutputValidationError,
    PromptOutputValidator,
    PromptTemplateLoader,
)
from recruitment_assistant_agent.prompts.policy import with_system_policy
from recruitment_assistant_agent.workflows.recruitment_nodes import SENSITIVE_ATTRIBUTE_FIELDS
from recruitment_assistant_agent.workflows.recruitment_state import (
    EducationEvidenceHint,
    ExperienceEvidenceHint,
    RecruitmentWorkflowState,
    RecruitmentWorkflowUpdate,
    ResumeStructuredPayload,
    SkillEvidenceHint,
)

SENSITIVE_TEXT_MARKERS = frozenset(
    {
        "female",
        "male",
        "gender",
        "married",
        "unmarried",
        "ethnicity",
        "religion",
        "hometown",
        "hukou",
        "id card",
        "years old",
    }
)


class TextLLMAdapter(Protocol):
    """Minimal text completion adapter contract for mock and real LLMs."""

    def complete(self, prompt: str) -> str:
        """Return raw model text for a rendered prompt."""


@dataclass(frozen=True, slots=True)
class ResumeParseResult:
    """Structured resume parse result used by workflow state."""

    resume_structure: ResumeStructuredPayload


class ResumeParsePromptService:
    """Parse resume text through prompt rendering and output validation."""

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

    def parse(self, resume_text: str) -> ResumeParseResult:
        """Render resume prompt, call adapter, and validate structured output."""

        rendered = self._template_loader.render(
            template_key=self._prompt.template_key,
            variables=self._prompt.variables or {},
            values={"resume_text": resume_text},
        )
        raw_output = self._llm_adapter.complete(with_system_policy(rendered.rendered_text))
        validated = self._output_validator.validate_json(raw_output)
        if _contains_sensitive_text(validated.value.values()):
            raise PromptOutputValidationError("resume parse output contains sensitive text")
        return ResumeParseResult(resume_structure=_resume_structure(validated.value))


def make_prompt_resume_parse_node(
    service: ResumeParsePromptService,
) -> Callable[[RecruitmentWorkflowState], RecruitmentWorkflowUpdate]:
    """Build a workflow node that consumes the prompt-backed resume parser."""

    def prompt_resume_parse_node(state: RecruitmentWorkflowState) -> RecruitmentWorkflowUpdate:
        node_trace = [*state.get("node_trace", []), "resume_parse"]
        if state.get("error_code"):
            return {"node_trace": node_trace}
        try:
            result = service.parse(state.get("mock_resume_text", ""))
        except Exception:
            return {
                "task_status": "failed",
                "persisted": False,
                "error_code": "PARSE_FAILED",
                "node_trace": node_trace,
            }
        return {
            "resume_structure": result.resume_structure,
            "node_trace": node_trace,
        }

    return prompt_resume_parse_node


def _contains_sensitive_text(values: Iterable[object]) -> bool:
    for value in values:
        if isinstance(value, str):
            lowered = value.lower()
            if any(marker in lowered for marker in SENSITIVE_TEXT_MARKERS):
                return True
        elif isinstance(value, Mapping):
            if _contains_sensitive_text(value.values()):
                return True
        elif isinstance(value, list) and _contains_sensitive_text(value):
            return True
    return False


def _resume_structure(value: Mapping[str, object]) -> ResumeStructuredPayload:
    clean_value = {
        key: item for key, item in value.items() if key not in SENSITIVE_ATTRIBUTE_FIELDS
    }
    return {
        "summary": cast(str | None, clean_value.get("summary")),
        "total_years_exp": _float_or_none(clean_value.get("total_years_exp")),
        "skills": _skill_hints(clean_value.get("skills")),
        "experiences": _experience_hints(clean_value.get("experiences")),
        "educations": _education_hints(clean_value.get("educations")),
        "soft_skills": _string_list(clean_value.get("soft_skills")),
    }


def _float_or_none(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _string_or_none(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _skill_hints(value: object) -> list[SkillEvidenceHint]:
    if not isinstance(value, list):
        return []
    skills: list[SkillEvidenceHint] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        skill_name = item.get("skill_name")
        evidence_snippet = item.get("evidence_snippet")
        if not isinstance(skill_name, str) or not isinstance(evidence_snippet, str):
            continue
        skills.append(
            {
                "skill_name": skill_name,
                "evidence_snippet": evidence_snippet,
                "source_section": _string_or_none(item.get("source_section")),
                "proficiency": _string_or_none(item.get("proficiency")),
            }
        )
    return skills


def _experience_hints(value: object) -> list[ExperienceEvidenceHint]:
    if not isinstance(value, list):
        return []
    experiences: list[ExperienceEvidenceHint] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        role_title = item.get("role_title")
        evidence_snippet = item.get("evidence_snippet")
        if not isinstance(role_title, str) or not isinstance(evidence_snippet, str):
            continue
        experiences.append(
            {
                "role_title": role_title,
                "evidence_snippet": evidence_snippet,
                "company_redacted": _string_or_none(item.get("company_redacted")),
                "duration_months": _int_or_none(item.get("duration_months")),
            }
        )
    return experiences


def _education_hints(value: object) -> list[EducationEvidenceHint]:
    if not isinstance(value, list):
        return []
    educations: list[EducationEvidenceHint] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        evidence_snippet = item.get("evidence_snippet")
        if not isinstance(evidence_snippet, str):
            continue
        educations.append(
            {
                "evidence_snippet": evidence_snippet,
                "degree": _string_or_none(item.get("degree")),
                "major": _string_or_none(item.get("major")),
                "school_tier": _string_or_none(item.get("school_tier")),
                "graduation_year": _int_or_none(item.get("graduation_year")),
            }
        )
    return educations
