"""Unit tests for Prompt output schema validation."""

from __future__ import annotations

import pytest

from legal_consulting_agent.domain.entities.legal_data import PromptVersion
from legal_consulting_agent.domain.value_objects.legal_enums import PromptStatus
from legal_consulting_agent.prompts import (
    PromptOutputValidationError,
    PromptOutputValidator,
    parse_json_object_output,
)


def classification_prompt() -> PromptVersion:
    return PromptVersion(
        id=1,
        prompt_name="legal_classification",
        version="v1",
        template_key="legal_classification/v1/template.txt",
        variables={"required": ["question"]},
        output_schema={
            "type": "object",
            "required": ["category", "intent", "legal_entities"],
            "properties": {
                "category": {"type": "string"},
                "intent": {"type": "string"},
                "legal_entities": {"type": "object"},
            },
        },
        status=PromptStatus.ACTIVE,
        created_by=1,
    )


def test_parse_json_object_output_requires_object() -> None:
    parsed = parse_json_object_output('{"category":"civil_labor"}')

    assert parsed["category"] == "civil_labor"


@pytest.mark.parametrize("raw_output", ["not-json", '["civil_labor"]', '"civil_labor"'])
def test_parse_json_object_output_rejects_invalid_json_object(raw_output: str) -> None:
    with pytest.raises(PromptOutputValidationError):
        parse_json_object_output(raw_output)


def test_validator_accepts_structured_classification_output() -> None:
    validator = PromptOutputValidator()

    result = validator.validate_json(
        prompt=classification_prompt(),
        raw_output=(
            '{"category":"civil_labor","intent":"询问劳动合同争议",'
            '"legal_entities":{"case_keywords":["调岗"]}}'
        ),
    )

    assert result.prompt_name == "legal_classification"
    assert result.version == "v1"
    assert result.data["category"] == "civil_labor"


def test_validator_rejects_missing_required_field() -> None:
    validator = PromptOutputValidator()

    with pytest.raises(PromptOutputValidationError, match="missing output fields: intent"):
        validator.validate(
            prompt=classification_prompt(),
            output={"category": "civil_labor", "legal_entities": {}},
        )


def test_validator_rejects_wrong_field_type() -> None:
    validator = PromptOutputValidator()

    with pytest.raises(PromptOutputValidationError, match="output field category must be string"):
        validator.validate(
            prompt=classification_prompt(),
            output={
                "category": ["civil_labor"],
                "intent": "询问劳动合同争议",
                "legal_entities": {},
            },
        )


def test_validator_rejects_invalid_schema() -> None:
    prompt = classification_prompt()
    invalid_prompt = PromptVersion(
        id=prompt.id,
        prompt_name=prompt.prompt_name,
        version=prompt.version,
        template_key=prompt.template_key,
        variables=prompt.variables,
        output_schema={"type": "array"},
        status=prompt.status,
        created_by=prompt.created_by,
    )

    with pytest.raises(PromptOutputValidationError, match="output_schema.type must be object"):
        PromptOutputValidator().validate(prompt=invalid_prompt, output={})
