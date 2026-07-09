"""Safe loader for versioned prompt templates."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

from legal_consulting_agent.domain.entities.legal_data import PromptVersion


class PromptTemplateError(ValueError):
    """Raised when prompt template metadata or variables are invalid."""


@dataclass(frozen=True, slots=True)
class PromptRenderResult:
    """Rendered prompt with version metadata and output schema."""

    prompt_name: str
    version: str
    template_key: str
    content: str
    output_schema: Mapping[str, object]


def validate_template_key(template_key: str) -> PurePosixPath:
    """Validate a stored template key as a safe relative POSIX path."""

    key_path = PurePosixPath(template_key)
    if (
        not template_key
        or key_path.is_absolute()
        or ".." in key_path.parts
        or "\\" in template_key
        or ":" in template_key
    ):
        raise PromptTemplateError("template_key must be a safe relative POSIX key")
    return key_path


def extract_required_variables(variables_schema: Mapping[str, object]) -> tuple[str, ...]:
    """Extract required variable names from PromptVersion.variables."""

    required = variables_schema.get("required", [])
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        raise PromptTemplateError("variables.required must be a list of strings")
    return tuple(required)


class PromptTemplateLoader:
    """Load and render versioned prompt templates from a controlled root."""

    def __init__(self, templates_root: Path) -> None:
        self._templates_root = templates_root.resolve()

    def render(
        self,
        *,
        prompt: PromptVersion,
        variables: Mapping[str, object],
    ) -> PromptRenderResult:
        """Render a prompt template using explicit caller-provided variables."""

        key_path = validate_template_key(prompt.template_key)
        template_path = (self._templates_root / Path(*key_path.parts)).resolve()
        if not template_path.is_relative_to(self._templates_root):
            raise PromptTemplateError("template_key resolves outside templates root")

        required_variables = extract_required_variables(prompt.variables)
        missing = [name for name in required_variables if name not in variables]
        if missing:
            raise PromptTemplateError(f"missing prompt variables: {', '.join(missing)}")

        try:
            template_text = template_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise PromptTemplateError("prompt template file not found") from exc

        try:
            content = template_text.format_map(dict(variables))
        except KeyError as exc:
            missing_key = str(exc.args[0])
            raise PromptTemplateError(f"missing prompt variable: {missing_key}") from exc

        return PromptRenderResult(
            prompt_name=prompt.prompt_name,
            version=prompt.version,
            template_key=prompt.template_key,
            content=content,
            output_schema=cast(Mapping[str, object], prompt.output_schema),
        )
