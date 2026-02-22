from __future__ import annotations

import os
from pathlib import Path

try:
    from platformdirs import user_data_dir
except ImportError:  # pragma: no cover
    def user_data_dir(appname: str, appauthor: str) -> str:
        return str(Path.home() / ".local" / "share" / appname)


def default_usage_roots() -> list[Path]:
    env = os.getenv("CCTV_USAGE_GLOB")
    if env:
        return [Path(p).expanduser() for p in env.split(":") if p]

    candidates = [
        Path.home() / ".claude",
        Path(user_data_dir("claude", "anthropic")),
        Path(user_data_dir("claude-code", "anthropic")),
    ]
    existing: list[Path] = []
    for c in candidates:
        if c.exists():
            existing.append(c)
    return existing or [Path.home() / ".claude"]
