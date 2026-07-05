"""Unit tests for prompt output schema validation."""

from __future__ import annotations

import pytest

from recruitment_assistant_agent.prompts.output_validator import (
    PromptOutputValidationError,
    PromptOutputValidator,
    parse_json_object_output,
)


def object_schema() -> dict[str, object]:
    return {
        "type": "object",
        "required": ["summary", "skills", "total_years_exp", "fairness_passed"],
        "properties": {
            "summary": {"type": "string"},
            "skills": {"type": "array"},
            "total_years_exp": {"type": "number"},
            "fairness_passed": {"type": "boolean"},
            "notes": {"type": "null"},
            "metadata": {"type": "object"},
        },
    }


def valid_output() -> dict[str, object]:
    return {
        "summary": "Python backend engineer.",
        "skills": ["Python"],
        "total_years_exp": 5.5,
        "fairness_passed": True,
        "notes": None,
        "metadata": {"source": "mock"},
    }


def test_parse_json_object_output_returns_object() -> None:
    assert parse_json_object_output('{"summary": "ok"}') == {"summary": "ok"}


@pytest.mark.parametrize("raw_output", ["", "[]", "null", "not json"])
def test_parse_json_object_output_rejects_non_object(raw_output: str) -> None:
    with pytest.raises(PromptOutputValidationError):
        parse_json_object_output(raw_output)


def test_validator_accepts_required_fields_and_supported_types() -> None:
    validator = PromptOutputValidator(object_schema())

    result = validator.validate(valid_output())

    assert result.value == valid_output()
    assert result.schema == object_schema()


def test_validator_validates_raw_json_object() -> None:
    validator = PromptOutputValidator(object_schema())

    result = validator.validate_json(
        '{"summary":"ok","skills":[],"total_years_exp":0,"fairness_passed":false}'
    )

    assert result.value["summary"] == "ok"


def test_validator_rejects_non_object_schema() -> None:
    with pytest.raises(PromptOutputValidationError):
        PromptOutputValidator({"type": "array"})


def test_validator_rejects_invalid_required_schema() -> None:
    with pytest.raises(PromptOutputValidationError):
        PromptOutputValidator({"type": "object", "required": "summary"})


def test_validator_rejects_missing_required_field() -> None:
    output = valid_output()
    output.pop("summary")
    validator = PromptOutputValidator(object_schema())

    with pytest.raises(PromptOutputValidationError) as exc_info:
        validator.validate(output)

    assert "summary" in str(exc_info.value)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("summary", 123),
        ("skills", "Python"),
        ("total_years_exp", "5"),
        ("fairness_passed", "true"),
        ("notes", "not-null"),
        ("metadata", []),
    ],
)
def test_validator_rejects_wrong_property_type(field_name: str, bad_value: object) -> None:
    output = valid_output()
    output[field_name] = bad_value
    validator = PromptOutputValidator(object_schema())

    with pytest.raises(PromptOutputValidationError) as exc_info:
        validator.validate(output)

    assert field_name in str(exc_info.value)


def test_validator_allows_integer_for_number_type() -> None:
    output = valid_output()
    output["total_years_exp"] = 5
    validator = PromptOutputValidator(object_schema())

    result = validator.validate(output)

    assert result.value["total_years_exp"] == 5


def test_validator_rejects_bool_for_number_type() -> None:
    output = valid_output()
    output["total_years_exp"] = True
    validator = PromptOutputValidator(object_schema())

    with pytest.raises(PromptOutputValidationError):
        validator.validate(output)


def test_validator_rejects_unsupported_property_type() -> None:
    schema = {"type": "object", "properties": {"summary": {"type": "integer"}}}

    with pytest.raises(PromptOutputValidationError):
        PromptOutputValidator(schema)
