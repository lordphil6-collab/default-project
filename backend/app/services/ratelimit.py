"""Abuse protection for public endpoints (Phase A).

In-memory sliding window — correct for single-process pilot/dev. Behind
multiple workers move to Redis (same interface: allowed(key) -> bool).
"""
import time
from collections import deque


class RateLimiter:
    def __init__(self, limit: int = 20, window_s: int = 60):
        self.limit = limit
        self.window_s = window_s
        self._hits: dict[str, deque] = {}

    def allowed(self, key: str, now: float | None = None) -> bool:
        now = now if now is not None else time.time()
        q = self._hits.setdefault(key, deque())
        while q and q[0] <= now - self.window_s:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True

    def reset(self, key: str) -> None:
        self._hits.pop(key, None)
