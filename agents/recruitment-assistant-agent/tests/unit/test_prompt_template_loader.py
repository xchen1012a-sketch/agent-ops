"""Unit tests for recruitment prompt template loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from recruitment_assistant_agent.prompts.template_loader import (
    PromptTemplateError,
    PromptTemplateLoader,
    extract_required_variables,
    validate_template_key,
)


def write_template(root: Path, key: str, content: str) -> None:
    path = root / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_validate_template_key_accepts_safe_relative_posix_key() -> None:
    assert validate_template_key("recruit_resume_parse/v1/template.txt") == (
        "recruit_resume_parse/v1/template.txt"
    )


@pytest.mark.parametrize(
    "template_key",
    [
        "",
        "/recruit_resume_parse/v1/template.txt",
        "recruit_resume_parse/../secret.txt",
        "recruit_resume_parse\\v1\\template.txt",
        "C:/secrets/template.txt",
        "recruit_resume_parse//template.txt",
        "recruit_resume_parse/./template.txt",
    ],
)
def test_validate_template_key_rejects_unsafe_paths(template_key: str) -> None:
    with pytest.raises(PromptTemplateError):
        validate_template_key(template_key)


def test_extract_required_variables_returns_tuple_from_schema() -> None:
    variables = {"required": ["resume_text", "job_description"]}

    assert extract_required_variables(variables) == ("resume_text", "job_description")


@pytest.mark.parametrize(
    "variables",
    [
        {"required": "resume_text"},
        {"required": ["resume-text"]},
        {"required": [""]},
    ],
)
def test_extract_required_variables_rejects_invalid_required_entries(
    variables: dict[str, object],
) -> None:
    with pytest.raises(PromptTemplateError):
        extract_required_variables(variables)


def test_loader_reads_utf8_template_and_renders_required_variables(tmp_path: Path) -> None:
    write_template(
        tmp_path,
        "recruit_resume_parse/v1/template.txt",
        "Resume: {resume_text}\nJD: {job_description}",
    )
    loader = PromptTemplateLoader(tmp_path)

    result = loader.render(
        template_key="recruit_resume_parse/v1/template.txt",
        variables={"required": ["resume_text", "job_description"]},
        values={
            "resume_text": "Built Python services.",
            "job_description": "Backend role.",
        },
    )

    assert result.template_key == "recruit_resume_parse/v1/template.txt"
    assert result.required_variables == ("resume_text", "job_description")
    assert result.template_text == "Resume: {resume_text}\nJD: {job_description}"
    assert result.rendered_text == "Resume: Built Python services.\nJD: Backend role."


def test_loader_rejects_missing_required_variable(tmp_path: Path) -> None:
    write_template(tmp_path, "recruit_resume_parse/v1/template.txt", "Resume: {resume_text}")
    loader = PromptTemplateLoader(tmp_path)

    with pytest.raises(PromptTemplateError) as exc_info:
        loader.render(
            template_key="recruit_resume_parse/v1/template.txt",
            variables={"required": ["resume_text"]},
            values={},
        )

    assert "resume_text" in str(exc_info.value)


def test_loader_rejects_non_identifier_placeholder(tmp_path: Path) -> None:
    write_template(tmp_path, "recruit_resume_parse/v1/template.txt", "Resume: {resume-text}")
    loader = PromptTemplateLoader(tmp_path)

    with pytest.raises(PromptTemplateError):
        loader.render(
            template_key="recruit_resume_parse/v1/template.txt",
            variables={"required": []},
            values={"resume-text": "unsafe"},
        )


def test_loader_rejects_malformed_format_string(tmp_path: Path) -> None:
    write_template(tmp_path, "recruit_resume_parse/v1/template.txt", "Resume: {resume_text")
    loader = PromptTemplateLoader(tmp_path)

    with pytest.raises(PromptTemplateError):
        loader.render(
            template_key="recruit_resume_parse/v1/template.txt",
            variables={"required": []},
            values={"resume_text": "Built Python services."},
        )


def test_loader_rejects_format_spec_placeholders(tmp_path: Path) -> None:
    write_template(
        tmp_path, "recruit_resume_parse/v1/template.txt", "Resume: {resume_text:{width}}"
    )
    loader = PromptTemplateLoader(tmp_path)

    with pytest.raises(PromptTemplateError):
        loader.render(
            template_key="recruit_resume_parse/v1/template.txt",
            variables={"required": []},
            values={"resume_text": "Built Python services.", "width": 10},
        )


def test_loader_rejects_conversion_placeholders(tmp_path: Path) -> None:
    write_template(tmp_path, "recruit_resume_parse/v1/template.txt", "Resume: {resume_text!r}")
    loader = PromptTemplateLoader(tmp_path)

    with pytest.raises(PromptTemplateError):
        loader.render(
            template_key="recruit_resume_parse/v1/template.txt",
            variables={"required": []},
            values={"resume_text": "Built Python services."},
        )


def test_loader_wraps_value_format_errors_as_prompt_error(tmp_path: Path) -> None:
    class BrokenFormat:
        def __format__(self, format_spec: str) -> str:
            raise RuntimeError("raw candidate value leaked")

    write_template(tmp_path, "recruit_resume_parse/v1/template.txt", "Resume: {resume_text}")
    loader = PromptTemplateLoader(tmp_path)

    with pytest.raises(PromptTemplateError) as exc_info:
        loader.render(
            template_key="recruit_resume_parse/v1/template.txt",
            variables={"required": []},
            values={"resume_text": BrokenFormat()},
        )

    assert exc_info.value.__cause__ is None
    assert "raw candidate" not in str(exc_info.value)


def test_loader_wraps_invalid_utf8_as_prompt_error(tmp_path: Path) -> None:
    path = tmp_path / "recruit_resume_parse/v1/template.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xff")
    loader = PromptTemplateLoader(tmp_path)

    with pytest.raises(PromptTemplateError):
        loader.load("recruit_resume_parse/v1/template.txt")


def test_loader_rejects_template_outside_controlled_root(tmp_path: Path) -> None:
    loader = PromptTemplateLoader(tmp_path)

    with pytest.raises(PromptTemplateError):
        loader.render(
            template_key="../outside/template.txt",
            variables={"required": []},
            values={},
        )


def test_loader_rejects_missing_template(tmp_path: Path) -> None:
    loader = PromptTemplateLoader(tmp_path)

    with pytest.raises(PromptTemplateError):
        loader.render(
            template_key="recruit_resume_parse/v1/template.txt",
            variables={"required": []},
            values={},
        )
