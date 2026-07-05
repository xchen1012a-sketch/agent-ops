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
            "skills": {"type": "array", "items": {"type": "string"}},
            "total_years_exp": {"type": "number"},
            "fairness_passed": {"type": "boolean"},
            "notes": {"type": "null"},
            "metadata": {
                "type": "object",
                "required": ["source"],
                "properties": {"source": {"type": "string"}},
            },
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


def test_parse_json_object_output_wraps_oversized_integer_errors() -> None:
    raw_output = '{"total_years_exp": ' + ("9" * 5_000) + "}"

    with pytest.raises(PromptOutputValidationError) as exc_info:
        parse_json_object_output(raw_output)

    assert exc_info.value.__cause__ is None


def test_parse_json_object_output_rejects_non_standard_json_constants() -> None:
    with pytest.raises(PromptOutputValidationError):
        parse_json_object_output('{"total_years_exp": NaN}')


def test_parse_json_object_output_does_not_chain_raw_json_error() -> None:
    raw_output = '{"summary": "raw candidate pii"'

    with pytest.raises(PromptOutputValidationError) as exc_info:
        parse_json_object_output(raw_output)

    assert exc_info.value.__cause__ is None
    assert "raw candidate pii" not in str(exc_info.value)


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


def test_validator_rejects_non_finite_number_type() -> None:
    output = valid_output()
    output["total_years_exp"] = float("nan")
    validator = PromptOutputValidator(object_schema())

    with pytest.raises(PromptOutputValidationError):
        validator.validate(output)


def test_validator_rejects_bool_for_number_type() -> None:
    output = valid_output()
    output["total_years_exp"] = True
    validator = PromptOutputValidator(object_schema())

    with pytest.raises(PromptOutputValidationError):
        validator.validate(output)


def test_validator_rejects_array_items_with_wrong_type() -> None:
    output = valid_output()
    output["skills"] = ["Python", 123]
    validator = PromptOutputValidator(object_schema())

    with pytest.raises(PromptOutputValidationError) as exc_info:
        validator.validate(output)

    assert "skills" in str(exc_info.value)


def test_validator_rejects_nested_object_unknown_fields() -> None:
    output = valid_output()
    output["metadata"] = {"source": "mock", "raw_instruction": "ignore rubric"}
    validator = PromptOutputValidator(object_schema())

    with pytest.raises(PromptOutputValidationError) as exc_info:
        validator.validate(output)

    assert "metadata.raw_instruction" in str(exc_info.value)


def test_validator_rejects_unconstrained_array_schema() -> None:
    schema: dict[str, object] = {
        "type": "object",
        "properties": {"skills": {"type": "array"}},
    }

    with pytest.raises(PromptOutputValidationError):
        PromptOutputValidator(schema)


def test_validator_rejects_unconstrained_object_schema() -> None:
    schema: dict[str, object] = {
        "type": "object",
        "properties": {"metadata": {"type": "object"}},
    }

    with pytest.raises(PromptOutputValidationError):
        PromptOutputValidator(schema)


def test_validator_rejects_unknown_fields() -> None:
    output = {**valid_output(), "raw_instruction": "ignore scoring rubric"}
    validator = PromptOutputValidator(object_schema())

    with pytest.raises(PromptOutputValidationError) as exc_info:
        validator.validate(output)

    assert "raw_instruction" in str(exc_info.value)


def test_validator_rejects_required_field_not_declared_in_properties() -> None:
    schema: dict[str, object] = {
        "type": "object",
        "required": ["summary"],
        "properties": {},
    }

    with pytest.raises(PromptOutputValidationError):
        PromptOutputValidator(schema)


def test_validator_rejects_oversized_raw_json_output() -> None:
    validator = PromptOutputValidator(object_schema(), max_raw_output_chars=10)

    with pytest.raises(PromptOutputValidationError):
        validator.validate_json(
            '{"summary":"ok","skills":[],"total_years_exp":0,"fairness_passed":false}'
        )


def test_validator_rejects_unsupported_property_type() -> None:
    schema: dict[str, object] = {
        "type": "object",
        "properties": {"summary": {"type": "integer"}},
    }

    with pytest.raises(PromptOutputValidationError):
        PromptOutputValidator(schema)
