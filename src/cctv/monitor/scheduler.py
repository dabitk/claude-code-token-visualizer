from __future__ import annotations

from cctv.util.time import now_ms


class DebouncedRunner:
    def __init__(self, debounce_ms: int) -> None:
        self.debounce_ms = debounce_ms
        self.dirty = True
        self._last_dirty_ms = 0

    def mark_dirty(self) -> None:
        self.dirty = True
        self._last_dirty_ms = now_ms()

    def should_run(self) -> bool:
        if not self.dirty:
            return False
        elapsed = now_ms() - self._last_dirty_ms
        if self._last_dirty_ms == 0:
            return True
        return elapsed >= self.debounce_ms

    def mark_clean(self) -> None:
        self.dirty = False
