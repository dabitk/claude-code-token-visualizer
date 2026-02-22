import unittest
from collections import deque

from cctv.domain.models import BucketPoint
from cctv.domain.state import StateStore


class StateTimeScaleTest(unittest.TestCase):
    def test_advance_time_shifts_window(self) -> None:
        store = StateStore(window_size=3)
        store.state.buckets = deque(
            [BucketPoint(start_ms=0), BucketPoint(start_ms=1000), BucketPoint(start_ms=2000)],
            maxlen=3,
        )

        store.advance_time(now_ms=5000, bucket_seconds=1)

        starts = [b.start_ms for b in store.state.buckets]
        self.assertEqual(starts, [3000, 4000, 5000])

    def test_scale_uses_nice_steps(self) -> None:
        store = StateStore(window_size=3)
        self.assertEqual(store._next_scale(424), 450)
        self.assertEqual(store._next_scale(1010), 1200)


if __name__ == "__main__":
    unittest.main()
