"""Prompt registry. Each prompt lives under prompts/<name>/v<n>/ with template, variables, and output schema."""

from recruitment_assistant_agent.prompts.output_validator import (
    PromptOutputValidationError,
    PromptOutputValidator,
    PromptValidatedOutput,
    parse_json_object_output,
)
from recruitment_assistant_agent.prompts.template_loader import (
    PromptRenderResult,
    PromptTemplateError,
    PromptTemplateLoader,
    extract_required_variables,
    validate_template_key,
)

__all__ = [
    "PromptOutputValidationError",
    "PromptOutputValidator",
    "PromptRenderResult",
    "PromptTemplateError",
    "PromptTemplateLoader",
    "PromptValidatedOutput",
    "extract_required_variables",
    "parse_json_object_output",
    "validate_template_key",
]
