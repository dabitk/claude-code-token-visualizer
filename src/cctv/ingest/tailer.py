from __future__ import annotations

from pathlib import Path

# Cap per-tick reads to prevent OOM on large session files.
_MAX_BYTES_PER_READ = 4 * 1024 * 1024  # 4 MB


class JsonlTailer:
    def __init__(self) -> None:
        self._offsets: dict[Path, int] = {}

    def read_new_lines(self, path: Path) -> list[str]:
        if not path.exists():
            self._offsets.pop(path, None)
            return []

        last = self._offsets.get(path, 0)
        size = path.stat().st_size
        if size < last:
            last = 0

        with path.open("r", encoding="utf-8", errors="replace") as f:
            f.seek(last)
            chunk = f.read(_MAX_BYTES_PER_READ)
            self._offsets[path] = f.tell()

        return [line.strip() for line in chunk.splitlines() if line.strip()]
