from __future__ import annotations

from pathlib import Path


def find_usage_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.jsonl"):
            # Claude session logs are often UUID-named jsonl files under projects/.
            # Keep history for fallback and let parser filter non-usage records.
            files.append(path)
    return sorted(set(files))
