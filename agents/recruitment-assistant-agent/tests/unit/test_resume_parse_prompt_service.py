"""Unit tests for prompt-backed resume parsing."""

from __future__ import annotations

from pathlib import Path

from recruitment_assistant_agent.application.services.resume_parse_prompt_service import (
    ResumeParsePromptService,
    make_prompt_resume_parse_node,
)
from recruitment_assistant_agent.domain.entities.recruit_data import PromptVersion
from recruitment_assistant_agent.domain.value_objects.recruit_enums import PromptStatus
from recruitment_assistant_agent.prompts import PromptOutputValidator, PromptTemplateLoader
from recruitment_assistant_agent.workflows.recruitment_state import RecruitmentWorkflowState


class StubLLMAdapter:
    def __init__(self, raw_output: str) -> None:
        self.raw_output = raw_output
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.raw_output


class FailingLLMAdapter:
    def complete(self, prompt: str) -> str:
        raise TimeoutError("provider timeout with raw resume text")


def prompt_version() -> PromptVersion:
    return PromptVersion(
        public_id="prompt-public-1",
        prompt_name="recruit_resume_parse",
        version="v1",
        template_key="recruit_resume_parse/v1/template.txt",
        status=PromptStatus.ACTIVE,
        created_by=1,
        variables={"required": ["resume_text"]},
        output_schema={
            "type": "object",
            "required": [
                "summary",
                "total_years_exp",
                "skills",
                "experiences",
                "educations",
                "soft_skills",
            ],
            "properties": {
                "summary": {"type": "string"},
                "total_years_exp": {"type": "number"},
                "skills": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["skill_name", "evidence_snippet"],
                        "properties": {
                            "skill_name": {"type": "string"},
                            "evidence_snippet": {"type": "string"},
                            "source_section": {"type": "string"},
                            "proficiency": {"type": "string"},
                        },
                    },
                },
                "experiences": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["role_title", "evidence_snippet"],
                        "properties": {
                            "role_title": {"type": "string"},
                            "evidence_snippet": {"type": "string"},
                            "company_redacted": {"type": "string"},
                            "duration_months": {"type": "number"},
                        },
                    },
                },
                "educations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["evidence_snippet"],
                        "properties": {
                            "evidence_snippet": {"type": "string"},
                            "degree": {"type": "string"},
                            "major": {"type": "string"},
                            "school_tier": {"type": "string"},
                            "graduation_year": {"type": "number"},
                        },
                    },
                },
                "soft_skills": {"type": "array", "items": {"type": "string"}},
            },
        },
    )


def write_template(root: Path) -> None:
    path = root / "recruit_resume_parse/v1/template.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Resume: {resume_text}", encoding="utf-8")


def valid_raw_output() -> str:
    return """
    {
      "summary": "Python backend engineer.",
      "total_years_exp": 5,
      "skills": [{"skill_name": "Python", "evidence_snippet": "Built Python services.", "source_section": "skills", "proficiency": "advanced"}],
      "experiences": [{"role_title": "Backend Engineer", "evidence_snippet": "Built APIs.", "company_redacted": "Company A", "duration_months": 36}],
      "educations": [{"evidence_snippet": "BS Computer Science.", "degree": "BS", "major": "CS", "school_tier": "undergraduate", "graduation_year": 2018}],
      "soft_skills": ["communication"]
    }
    """


def sensitive_raw_output() -> str:
    return """
    {
      "summary": "Candidate is female and 28 years old.",
      "total_years_exp": 5,
      "skills": [{"skill_name": "Python", "evidence_snippet": "Built Python services.", "source_section": "skills", "proficiency": "advanced"}],
      "experiences": [],
      "educations": [],
      "soft_skills": ["communication"]
    }
    """


def test_service_renders_prompt_and_returns_resume_structure(tmp_path: Path) -> None:
    write_template(tmp_path)
    adapter = StubLLMAdapter(valid_raw_output())
    service = ResumeParsePromptService(
        prompt=prompt_version(),
        template_loader=PromptTemplateLoader(tmp_path),
        output_validator=PromptOutputValidator(prompt_version().output_schema or {}),
        llm_adapter=adapter,
    )

    result = service.parse("Built Python services.")

    assert adapter.prompts == ["Resume: Built Python services."]
    assert result.resume_structure["summary"] == "Python backend engineer."
    assert result.resume_structure["skills"][0]["skill_name"] == "Python"


def test_prompt_resume_parse_node_updates_state(tmp_path: Path) -> None:
    write_template(tmp_path)
    service = ResumeParsePromptService(
        prompt=prompt_version(),
        template_loader=PromptTemplateLoader(tmp_path),
        output_validator=PromptOutputValidator(prompt_version().output_schema or {}),
        llm_adapter=StubLLMAdapter(valid_raw_output()),
    )
    node = make_prompt_resume_parse_node(service)
    state: RecruitmentWorkflowState = {
        "thread_id": "thread-public-id",
        "user_id": 1,
        "task_id": 10,
        "material_kind": "resume_jd",
        "prompt_version": "recruit_resume_parse:v1",
        "workflow_version": "recruitment_workflow:v1",
        "mock_resume_text": "Built Python services.",
    }

    update = node(state)

    assert update["resume_structure"]["summary"] == "Python backend engineer."
    assert update["node_trace"] == ["resume_parse"]
    assert "error_code" not in update


def test_prompt_resume_parse_node_returns_parse_failed_on_invalid_output(tmp_path: Path) -> None:
    write_template(tmp_path)
    service = ResumeParsePromptService(
        prompt=prompt_version(),
        template_loader=PromptTemplateLoader(tmp_path),
        output_validator=PromptOutputValidator(prompt_version().output_schema or {}),
        llm_adapter=StubLLMAdapter("not json"),
    )
    node = make_prompt_resume_parse_node(service)
    state: RecruitmentWorkflowState = {
        "thread_id": "thread-public-id",
        "user_id": 1,
        "task_id": 10,
        "material_kind": "resume_jd",
        "prompt_version": "recruit_resume_parse:v1",
        "workflow_version": "recruitment_workflow:v1",
        "mock_resume_text": "Built Python services.",
    }

    update = node(state)

    assert update["error_code"] == "PARSE_FAILED"
    assert update["task_status"] == "failed"
    assert update["persisted"] is False
    assert update["node_trace"] == ["resume_parse"]


def test_prompt_resume_parse_node_returns_parse_failed_on_adapter_error(tmp_path: Path) -> None:
    write_template(tmp_path)
    service = ResumeParsePromptService(
        prompt=prompt_version(),
        template_loader=PromptTemplateLoader(tmp_path),
        output_validator=PromptOutputValidator(prompt_version().output_schema or {}),
        llm_adapter=FailingLLMAdapter(),
    )
    node = make_prompt_resume_parse_node(service)
    state: RecruitmentWorkflowState = {
        "thread_id": "thread-public-id",
        "user_id": 1,
        "task_id": 10,
        "material_kind": "resume_jd",
        "prompt_version": "recruit_resume_parse:v1",
        "workflow_version": "recruitment_workflow:v1",
        "mock_resume_text": "Built Python services.",
    }

    update = node(state)

    assert update["error_code"] == "PARSE_FAILED"
    assert update["persisted"] is False
    assert update["node_trace"] == ["resume_parse"]


def test_prompt_resume_parse_node_returns_parse_failed_on_sensitive_text(tmp_path: Path) -> None:
    write_template(tmp_path)
    service = ResumeParsePromptService(
        prompt=prompt_version(),
        template_loader=PromptTemplateLoader(tmp_path),
        output_validator=PromptOutputValidator(prompt_version().output_schema or {}),
        llm_adapter=StubLLMAdapter(sensitive_raw_output()),
    )
    node = make_prompt_resume_parse_node(service)
    state: RecruitmentWorkflowState = {
        "thread_id": "thread-public-id",
        "user_id": 1,
        "task_id": 10,
        "material_kind": "resume_jd",
        "prompt_version": "recruit_resume_parse:v1",
        "workflow_version": "recruitment_workflow:v1",
        "mock_resume_text": "Built Python services.",
    }

    update = node(state)

    assert update["error_code"] == "PARSE_FAILED"
    assert update["persisted"] is False
    assert update["node_trace"] == ["resume_parse"]


def test_prompt_resume_parse_node_skips_when_state_already_failed(tmp_path: Path) -> None:
    write_template(tmp_path)
    service = ResumeParsePromptService(
        prompt=prompt_version(),
        template_loader=PromptTemplateLoader(tmp_path),
        output_validator=PromptOutputValidator(prompt_version().output_schema or {}),
        llm_adapter=StubLLMAdapter(valid_raw_output()),
    )
    node = make_prompt_resume_parse_node(service)
    state: RecruitmentWorkflowState = {
        "thread_id": "thread-public-id",
        "user_id": 1,
        "task_id": 10,
        "material_kind": "resume_jd",
        "prompt_version": "recruit_resume_parse:v1",
        "workflow_version": "recruitment_workflow:v1",
        "error_code": "FILE_UNSAFE",
        "node_trace": ["file_safety"],
    }

    update = node(state)

    assert update == {"node_trace": ["file_safety", "resume_parse"]}
