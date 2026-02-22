from __future__ import annotations

import time


def now_ms() -> int:
    return int(time.time() * 1000)


def floor_to_bucket_ms(ts_ms: int, bucket_seconds: int) -> int:
    bucket_ms = bucket_seconds * 1000
    return (ts_ms // bucket_ms) * bucket_ms
