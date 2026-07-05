"""Prompt registry and safe template loading."""

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
    "extract_required_variables",
    "validate_template_key",
]
