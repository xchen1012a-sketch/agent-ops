"""Structured validation for prompt / mock LLM outputs."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from legal_consulting_agent.domain.entities.legal_data import PromptVersion


class PromptOutputValidationError(ValueError):
    """Raised when a model output does not satisfy the prompt output schema."""


@dataclass(frozen=True, slots=True)
class PromptValidatedOutput:
    """Validated model output with prompt version metadata."""

    prompt_name: str
    version: str
    data: Mapping[str, object]


def parse_json_object_output(raw_output: str) -> Mapping[str, object]:
    """Parse an LLM JSON string and require an object at the top level."""

    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise PromptOutputValidationError("model output must be valid JSON") from exc
    if not isinstance(parsed, dict) or not all(isinstance(key, str) for key in parsed):
        raise PromptOutputValidationError("model output must be a JSON object")
    return cast(Mapping[str, object], parsed)


def _extract_required_fields(schema: Mapping[str, object]) -> tuple[str, ...]:
    required = schema.get("required", [])
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        raise PromptOutputValidationError("output_schema.required must be a list of strings")
    return tuple(required)


def _extract_properties(schema: Mapping[str, object]) -> Mapping[str, object]:
    properties = schema.get("properties", {})
    if not isinstance(properties, dict) or not all(
        isinstance(key, str) and isinstance(value, dict) for key, value in properties.items()
    ):
        raise PromptOutputValidationError("output_schema.properties must be an object")
    return cast(Mapping[str, object], properties)


def _matches_json_type(value: object, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return (isinstance(value, int | float)) and not isinstance(value, bool)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "null":
        return value is None
    raise PromptOutputValidationError(f"unsupported output schema type: {expected_type}")


def _extract_expected_types(field_name: str, field_schema: Mapping[str, object]) -> tuple[str, ...]:
    expected_type = field_schema.get("type")
    if isinstance(expected_type, str):
        return (expected_type,)
    if isinstance(expected_type, list) and all(isinstance(item, str) for item in expected_type):
        return tuple(expected_type)
    raise PromptOutputValidationError(
        f"output_schema.properties.{field_name}.type must be a string or list of strings"
    )


class PromptOutputValidator:
    """Validate prompt outputs against the stored PromptVersion output schema."""

    def validate(
        self,
        *,
        prompt: PromptVersion,
        output: Mapping[str, object],
    ) -> PromptValidatedOutput:
        """Validate a parsed model output object."""

        schema = cast(Mapping[str, object], prompt.output_schema)
        if schema.get("type") != "object":
            raise PromptOutputValidationError("output_schema.type must be object")

        missing = [field for field in _extract_required_fields(schema) if field not in output]
        if missing:
            raise PromptOutputValidationError(f"missing output fields: {', '.join(missing)}")

        properties = _extract_properties(schema)
        for field_name, field_schema in properties.items():
            if field_name not in output:
                continue
            expected_types = _extract_expected_types(
                field_name,
                cast(Mapping[str, object], field_schema),
            )
            if not any(_matches_json_type(output[field_name], item) for item in expected_types):
                raise PromptOutputValidationError(
                    f"output field {field_name} must be {' or '.join(expected_types)}"
                )

        return PromptValidatedOutput(
            prompt_name=prompt.prompt_name,
            version=prompt.version,
            data=output,
        )

    def validate_json(
        self,
        *,
        prompt: PromptVersion,
        raw_output: str,
    ) -> PromptValidatedOutput:
        """Parse and validate a raw JSON output string."""

        return self.validate(
            prompt=prompt,
            output=parse_json_object_output(raw_output),
        )
