from __future__ import annotations

from dataclasses import dataclass, field
from typing import Deque, Dict


@dataclass(frozen=True)
class RequestUsage:
    event_id: str
    timestamp_ms: int
    model: str
    input_tokens: int
    output_tokens: int
    cache_hit: bool | None = None
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0

    @property
    def request_cache_hit_rate(self) -> float | None:
        denom = self.input_tokens + self.cache_read_input_tokens
        if denom <= 0:
            return None
        return self.cache_read_input_tokens / denom


@dataclass
class BucketPoint:
    start_ms: int
    input_tokens: int = 0
    output_tokens: int = 0
    count: int = 0


@dataclass
class ModelTotal:
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    cache_hit_count: int = 0
    cache_total_count: int = 0
    cache_read_input_tokens_total: int = 0
    uncached_input_tokens_total: int = 0
    last_request_cache_hit_rate: float | None = None

    @property
    def token_total(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def cache_hit_rate(self) -> float | None:
        if self.cache_total_count == 0:
            return None
        return self.cache_hit_count / self.cache_total_count

    @property
    def cumulative_cache_hit_rate(self) -> float | None:
        denom = self.uncached_input_tokens_total + self.cache_read_input_tokens_total
        if denom <= 0:
            return None
        return self.cache_read_input_tokens_total / denom


@dataclass
class UiConfig:
    bucket_seconds: int = 10
    window_size: int = 120
    refresh_seconds: float = 1.0
    show_totals: bool = True
    show_cache_hit: bool = True


@dataclass
class AppState:
    buckets: Deque[BucketPoint]
    totals_by_model: Dict[str, ModelTotal] = field(default_factory=dict)
    scale_input_max: int = 100
    scale_output_max: int = 100
