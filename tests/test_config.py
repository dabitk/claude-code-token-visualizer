import os
import unittest

from cctv.config import parse_args


class ConfigTest(unittest.TestCase):
    def test_parse_args_reads_cctv_prefix(self) -> None:
        old_bucket = os.environ.get("CCTV_BUCKET_SECONDS")
        old_window = os.environ.get("CCTV_WINDOW_SIZE")
        try:
            os.environ["CCTV_BUCKET_SECONDS"] = "1m"
            os.environ["CCTV_WINDOW_SIZE"] = "50"
            cfg = parse_args([])
        finally:
            if old_bucket is None:
                os.environ.pop("CCTV_BUCKET_SECONDS", None)
            else:
                os.environ["CCTV_BUCKET_SECONDS"] = old_bucket
            if old_window is None:
                os.environ.pop("CCTV_WINDOW_SIZE", None)
            else:
                os.environ["CCTV_WINDOW_SIZE"] = old_window

        self.assertEqual(cfg.bucket_seconds, 60)
        self.assertEqual(cfg.window_size, 50)


if __name__ == "__main__":
    unittest.main()
