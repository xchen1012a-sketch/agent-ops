"""Prompt registry and safe template loading."""

from legal_consulting_agent.prompts.output_validator import (
    PromptOutputValidationError,
    PromptOutputValidator,
    PromptValidatedOutput,
    parse_json_object_output,
)
from legal_consulting_agent.prompts.template_loader import (
    PromptRenderResult,
    PromptTemplateError,
    PromptTemplateLoader,
    extract_required_variables,
    validate_template_key,
)

__all__ = [
    "PromptRenderResult",
    "PromptTemplateError",
    "PromptTemplateLoader",
    "PromptOutputValidationError",
    "PromptOutputValidator",
    "PromptValidatedOutput",
    "extract_required_variables",
    "parse_json_object_output",
    "validate_template_key",
]
