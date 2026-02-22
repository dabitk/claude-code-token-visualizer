from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from cctv.domain.models import RequestUsage
from cctv.util.time import now_ms


INPUT_KEYS = ["input_tokens", "input", "prompt_tokens", "inputTokenCount"]
OUTPUT_KEYS = ["output_tokens", "output", "completion_tokens", "outputTokenCount"]
TS_KEYS = ["timestamp_ms", "timestamp", "created_at_ms", "created_at"]
MODEL_KEYS = ["model", "model_name", "modelId"]
CACHE_KEYS = ["cache_hit", "prompt_cache_hit", "cacheHit"]
ID_KEYS = ["event_id", "request_id", "id"]


def _nested_get(rec: dict[str, Any], path: tuple[str, ...]) -> Any | None:
    cur: Any = rec
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def _pick_int(rec: dict[str, Any], keys: list[str], default: int = 0) -> int:
    for k in keys:
        if k in rec and rec[k] is not None:
            try:
                return int(rec[k])
            except (TypeError, ValueError):
                continue
    return default


def _pick_str(rec: dict[str, Any], keys: list[str], default: str = "unknown") -> str:
    for k in keys:
        if k in rec and rec[k] is not None:
            return str(rec[k])
    return default


def _pick_bool(rec: dict[str, Any], keys: list[str]) -> bool | None:
    for k in keys:
        if k in rec:
            val = rec[k]
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.lower() in {"1", "true", "yes", "on"}
            if isinstance(val, (int, float)):
                return bool(val)
    return None


def _parse_timestamp_ms(val: Any) -> int:
    if val is None:
        return now_ms()
    if isinstance(val, (int, float)):
        ts = int(val)
        return ts * 1000 if ts < 10_000_000_000 else ts
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return now_ms()
        if s.isdigit():
            ts = int(s)
            return ts * 1000 if ts < 10_000_000_000 else ts
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            return int(dt.timestamp() * 1000)
        except ValueError:
            return now_ms()
    return now_ms()


def parse_usage_line(line: str) -> RequestUsage | None:
    try:
        rec = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(rec, dict):
        return None

    usage_obj = _nested_get(rec, ("message", "usage"))
    usage_rec = usage_obj if isinstance(usage_obj, dict) else rec

    input_tokens = _pick_int(usage_rec, INPUT_KEYS)
    output_tokens = _pick_int(usage_rec, OUTPUT_KEYS)
    if input_tokens == 0 and output_tokens == 0:
        return None

    ts_ms = _parse_timestamp_ms(_pick_str(rec, TS_KEYS, default=str(now_ms())))

    event_id = _pick_str(rec, ID_KEYS, default="")
    if not event_id:
        event_id = _pick_str(rec, ["uuid", "requestId", "messageId"], default="")
    if not event_id:
        digest = hashlib.sha1(line.encode("utf-8")).hexdigest()
        event_id = digest

    model = _pick_str(rec, MODEL_KEYS, default="")
    if not model:
        model = _pick_str(usage_rec, MODEL_KEYS, default="")
    if not model:
        nested_model = _nested_get(rec, ("message", "model"))
        model = str(nested_model) if nested_model else "unknown"

    cache_hit = _pick_bool(rec, CACHE_KEYS)
    cache_read_input_tokens = _pick_int(usage_rec, ["cache_read_input_tokens"], default=0)
    cache_creation_input_tokens = _pick_int(usage_rec, ["cache_creation_input_tokens"], default=0)
    if cache_hit is None:
        cache_hit = cache_read_input_tokens > 0

    return RequestUsage(
        event_id=event_id,
        timestamp_ms=ts_ms,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_hit=cache_hit,
        cache_read_input_tokens=cache_read_input_tokens,
        cache_creation_input_tokens=cache_creation_input_tokens,
    )
