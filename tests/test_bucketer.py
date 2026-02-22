import unittest
from collections import deque

from cctv.aggregate.bucketer import add_usage_to_buckets
from cctv.domain.models import BucketPoint, RequestUsage


class BucketerTest(unittest.TestCase):
    def test_add_usage_to_buckets_rolls_forward(self) -> None:
        buckets = deque([BucketPoint(start_ms=1_000)], maxlen=5)
        usage = RequestUsage(
            event_id="x",
            timestamp_ms=3_500,
            model="sonnet",
            input_tokens=7,
            output_tokens=2,
        )

        add_usage_to_buckets(buckets, usage, bucket_seconds=1)

        self.assertEqual(buckets[-1].start_ms, 3_000)
        self.assertEqual(buckets[-1].input_tokens, 7)
        self.assertEqual(buckets[-1].output_tokens, 2)


if __name__ == "__main__":
    unittest.main()
