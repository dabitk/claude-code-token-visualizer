from __future__ import annotations

import argparse
import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    bucket_seconds: int
    window_size: int
    refresh_seconds: float
    debounce_ms: int
    pricing_path: str | None
    show_totals: bool
    show_cache_hit: bool
    log_level: str


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _parse_bucket(raw: str) -> int:
    s = raw.strip().lower()
    if s.endswith("s"):
        return int(s[:-1])
    if s.endswith("m"):
        return int(s[:-1]) * 60
    return int(s)


def parse_args(argv: list[str] | None = None) -> AppConfig:
    parser = argparse.ArgumentParser(description="Claude Code token visualizer")
    parser.add_argument("--bucket", default=os.getenv("CCTV_BUCKET_SECONDS", "10"))
    parser.add_argument("--window", type=int, default=int(os.getenv("CCTV_WINDOW_SIZE", "120")))
    parser.add_argument("--refresh", type=float, default=float(os.getenv("CCTV_REFRESH_SECONDS", "1")))
    parser.add_argument("--debounce-ms", type=int, default=int(os.getenv("CCTV_DEBOUNCE_MS", "250")))
    parser.add_argument("--pricing", default=os.getenv("CCTV_PRICING_FILE"))
    parser.add_argument("--show-totals", action="store_true", default=_env_bool("CCTV_SHOW_TOTALS", True))
    parser.add_argument("--hide-totals", action="store_false", dest="show_totals")
    parser.add_argument("--show-cache-hit", action="store_true", default=_env_bool("CCTV_SHOW_CACHE_HIT", True))
    parser.add_argument("--hide-cache-hit", action="store_false", dest="show_cache_hit")
    parser.add_argument("--log-level", default=os.getenv("CCTV_LOG_LEVEL", "INFO"))
    args = parser.parse_args(argv)

    return AppConfig(
        bucket_seconds=_parse_bucket(str(args.bucket)),
        window_size=args.window,
        refresh_seconds=args.refresh,
        debounce_ms=args.debounce_ms,
        pricing_path=args.pricing,
        show_totals=args.show_totals,
        show_cache_hit=args.show_cache_hit,
        log_level=args.log_level,
    )
