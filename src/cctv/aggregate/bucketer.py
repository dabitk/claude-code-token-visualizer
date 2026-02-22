from __future__ import annotations

from collections import deque
from typing import Deque

from cctv.domain.models import BucketPoint, RequestUsage
from cctv.util.time import floor_to_bucket_ms


def add_usage_to_buckets(buckets: Deque[BucketPoint], usage: RequestUsage, bucket_seconds: int) -> None:
    bucket_ms = floor_to_bucket_ms(usage.timestamp_ms, bucket_seconds)

    if not buckets:
        buckets.append(BucketPoint(start_ms=bucket_ms))

    if bucket_ms < buckets[0].start_ms:
        return

    while buckets and bucket_ms > buckets[-1].start_ms:
        next_start = buckets[-1].start_ms + bucket_seconds * 1000
        buckets.append(BucketPoint(start_ms=next_start))

    if not buckets:
        buckets.append(BucketPoint(start_ms=bucket_ms))

    target = buckets[-1]
    if target.start_ms != bucket_ms:
        for point in buckets:
            if point.start_ms == bucket_ms:
                target = point
                break

    target.input_tokens += usage.input_tokens
    target.output_tokens += usage.output_tokens
    target.count += 1


def empty_buckets(window_size: int, now_bucket_ms: int, bucket_seconds: int) -> Deque[BucketPoint]:
    points = deque(maxlen=window_size)
    start = now_bucket_ms - (window_size - 1) * bucket_seconds * 1000
    for i in range(window_size):
        points.append(BucketPoint(start_ms=start + i * bucket_seconds * 1000))
    return points


def advance_buckets_to_time(buckets: Deque[BucketPoint], now_ms: int, bucket_seconds: int) -> None:
    if not buckets:
        return
    bucket_ms = bucket_seconds * 1000
    now_bucket = floor_to_bucket_ms(now_ms, bucket_seconds)
    while buckets and buckets[-1].start_ms < now_bucket:
        buckets.append(BucketPoint(start_ms=buckets[-1].start_ms + bucket_ms))
