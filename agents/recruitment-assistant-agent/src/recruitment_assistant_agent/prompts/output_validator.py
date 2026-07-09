"""Prompt output schema validation boundary."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any, Self


class PromptOutputValidationError(ValueError):
    """Raised when prompt output does not match the expected schema."""


@dataclass(frozen=True, slots=True)
class PromptValidatedOutput:
    """Validated prompt output with its source schema."""

    value: dict[str, object]
    schema: dict[str, object]


@dataclass(frozen=True, slots=True)
class _SchemaNode:
    type_name: str
    required: tuple[str, ...] = ()
    properties: dict[str, Self] | None = None
    items: Self | None = None


SUPPORTED_PROPERTY_TYPES = frozenset({"string", "array", "number", "boolean", "null", "object"})
DEFAULT_MAX_RAW_OUTPUT_CHARS = 50_000


def _reject_json_constant(constant: str) -> object:
    raise PromptOutputValidationError("prompt output must be standard JSON")


def parse_json_object_output(
    raw_output: str,
    *,
    max_raw_output_chars: int = DEFAULT_MAX_RAW_OUTPUT_CHARS,
) -> dict[str, object]:
    """Parse raw model output as a JSON object."""

    if len(raw_output) > max_raw_output_chars:
        raise PromptOutputValidationError("prompt output exceeds maximum length")

    try:
        parsed = json.loads(
            raw_output,
            parse_constant=_reject_json_constant,
        )
    except JSONDecodeError:
        raise PromptOutputValidationError("prompt output must be valid JSON") from None
    except ValueError:
        raise PromptOutputValidationError("prompt output contains invalid JSON values") from None
    if not isinstance(parsed, dict):
        raise PromptOutputValidationError("prompt output must be a JSON object")
    return parsed


def _extract_required(schema: dict[str, Any], path: str) -> tuple[str, ...]:
    required = schema.get("required", [])
    if not isinstance(required, list):
        raise PromptOutputValidationError(f"{path}.required must be a list")

    names: list[str] = []
    for name in required:
        if not isinstance(name, str) or not name:
            raise PromptOutputValidationError(f"{path}.required entries must be non-empty strings")
        names.append(name)
    return tuple(names)


def _extract_properties(schema: dict[str, Any], path: str) -> dict[str, _SchemaNode]:
    properties = schema.get("properties")
    if not isinstance(properties, dict) or not properties:
        raise PromptOutputValidationError(f"{path}.properties must be a non-empty object")

    parsed_properties: dict[str, _SchemaNode] = {}
    for field_name, field_schema in properties.items():
        if not isinstance(field_name, str) or not field_name:
            raise PromptOutputValidationError(f"{path}.properties keys must be non-empty strings")
        if not isinstance(field_schema, dict):
            raise PromptOutputValidationError(f"{path}.{field_name} schema must be an object")
        parsed_properties[field_name] = _parse_schema_node(field_schema, f"{path}.{field_name}")
    return parsed_properties


def _parse_schema_node(schema: dict[str, Any], path: str) -> _SchemaNode:
    type_name = schema.get("type")
    if not isinstance(type_name, str) or type_name not in SUPPORTED_PROPERTY_TYPES:
        raise PromptOutputValidationError(f"unsupported property type for {path}")

    if type_name == "object":
        required = _extract_required(schema, path)
        properties = _extract_properties(schema, path)
        for field_name in required:
            if field_name not in properties:
                raise PromptOutputValidationError(
                    f"required field is not declared in properties: {path}.{field_name}"
                )
        return _SchemaNode(type_name=type_name, required=required, properties=properties)

    if type_name == "array":
        items = schema.get("items")
        if not isinstance(items, dict):
            raise PromptOutputValidationError(f"{path}.items must be an object")
        return _SchemaNode(
            type_name=type_name,
            items=_parse_schema_node(items, f"{path}[]"),
        )

    return _SchemaNode(type_name=type_name)


def _matches_scalar_type(value: object, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "number":
        if isinstance(value, bool):
            return False
        if isinstance(value, int):
            return True
        return isinstance(value, float) and math.isfinite(value)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "null":
        return value is None
    return False


def _validate_value(value: object, node: _SchemaNode, path: str) -> None:
    if node.type_name == "object":
        if not isinstance(value, dict):
            raise PromptOutputValidationError(f"invalid type for field: {path}")
        _validate_object(value, node, path)
        return

    if node.type_name == "array":
        if not isinstance(value, list):
            raise PromptOutputValidationError(f"invalid type for field: {path}")
        if node.items is None:
            raise PromptOutputValidationError(f"array schema is missing items: {path}")
        for index, item in enumerate(value):
            _validate_value(item, node.items, f"{path}[{index}]")
        return

    if not _matches_scalar_type(value, node.type_name):
        raise PromptOutputValidationError(f"invalid type for field: {path}")


def _validate_object(output: dict[str, object], node: _SchemaNode, path: str) -> None:
    if node.properties is None:
        raise PromptOutputValidationError(f"object schema is missing properties: {path}")

    for field_name in node.required:
        if field_name not in output:
            raise PromptOutputValidationError(f"missing required field: {path}.{field_name}")

    for field_name in output:
        if field_name not in node.properties:
            raise PromptOutputValidationError(f"unknown output field: {path}.{field_name}")

    for field_name, field_schema in node.properties.items():
        if field_name in output:
            _validate_value(output[field_name], field_schema, f"{path}.{field_name}")


class PromptOutputValidator:
    """Validate prompt JSON output against a constrained object schema."""

    def __init__(
        self,
        schema: dict[str, object],
        *,
        max_raw_output_chars: int = DEFAULT_MAX_RAW_OUTPUT_CHARS,
    ) -> None:
        if schema.get("type") != "object":
            raise PromptOutputValidationError("schema.type must be object")
        self._schema = dict(schema)
        self._schema_node = _parse_schema_node(schema, "schema")
        self._max_raw_output_chars = max_raw_output_chars

    def validate(self, output: dict[str, object]) -> PromptValidatedOutput:
        """Validate a parsed JSON object."""

        _validate_object(output, self._schema_node, "output")
        return PromptValidatedOutput(value=output, schema=self._schema)

    def validate_json(self, raw_output: str) -> PromptValidatedOutput:
        """Parse and validate raw JSON object output."""

        return self.validate(
            parse_json_object_output(
                raw_output,
                max_raw_output_chars=self._max_raw_output_chars,
            )
        )
