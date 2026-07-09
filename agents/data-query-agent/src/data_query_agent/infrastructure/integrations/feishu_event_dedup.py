"""Feishu event de-duplication store: at-least-once delivery guard.

飞书事件可能重复投递。生产用 Redis SETNX+TTL 做跨进程/跨副本去重（阿里云多 worker
下进程内 set 会漏判）；离线测试用进程内实现。
"""

from __future__ import annotations

from typing import Protocol

from data_query_agent.infrastructure.integrations.feishu_client import RedisLike


class FeishuEventDedupStore(Protocol):
    """Boundary that records an event id and reports prior delivery."""

    async def is_duplicate(self, event_id: str) -> bool:
        """Mark the id as seen and return whether it was already seen."""


class RedisFeishuEventDedupStore(FeishuEventDedupStore):
    """Redis SETNX-based dedup with TTL; safe across workers and restarts."""

    def __init__(self, redis: RedisLike, *, ttl_seconds: int, key_prefix: str = "feishu:event:") -> None:
        self._redis = redis
        self._ttl_seconds = ttl_seconds
        self._key_prefix = key_prefix

    async def is_duplicate(self, event_id: str) -> bool:
        created = await self._redis.set(
            f"{self._key_prefix}{event_id}", "1", ex=self._ttl_seconds, nx=True
        )
        return not created


class InMemoryFeishuEventDedupStore(FeishuEventDedupStore):
    """Process-local dedup. Fallback/testing only; unsafe across workers."""

    def __init__(self) -> None:
        self._seen: set[str] = set()

    async def is_duplicate(self, event_id: str) -> bool:
        if event_id in self._seen:
            return True
        self._seen.add(event_id)
        return False
