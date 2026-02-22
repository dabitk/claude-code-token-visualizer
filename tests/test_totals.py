import unittest

from cctv.aggregate.totals import apply_usage_to_totals
from cctv.domain.models import RequestUsage


class TotalsTest(unittest.TestCase):
    def test_apply_usage_to_totals_accumulates_cost(self) -> None:
        totals: dict = {}
        usage = RequestUsage(
            event_id="1",
            timestamp_ms=1,
            model="sonnet",
            input_tokens=1_000_000,
            output_tokens=0,
        )
        pricing = {"sonnet": {"input": 3.0, "output": 15.0}}

        apply_usage_to_totals(totals, usage, pricing)

        self.assertEqual(totals["sonnet"].input_tokens, 1_000_000)
        self.assertEqual(totals["sonnet"].cost_usd, 3.0)
        self.assertEqual(totals["sonnet"].last_request_cache_hit_rate, 0.0)
        self.assertEqual(totals["sonnet"].cumulative_cache_hit_rate, 0.0)

    def test_apply_usage_to_totals_cache_rates(self) -> None:
        totals: dict = {}
        usage = RequestUsage(
            event_id="2",
            timestamp_ms=1,
            model="sonnet",
            input_tokens=100,
            output_tokens=0,
            cache_read_input_tokens=900,
        )
        pricing = {"sonnet": {"input": 3.0, "output": 15.0}}

        apply_usage_to_totals(totals, usage, pricing)

        self.assertAlmostEqual(totals["sonnet"].last_request_cache_hit_rate or 0.0, 0.9, places=4)
        self.assertAlmostEqual(totals["sonnet"].cumulative_cache_hit_rate or 0.0, 0.9, places=4)


if __name__ == "__main__":
    unittest.main()
