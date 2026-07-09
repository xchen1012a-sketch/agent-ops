"""Prompt template loading and structured output validation."""

from __future__ import annotations

import json
import string
from dataclasses import dataclass
from importlib import resources
from types import MappingProxyType
from typing import Any

PROMPT_RESOURCE_PACKAGE = "data_query_agent.prompts.data_query"


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    """Versioned prompt template loaded from package resources."""

    name: str
    version: str
    template: str
    variables_schema: MappingProxyType[str, object]
    output_schema: MappingProxyType[str, object]


class PromptTemplateService:
    """Load prompt templates and validate structured LLM outputs.

    Prompt files are the source of truth for text, variables, and output schema.
    The service only renders declared variables and validates JSON output before
    any workflow node can consume it.
    """

    def __init__(self, *, resource_package: str = PROMPT_RESOURCE_PACKAGE) -> None:
        self._resource_package = resource_package

    def load_template(self, *, prompt_name: str, version: str) -> PromptTemplate:
        """Load and validate one prompt template resource."""
        resource_name = f"{prompt_name}.{version}.json"
        try:
            raw_body = (
                resources.files(self._resource_package)
                .joinpath(resource_name)
                .read_text(encoding="utf-8")
            )
        except FileNotFoundError as exc:
            raise ValueError(f"prompt template not found: {prompt_name}@{version}") from exc
        raw = _as_object(json.loads(raw_body), "prompt template")
        name = _as_string(raw.get("name"), "name")
        loaded_version = _as_string(raw.get("version"), "version")
        if name != prompt_name or loaded_version != version:
            raise ValueError("prompt template name/version does not match resource path")
        template = _as_string(raw.get("template"), "template")
        variables_schema = _as_object(raw.get("variables_schema"), "variables_schema")
        output_schema = _as_object(raw.get("output_schema"), "output_schema")
        _validate_template_variables(template, variables_schema)
        _validate_output_schema(output_schema)
        return PromptTemplate(
            name=name,
            version=loaded_version,
            template=template,
            variables_schema=MappingProxyType(dict(variables_schema)),
            output_schema=MappingProxyType(dict(output_schema)),
        )

    def render(self, *, template: PromptTemplate, variables: dict[str, object]) -> str:
        """Render a prompt only when all required variables are present."""
        required = _required_variables(template.variables_schema)
        missing = sorted(name for name in required if name not in variables)
        if missing:
            raise ValueError(f"missing prompt variables: {', '.join(missing)}")
        allowed = _declared_variables(template.variables_schema)
        extra = sorted(name for name in variables if name not in allowed)
        if extra:
            raise ValueError(f"unknown prompt variables: {', '.join(extra)}")
        safe_variables = {name: str(value) for name, value in variables.items()}
        return template.template.format(**safe_variables)

    def validate_output(self, *, template: PromptTemplate, raw_output: str) -> dict[str, object]:
        """Parse and validate structured JSON output against the template schema."""
        try:
            parsed = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM output must be valid JSON") from exc
        output = _as_object(parsed, "LLM output")
        _validate_object_against_schema(output, template.output_schema)
        return output


def _validate_template_variables(template: str, schema: dict[str, object]) -> None:
    placeholders = {
        field_name
        for _, field_name, _, _ in string.Formatter().parse(template)
        if field_name is not None and field_name != ""
    }
    declared = _declared_variables(schema)
    undeclared = sorted(name for name in placeholders if name not in declared)
    if undeclared:
        raise ValueError(f"template uses undeclared variables: {', '.join(undeclared)}")


def _validate_output_schema(schema: dict[str, object]) -> None:
    if schema.get("type") != "object":
        raise ValueError("output schema type must be object")
    properties = _as_object(schema.get("properties"), "output_schema.properties")
    required = _required_variables(schema)
    unknown_required = sorted(name for name in required if name not in properties)
    if unknown_required:
        raise ValueError(
            f"required output fields missing from properties: {', '.join(unknown_required)}"
        )


def _validate_object_against_schema(
    output: dict[str, object], schema: MappingProxyType[str, object]
) -> None:
    properties = _as_object(schema.get("properties"), "output_schema.properties")
    for field_name in _required_variables(schema):
        if field_name not in output:
            raise ValueError(f"LLM output missing required field: {field_name}")
    for field_name, value in output.items():
        field_schema = properties.get(field_name)
        if field_schema is None:
            continue
        expected_type = _as_object(field_schema, f"output_schema.properties.{field_name}").get(
            "type"
        )
        if isinstance(expected_type, str) and not _matches_json_type(value, expected_type):
            raise ValueError(f"LLM output field has invalid type: {field_name}")


def _matches_json_type(value: object, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "null":
        return value is None
    raise ValueError(f"unsupported JSON schema type: {expected_type}")


def _required_variables(schema: MappingProxyType[str, object] | dict[str, object]) -> set[str]:
    required = schema.get("required", [])
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        raise ValueError("schema required must be a string list")
    return set(required)


def _declared_variables(schema: dict[str, object] | MappingProxyType[str, object]) -> set[str]:
    properties = _as_object(schema.get("properties"), "variables_schema.properties")
    return set(properties) | _required_variables(schema)


def _as_object(value: Any, field_name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    return value


def _as_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value
