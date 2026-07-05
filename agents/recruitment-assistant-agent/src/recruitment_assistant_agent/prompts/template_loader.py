"""Safe prompt template loading and rendering boundary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from string import Formatter
from typing import Any


class PromptTemplateError(ValueError):
    """Raised when prompt template loading or rendering is unsafe or invalid."""


@dataclass(frozen=True, slots=True)
class PromptRenderResult:
    """Rendered prompt text with its source template metadata."""

    template_key: str
    template_text: str
    rendered_text: str
    required_variables: tuple[str, ...]


def validate_template_key(template_key: str) -> str:
    """Validate that a template key is a safe relative POSIX path."""

    if not template_key:
        raise PromptTemplateError("template_key must be non-empty")
    if "\\" in template_key or "//" in template_key:
        raise PromptTemplateError("template_key must use safe POSIX separators")
    if ":" in template_key:
        raise PromptTemplateError("template_key must not contain a drive or scheme")
    if any(part in {"", ".", ".."} for part in template_key.split("/")):
        raise PromptTemplateError("template_key must not contain traversal segments")

    path = PurePosixPath(template_key)
    if path.is_absolute():
        raise PromptTemplateError("template_key must be relative")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise PromptTemplateError("template_key must not contain traversal segments")
    return path.as_posix()


def extract_required_variables(variables: dict[str, Any]) -> tuple[str, ...]:
    """Extract required prompt variables from prompt metadata."""

    required = variables.get("required", [])
    if not isinstance(required, list):
        raise PromptTemplateError("variables.required must be a list")

    names: list[str] = []
    for name in required:
        if not isinstance(name, str) or not name.isidentifier():
            raise PromptTemplateError("variables.required entries must be identifiers")
        names.append(name)
    return tuple(names)


def _template_fields(template_text: str) -> set[str]:
    fields: set[str] = set()
    try:
        parsed = tuple(Formatter().parse(template_text))
    except ValueError as exc:
        raise PromptTemplateError("template format is invalid") from exc

    for _, field_name, format_spec, conversion in parsed:
        if field_name is not None:
            if not field_name.isidentifier():
                raise PromptTemplateError("template placeholders must be identifiers")
            if format_spec or conversion is not None:
                raise PromptTemplateError("template placeholders must be simple identifiers")
            fields.add(field_name)
    return fields


class PromptTemplateLoader:
    """Load UTF-8 prompt templates from one controlled root directory."""

    def __init__(self, template_root: Path) -> None:
        self._template_root = template_root.resolve()

    def load(self, template_key: str) -> str:
        """Load a prompt template by safe key."""

        safe_key = validate_template_key(template_key)
        template_path = (self._template_root / safe_key).resolve()
        if not template_path.is_relative_to(self._template_root):
            raise PromptTemplateError("template_key resolved outside prompt root")
        if not template_path.is_file():
            raise PromptTemplateError("template not found")
        try:
            return template_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise PromptTemplateError("template must be valid UTF-8") from exc

    def render(
        self,
        *,
        template_key: str,
        variables: dict[str, Any],
        values: dict[str, object],
    ) -> PromptRenderResult:
        """Load and render a prompt template with required variables."""

        safe_key = validate_template_key(template_key)
        template_text = self.load(safe_key)
        required_variables = extract_required_variables(variables)
        missing = [name for name in required_variables if name not in values]
        if missing:
            raise PromptTemplateError(f"missing required prompt variables: {', '.join(missing)}")

        fields = _template_fields(template_text)
        missing_fields = [name for name in fields if name not in values]
        if missing_fields:
            raise PromptTemplateError(
                f"missing template values: {', '.join(sorted(missing_fields))}"
            )

        try:
            rendered_text = template_text.format(**values)
        except Exception:
            raise PromptTemplateError("template rendering failed") from None
        return PromptRenderResult(
            template_key=safe_key,
            template_text=template_text,
            rendered_text=rendered_text,
            required_variables=required_variables,
        )
