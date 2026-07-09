"""Load versioned recruitment MVP rules from package data."""

from __future__ import annotations

import json
from collections.abc import Mapping
from functools import lru_cache
from importlib.resources import files
from typing import cast

RULE_RESOURCE = "recruitment_mvp_v1.json"


@lru_cache
def load_recruitment_mvp_rules() -> dict[str, object]:
    """Return the versioned rules used by the deterministic MVP path."""

    resource = files("recruitment_assistant_agent.rules").joinpath(RULE_RESOURCE)
    with resource.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("recruitment MVP rules must be a JSON object")
    return cast(dict[str, object], data)


def rule_version() -> str:
    """Return the rule package version."""

    value = load_recruitment_mvp_rules().get("version")
    if not isinstance(value, str) or not value:
        raise ValueError("recruitment MVP rules version must be a non-empty string")
    return value


def protected_attribute_fields() -> frozenset[str]:
    """Return protected attributes that must not participate in scoring."""

    fairness = _mapping(load_recruitment_mvp_rules().get("fairness"), "fairness")
    fields = fairness.get("protected_attribute_fields")
    if not isinstance(fields, list) or not all(isinstance(item, str) for item in fields):
        raise ValueError("fairness.protected_attribute_fields must be a string list")
    return frozenset(fields)


def skill_keywords() -> tuple[str, ...]:
    """Return skill keywords used by the deterministic report summary."""

    matching = _mapping(load_recruitment_mvp_rules().get("matching"), "matching")
    keywords = matching.get("skill_keywords")
    if not isinstance(keywords, list) or not all(isinstance(item, str) for item in keywords):
        raise ValueError("matching.skill_keywords must be a string list")
    return tuple(keywords)


def workflow_node_names() -> tuple[str, ...]:
    """Return Dify-equivalent workflow node names for evidence and reporting."""

    nodes = load_recruitment_mvp_rules().get("workflow_nodes")
    if not isinstance(nodes, list) or not all(isinstance(item, str) for item in nodes):
        raise ValueError("workflow_nodes must be a string list")
    return tuple(nodes)


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a JSON object")
    return value
