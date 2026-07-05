"""Prompt output schema validation boundary."""

from __future__ import annotations

import json
from dataclasses import dataclass
from json import JSONDecodeError


class PromptOutputValidationError(ValueError):
    """Raised when prompt output does not match the expected schema."""


@dataclass(frozen=True, slots=True)
class PromptValidatedOutput:
    """Validated prompt output with its source schema."""

    value: dict[str, object]
    schema: dict[str, object]


SUPPORTED_PROPERTY_TYPES = frozenset({"string", "array", "number", "boolean", "null", "object"})


def parse_json_object_output(raw_output: str) -> dict[str, object]:
    """Parse raw model output as a JSON object."""

    try:
        parsed = json.loads(raw_output)
    except JSONDecodeError as exc:
        raise PromptOutputValidationError("prompt output must be valid JSON") from exc
    if not isinstance(parsed, dict):
        raise PromptOutputValidationError("prompt output must be a JSON object")
    return parsed


def _extract_required(schema: dict[str, object]) -> tuple[str, ...]:
    required = schema.get("required", [])
    if not isinstance(required, list):
        raise PromptOutputValidationError("schema.required must be a list")

    names: list[str] = []
    for name in required:
        if not isinstance(name, str) or not name:
            raise PromptOutputValidationError("schema.required entries must be non-empty strings")
        names.append(name)
    return tuple(names)


def _extract_properties(schema: dict[str, object]) -> dict[str, str]:
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        raise PromptOutputValidationError("schema.properties must be an object")

    property_types: dict[str, str] = {}
    for field_name, field_schema in properties.items():
        if not isinstance(field_name, str) or not isinstance(field_schema, dict):
            raise PromptOutputValidationError("schema.properties entries must be objects")
        field_type = field_schema.get("type")
        if not isinstance(field_type, str) or field_type not in SUPPORTED_PROPERTY_TYPES:
            raise PromptOutputValidationError(f"unsupported property type for {field_name}")
        property_types[field_name] = field_type
    return property_types


def _matches_type(value: object, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "null":
        return value is None
    if expected_type == "object":
        return isinstance(value, dict)
    return False


class PromptOutputValidator:
    """Validate prompt JSON output against a constrained object schema."""

    def __init__(self, schema: dict[str, object]) -> None:
        if schema.get("type") != "object":
            raise PromptOutputValidationError("schema.type must be object")
        self._schema = dict(schema)
        self._required = _extract_required(schema)
        self._properties = _extract_properties(schema)

    def validate(self, output: dict[str, object]) -> PromptValidatedOutput:
        """Validate a parsed JSON object."""

        for field_name in self._required:
            if field_name not in output:
                raise PromptOutputValidationError(f"missing required field: {field_name}")

        for field_name, expected_type in self._properties.items():
            if field_name in output and not _matches_type(output[field_name], expected_type):
                raise PromptOutputValidationError(f"invalid type for field: {field_name}")

        return PromptValidatedOutput(value=output, schema=self._schema)

    def validate_json(self, raw_output: str) -> PromptValidatedOutput:
        """Parse and validate raw JSON object output."""

        return self.validate(parse_json_object_output(raw_output))
