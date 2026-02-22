from __future__ import annotations

from cctv.domain.models import ModelTotal, RequestUsage
from cctv.pricing import model_price


def apply_usage_to_totals(
    totals_by_model: dict[str, ModelTotal], usage: RequestUsage, pricing: dict[str, dict[str, float]]
) -> None:
    total = totals_by_model.get(usage.model)
    if total is None:
        total = ModelTotal(model=usage.model)
        totals_by_model[usage.model] = total

    total.input_tokens += usage.input_tokens
    total.output_tokens += usage.output_tokens
    total.uncached_input_tokens_total += usage.input_tokens
    total.cache_read_input_tokens_total += usage.cache_read_input_tokens
    total.last_request_cache_hit_rate = usage.request_cache_hit_rate

    in_rate, out_rate = model_price(pricing, usage.model)
    total.cost_usd += (usage.input_tokens / 1_000_000) * in_rate
    total.cost_usd += (usage.output_tokens / 1_000_000) * out_rate

    if usage.cache_hit is not None:
        total.cache_total_count += 1
        if usage.cache_hit:
            total.cache_hit_count += 1
