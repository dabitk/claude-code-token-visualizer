# cctv — Claude Code Token Visualizer

A real-time terminal UI that visualizes token usage from your [Claude Code](https://claude.ai/code) sessions — input tokens, output tokens, cost, and cache hit rates — all as live histograms directly in your terminal.

---

## How it works

`cctv` does **not** intercept terminal output or wrap Claude Code.

Instead, it tails the `.jsonl` usage log files that Claude Code writes locally, parses each request event, aggregates them into time buckets, and renders the result as a live histogram.

```
Claude Code JSONL logs
        ↓
  RequestUsage events
        ↓
  Time-bucket aggregation
        ↓
  TUI histogram (Textual)
```

This design means `cctv` runs completely independently — open it in a second terminal alongside your Claude Code session.

---

## Features

- **Real-time histograms** — input and output token consumption per time bucket
- **Per-model cumulative stats** — total tokens, estimated cost in USD
- **Cache hit tracking** — per-request and cumulative cache hit rates
- **Dynamic Y-axis** — auto-scaling with "nice" tick marks
- **Configurable time window** — zoom in (1 s buckets) or zoom out (1 min buckets)
- **Custom pricing** — override default model prices with a JSON file
- **Zero dependencies on Claude Code internals** — reads only local log files

---

## Requirements

- Python 3.9+
- Claude Code installed and having run at least one session (to produce `.jsonl` logs)

---

## Installation

### From PyPI (recommended)

```bash
pip install claude-code-token-visualizer
```

or with pip3:

```bash
pip3 install claude-code-token-visualizer
```

### With pipx (isolated environment)

```bash
pipx install claude-code-token-visualizer
```

### From source

```bash
git clone https://github.com/dabitk/claude-code-token-visualizer.git
cd claude-code-token-visualizer
pip install -e .
```

---

## Quick Start

Open a second terminal while Claude Code is running:

```bash
cctv
```

That's it. `cctv` automatically discovers Claude Code's log directory and starts displaying token usage in real time.

**Navigation:**

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate menu |
| `Enter` | Select / toggle option |
| `q` | Quit |

---

## CLI Options

All options can also be set via environment variables (prefix `CCTV_`).

| Flag | Env var | Default | Description |
|------|---------|---------|-------------|
| `--bucket <N>` | `CCTV_BUCKET_SECONDS` | `10` | Time bucket width. Accepts `10`, `10s`, or `2m` |
| `--window <N>` | `CCTV_WINDOW_SIZE` | `120` | Number of buckets shown (total time = bucket × window) |
| `--refresh <N>` | `CCTV_REFRESH_SECONDS` | `1.0` | UI refresh interval in seconds |
| `--debounce-ms <N>` | `CCTV_DEBOUNCE_MS` | `250` | File-change debounce delay in milliseconds |
| `--pricing <path>` | `CCTV_PRICING_FILE` | built-in | Path to a custom pricing JSON file |
| `--hide-totals` | `CCTV_SHOW_TOTALS=0` | totals on | Hide the cumulative totals panel |
| `--hide-cache-hit` | `CCTV_SHOW_CACHE_HIT=0` | cache on | Hide cache hit rate columns |
| `--log-level <LEVEL>` | `CCTV_LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, …) |

### Examples

```bash
# 1-second buckets over a 3-minute window
cctv --bucket 1s --window 180

# 1-minute buckets, no cache stats
cctv --bucket 1m --hide-cache-hit

# Custom log directory
CCTV_USAGE_GLOB=~/.claude:~/work/.claude cctv
```

---

## Custom Pricing

By default, `cctv` uses built-in pricing for current Claude models. To override:

```bash
cctv --pricing my_pricing.json
```

The file must be a JSON object mapping model name substrings to per-million-token prices:

```json
{
  "claude-sonnet-4-6": { "input": 3.0,  "output": 15.0 },
  "claude-opus-4-6":   { "input": 15.0, "output": 75.0 },
  "claude-haiku-4-5":  { "input": 0.8,  "output": 4.0  }
}
```

Matching is done by substring, so `"sonnet"` matches `"claude-3-5-sonnet-20241022"`.

---

## Log File Location

`cctv` searches for `.jsonl` usage files in the following directories (in order):

1. `~/.claude/`
2. `~/.local/share/claude/`
3. `~/.local/share/claude-code/`

To use a custom path, set `CCTV_USAGE_GLOB`:

```bash
CCTV_USAGE_GLOB=/custom/path/to/claude cctv
```

Multiple paths can be separated by `:`.

---

## Project Structure

```
src/cctv/
├── cli.py              # Entry point
├── config.py           # CLI argument parsing
├── paths.py            # Log directory discovery
├── pricing.py          # Model pricing database
│
├── domain/             # Data models & state
│   ├── models.py       # RequestUsage, BucketPoint, ModelTotal, AppState
│   ├── events.py       # Event types
│   └── state.py        # StateStore
│
├── ingest/             # Data collection
│   ├── locator.py      # Find .jsonl files
│   ├── tailer.py       # Incremental file reader
│   ├── parser.py       # JSON → RequestUsage
│   └── dedupe.py       # Duplicate event filter
│
├── aggregate/          # Aggregation
│   ├── bucketer.py     # Time-bucket aggregation
│   └── totals.py       # Per-model cumulative stats
│
├── monitor/            # File monitoring
│   ├── watcher.py      # Watchdog-based file observer
│   └── scheduler.py    # Debounce scheduler
│
├── tui/                # Terminal UI (Textual)
│   ├── app.py          # Main Textual app
│   ├── widgets.py      # Custom widgets
│   └── render.py       # Histogram renderer
│
└── util/               # Utilities
    ├── time.py
    ├── math.py
    └── logging.py
```

---

## Contributing

Contributions are welcome. Please open an issue first for significant changes.

```bash
# Install dev dependencies and run tests
pip install -e ".[dev]"
pytest tests/
```

---

## License

[MIT](LICENSE)
