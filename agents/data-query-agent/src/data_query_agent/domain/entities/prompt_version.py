"""Domain entities for prompt version records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class PromptVersion:
    """Versioned prompt template metadata for data query workflows."""

    id: int | None
    public_id: str
    prompt_name: str
    version: str
    template_hash: str
    template_body: str
    variables_schema: str
    output_schema: str
    is_active: bool
    created_by_user_id: int
    created_at: datetime
