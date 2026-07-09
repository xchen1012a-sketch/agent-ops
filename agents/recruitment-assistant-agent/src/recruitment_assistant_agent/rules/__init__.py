"""Versioned recruitment MVP rule package."""

from recruitment_assistant_agent.rules.recruitment_mvp_rules import (
    load_recruitment_mvp_rules,
    protected_attribute_fields,
    rule_version,
    skill_keywords,
    workflow_node_names,
)

__all__ = [
    "load_recruitment_mvp_rules",
    "protected_attribute_fields",
    "rule_version",
    "skill_keywords",
    "workflow_node_names",
]
