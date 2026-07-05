"""Unit tests for prompt template loading and output validation."""

from __future__ import annotations

import json

import pytest

from data_query_agent.application.services.prompt_template_service import PromptTemplateService


def test_loads_prompt_template_from_versioned_resource() -> None:
    service = PromptTemplateService()

    template = service.load_template(prompt_name="nl2sql", version="v1")

    assert template.name == "nl2sql"
    assert template.version == "v1"
    assert "question" in template.variables_schema["required"]
    assert template.output_schema["type"] == "object"


def test_render_rejects_missing_and_unknown_variables() -> None:
    service = PromptTemplateService()
    template = service.load_template(prompt_name="nl2sql", version="v1")

    with pytest.raises(ValueError, match="missing prompt variables"):
        service.render(template=template, variables={"question": "total sales"})
    with pytest.raises(ValueError, match="unknown prompt variables"):
        service.render(
            template=template,
            variables={
                "question": "total sales",
                "schema_summary": "wide_orders",
                "extra": "not declared",
            },
        )


def test_render_uses_declared_variables() -> None:
    service = PromptTemplateService()
    template = service.load_template(prompt_name="nl2sql", version="v1")

    rendered = service.render(
        template=template,
        variables={"question": "total sales", "schema_summary": "wide_orders"},
    )

    assert "total sales" in rendered
    assert "wide_orders" in rendered


def test_validate_output_accepts_matching_json_schema() -> None:
    service = PromptTemplateService()
    template = service.load_template(prompt_name="nl2sql", version="v1")

    output = service.validate_output(
        template=template,
        raw_output=json.dumps(
            {
                "sql": "SELECT SUM(total_amount) FROM wide_orders LIMIT 100",
                "confidence": 0.91,
                "reasoning_summary": "matched sales metric",
            }
        ),
    )

    assert output["confidence"] == 0.91


@pytest.mark.parametrize(
    ("raw_output", "message"),
    [
        ("not-json", "valid JSON"),
        (json.dumps({"sql": "SELECT 1"}), "missing required field"),
        (json.dumps({"sql": "SELECT 1", "confidence": "high"}), "invalid type"),
    ],
)
def test_validate_output_rejects_non_json_or_schema_mismatch(
    raw_output: str,
    message: str,
) -> None:
    service = PromptTemplateService()
    template = service.load_template(prompt_name="nl2sql", version="v1")

    with pytest.raises(ValueError, match=message):
        service.validate_output(template=template, raw_output=raw_output)


def test_missing_template_resource_is_rejected() -> None:
    service = PromptTemplateService()

    with pytest.raises(ValueError, match="prompt template not found"):
        service.load_template(prompt_name="unknown", version="v1")
