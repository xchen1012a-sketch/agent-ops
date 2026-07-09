"""Load shop_db schema from the course SQL dump and project it to the whitelist.

The data-query agent binds the course e-commerce schema (``shop_db_export.sql``)
via the ``SHOP_SCHEMA_PATH`` setting. Because the SQL dump covers the full star
schema (dim_* / fact_*), but the agent's SQL whitelist only allows the two
wide fact tables, this loader filters the schema description to the whitelisted
tables so the NL2SQL prompt stays focused and token-cheap.

The output is plain MySQL DDL: it is the most faithful schema description for
the LLM and avoids re-deriving a parallel schema document that would drift
from the source of truth.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from data_query_agent.domain.policies.sql_whitelist import SqlWhitelistSource

_CREATE_TABLE_RE = re.compile(
    r"CREATE TABLE\s+`(?P<name>[^`]+)`\s*\((?P<body>.*?)\)\s*ENGINE=.*?;",
    re.DOTALL | re.IGNORECASE,
)


class ShopSchemaLoader:
    """Read the shop_db SQL dump once and project it onto the whitelist."""

    def __init__(self, schema_path: str, whitelist: SqlWhitelistSource) -> None:
        self._schema_path = schema_path
        self._whitelist = whitelist

    @lru_cache(maxsize=1)
    def load_schema_description(self) -> str:
        """Return focused DDL for whitelisted tables, or an empty string."""
        if not self._schema_path:
            return ""
        path = Path(self._schema_path)
        if not path.exists():
            return ""
        raw_sql = path.read_text(encoding="utf-8", errors="replace")
        allowed = set(self._whitelist.allowed_tables)
        blocks: list[str] = []
        for match in _CREATE_TABLE_RE.finditer(raw_sql):
            table_name = match.group("name")
            if table_name not in allowed:
                continue
            body = match.group("body").strip()
            blocks.append(f"CREATE TABLE `{table_name}` (\n{body}\n);")
        return "\n\n".join(blocks)
