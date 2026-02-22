import unittest

from cctv.ingest.parser import parse_usage_line


class ParserTest(unittest.TestCase):
    def test_parse_usage_line_happy_path(self) -> None:
        line = '{"event_id":"e1","timestamp_ms":1700000000000,"model":"sonnet","input_tokens":10,"output_tokens":3,"cache_hit":true}'
        usage = parse_usage_line(line)
        self.assertIsNotNone(usage)
        assert usage is not None
        self.assertEqual(usage.event_id, "e1")
        self.assertEqual(usage.model, "sonnet")
        self.assertEqual(usage.input_tokens, 10)
        self.assertEqual(usage.output_tokens, 3)
        self.assertTrue(usage.cache_hit)
        self.assertEqual(usage.cache_read_input_tokens, 0)
        self.assertEqual(usage.cache_creation_input_tokens, 0)

    def test_parse_usage_line_rejects_non_usage(self) -> None:
        usage = parse_usage_line('{"message":"hello"}')
        self.assertIsNone(usage)

    def test_parse_usage_line_nested_claude_session_record(self) -> None:
        line = (
            '{"type":"assistant","uuid":"u1","timestamp":"2026-02-21T06:49:42.972Z",'
            '"message":{"model":"claude-sonnet-4-6","usage":{"input_tokens":3,"output_tokens":1,'
            '"cache_read_input_tokens":17872}}}'
        )
        usage = parse_usage_line(line)
        self.assertIsNotNone(usage)
        assert usage is not None
        self.assertEqual(usage.event_id, "u1")
        self.assertEqual(usage.model, "claude-sonnet-4-6")
        self.assertEqual(usage.input_tokens, 3)
        self.assertEqual(usage.output_tokens, 1)
        self.assertTrue(usage.cache_hit)
        self.assertEqual(usage.cache_read_input_tokens, 17872)
        self.assertEqual(usage.cache_creation_input_tokens, 0)


if __name__ == "__main__":
    unittest.main()
