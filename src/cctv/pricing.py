from __future__ import annotations

import json
from pathlib import Path

DEFAULT_PRICING_PER_MILLION = {
    # Claude 4.x (exact model IDs)
    "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
    "claude-opus-4-5": {"input": 15.0, "output": 75.0},
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
    "claude-haiku-4-5": {"input": 0.8, "output": 4.0},
    # Claude 3.x (exact model IDs)
    "claude-3-5-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku": {"input": 0.8, "output": 4.0},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    "claude-3-opus": {"input": 15.0, "output": 75.0},
    "claude-3-sonnet": {"input": 3.0, "output": 15.0},
    # Fallback aliases (substring match용)
    "sonnet": {"input": 3.0, "output": 15.0},
    "haiku": {"input": 0.8, "output": 4.0},
    "opus": {"input": 15.0, "output": 75.0},
}


def load_pricing(path: str | None) -> dict[str, dict[str, float]]:
    if not path:
        return DEFAULT_PRICING_PER_MILLION
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"[cctv] Cannot load pricing file {path!r}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"[cctv] Pricing file must be a JSON object, got {type(data).__name__}")
    return data


def model_price(pricing: dict[str, dict[str, float]], model: str) -> tuple[float, float]:
    lower = model.lower()
    if lower in pricing:
        p = pricing[lower]
        return float(p.get("input", 0.0)), float(p.get("output", 0.0))
    for key, p in pricing.items():
        if key in lower:
            return float(p.get("input", 0.0)), float(p.get("output", 0.0))
    return 0.0, 0.0
