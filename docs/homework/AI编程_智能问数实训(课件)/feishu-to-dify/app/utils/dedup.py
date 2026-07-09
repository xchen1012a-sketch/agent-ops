"""In-memory message deduplication with TTL."""

from __future__ import annotations

import time
from threading import Lock


class MessageDeduper:
    """Track processed message_id values to avoid duplicate Dify invocations."""

    def __init__(self, ttl_seconds: int = 600) -> None:
        self._ttl = ttl_seconds
        self._seen: dict[str, float] = {}
        self._lock = Lock()

    def _purge_expired(self, now: float) -> None:
        expired = [key for key, ts in self._seen.items() if now - ts > self._ttl]
        for key in expired:
            self._seen.pop(key, None)

    def is_duplicate(self, msgid: str) -> bool:
        return not self.try_acquire(msgid)

    def try_acquire(self, msgid: str) -> bool:
        """Return True only the first time a msgid is seen within TTL."""
        if not msgid:
            return True
        now = time.time()
        with self._lock:
            self._purge_expired(now)
            if msgid in self._seen:
                return False
            self._seen[msgid] = now
            return True

    def mark_seen(self, msgid: str) -> None:
        if not msgid:
            return
        with self._lock:
            self._seen[msgid] = time.time()

    def clear(self) -> None:
        with self._lock:
            self._seen.clear()
