"""Unit tests for safe prompt template loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from legal_consulting_agent.domain.entities.legal_data import PromptVersion
from legal_consulting_agent.domain.value_objects.legal_enums import PromptStatus
from legal_consulting_agent.prompts import (
    PromptTemplateError,
    PromptTemplateLoader,
    extract_required_variables,
    validate_template_key,
)


def prompt_version(template_key: str = "legal_classification/v1/template.txt") -> PromptVersion:
    return PromptVersion(
        id=1,
        prompt_name="legal_classification",
        version="v1",
        template_key=template_key,
        variables={"required": ["question"]},
        output_schema={"type": "object", "required": ["category", "intent"]},
        status=PromptStatus.ACTIVE,
        created_by=1,
    )


def write_template(root: Path, key: str, content: str) -> None:
    path = root.joinpath(*key.split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_render_loads_template_from_safe_key(tmp_path: Path) -> None:
    key = "legal_classification/v1/template.txt"
    write_template(tmp_path, key, "请分类：{question}")
    loader = PromptTemplateLoader(tmp_path)

    result = loader.render(
        prompt=prompt_version(key),
        variables={"question": "公司单方面调岗，我可以拒绝吗？"},
    )

    assert result.prompt_name == "legal_classification"
    assert result.version == "v1"
    assert result.template_key == key
    assert result.content == "请分类：公司单方面调岗，我可以拒绝吗？"
    assert result.output_schema["type"] == "object"


@pytest.mark.parametrize(
    "template_key",
    [
        "",
        "/absolute/template.txt",
        "../outside/template.txt",
        "legal\\template.txt",
        "C:/template.txt",
    ],
)
def test_validate_template_key_rejects_unsafe_keys(template_key: str) -> None:
    with pytest.raises(PromptTemplateError, match="safe relative POSIX key"):
        validate_template_key(template_key)


def test_render_rejects_missing_required_variable(tmp_path: Path) -> None:
    key = "legal_classification/v1/template.txt"
    write_template(tmp_path, key, "请分类：{question}")
    loader = PromptTemplateLoader(tmp_path)

    with pytest.raises(PromptTemplateError, match="missing prompt variables: question"):
        loader.render(prompt=prompt_version(key), variables={})


def test_render_rejects_unknown_template_placeholder(tmp_path: Path) -> None:
    key = "legal_generation/v1/template.txt"
    write_template(tmp_path, key, "问题：{question}；上下文：{context}")
    loader = PromptTemplateLoader(tmp_path)

    with pytest.raises(PromptTemplateError, match="missing prompt variable: context"):
        loader.render(
            prompt=prompt_version(key),
            variables={"question": "公司单方面调岗，我可以拒绝吗？"},
        )


def test_extract_required_variables_rejects_invalid_schema() -> None:
    with pytest.raises(PromptTemplateError, match="variables.required"):
        extract_required_variables({"required": "question"})
