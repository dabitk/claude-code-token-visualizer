from __future__ import annotations

from collections import deque
import math

from cctv.aggregate.bucketer import add_usage_to_buckets, advance_buckets_to_time
from cctv.aggregate.totals import apply_usage_to_totals
from cctv.domain.models import AppState, BucketPoint, RequestUsage
from cctv.util.math import nice_step


class StateStore:
    def __init__(self, window_size: int, scale_max: int = 100) -> None:
        self.state = AppState(
            buckets=deque(maxlen=window_size),
            scale_input_max=scale_max,
            scale_output_max=scale_max,
        )

    def apply_usage(self, usage: RequestUsage, bucket_seconds: int, price_per_million: dict[str, float]) -> None:
        add_usage_to_buckets(self.state.buckets, usage, bucket_seconds)
        apply_usage_to_totals(self.state.totals_by_model, usage, price_per_million)
        if usage.input_tokens > self.state.scale_input_max:
            self.state.scale_input_max = self._next_scale(usage.input_tokens)
        if usage.output_tokens > self.state.scale_output_max:
            self.state.scale_output_max = self._next_scale(usage.output_tokens)

    def max_bucket_values(self) -> tuple[int, int]:
        if not self.state.buckets:
            return 0, 0
        max_input = max(b.input_tokens for b in self.state.buckets)
        max_output = max(b.output_tokens for b in self.state.buckets)
        return max_input, max_output

    def maybe_rescale(self) -> None:
        peak_input, peak_output = self.max_bucket_values()
        if peak_input > self.state.scale_input_max:
            self.state.scale_input_max = self._next_scale(peak_input)
        if peak_output > self.state.scale_output_max:
            self.state.scale_output_max = self._next_scale(peak_output)

    def advance_time(self, now_ms: int, bucket_seconds: int) -> None:
        advance_buckets_to_time(self.state.buckets, now_ms, bucket_seconds)

    def _next_scale(self, peak: int) -> int:
        target = max(100, int(math.ceil(peak * 1.05)))
        step = nice_step(target / 10)
        return int(math.ceil(target / step) * step)
