from __future__ import annotations

from collections import deque


class DedupeCache:
    def __init__(self, max_size: int = 50_000) -> None:
        self._seen: set[str] = set()
        self._queue: deque[str] = deque()
        self._max_size = max_size

    def add_if_new(self, event_id: str) -> bool:
        if event_id in self._seen:
            return False
        self._seen.add(event_id)
        self._queue.append(event_id)
        if len(self._queue) > self._max_size:
            old = self._queue.popleft()
            self._seen.discard(old)
        return True
