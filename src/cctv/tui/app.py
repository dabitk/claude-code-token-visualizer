from __future__ import annotations

from collections import deque
from dataclasses import replace
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.events import Resize
from textual.timer import Timer
from textual.widgets import Static

from cctv.aggregate.bucketer import empty_buckets
from cctv.config import AppConfig
from cctv.domain.state import StateStore
from cctv.ingest.dedupe import DedupeCache
from cctv.ingest.locator import find_usage_files
from cctv.ingest.parser import parse_usage_line
from cctv.ingest.tailer import JsonlTailer
from cctv.monitor.scheduler import DebouncedRunner
from cctv.monitor.watcher import UsageWatcher
from cctv.tui.render import render_histogram_grid
from cctv.tui.widgets import HintsWidget, HistogramWidget, NavWidget, StatusLineWidget
from cctv.util.time import floor_to_bucket_ms, now_ms


class CctvApp(App):
    CSS = """
    Screen { layout: vertical; }
    #top { height: 3fr; }
    #bottom { height: 3fr; }
    #status { height: auto; min-height: 1; }
    #nav { height: 2fr; min-height: 5; border: round green; }
    #hints { height: 1; color: $text-muted; }
    """

    BINDINGS = [
        ("up", "nav_up", "Move Up"),
        ("down", "nav_down", "Move Down"),
        ("enter", "nav_select", "Select"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, config: AppConfig, pricing: dict[str, dict[str, float]], roots: list[Path]) -> None:
        super().__init__()
        # Use replace() to avoid mutating the caller's config object.
        self.config = replace(
            config,
            bucket_seconds=max(1, int(round(config.refresh_seconds))),
        )
        self.pricing = pricing
        self.roots = roots
        now_bucket = floor_to_bucket_ms(now_ms(), self.config.bucket_seconds)
        buckets = empty_buckets(self.config.window_size, now_bucket, self.config.bucket_seconds)
        self.store = StateStore(window_size=self.config.window_size)
        self.store.state.buckets = buckets
        self.dedupe = DedupeCache()
        self.tailer = JsonlTailer()
        self.scheduler = DebouncedRunner(self.config.debounce_ms)
        self.refresh_options = deque([1.0, 10.0, 60.0])
        # _known_files: all discovered .jsonl paths.
        # _pending_files: files flagged by watchdog since last tick.
        self._known_files: set[Path] = set()
        self._pending_files: set[Path] = set()
        self.watcher = UsageWatcher(roots, self._on_file_changed)
        self._timer: Timer | None = None
        self.nav_selected_idx = 0
        self._last_file_scan_ms = 0
        self._file_scan_interval_ms = 30_000  # full rescan every 30s

    def _on_file_changed(self, path: Path) -> None:
        self._known_files.add(path)
        self._pending_files.add(path)
        self.scheduler.mark_dirty()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield HistogramWidget("Input tokens / bucket", id="top")
            yield HistogramWidget("Output tokens / bucket", id="bottom")
            yield StatusLineWidget(id="status")
            yield NavWidget(id="nav")
            yield HintsWidget(id="hints")

    def on_mount(self) -> None:
        # One-time full scan; watchdog events keep the set up-to-date after this.
        discovered = set(find_usage_files(self.roots))
        self._known_files = discovered
        self._pending_files = discovered.copy()
        self._last_file_scan_ms = now_ms()
        self.watcher.start()
        self._timer = self.set_interval(self.config.refresh_seconds, self._tick)
        self._render_all()

    def on_unmount(self) -> None:
        self.watcher.stop()

    def on_resize(self, _: Resize) -> None:
        self._render_all()

    def action_cycle_refresh(self) -> None:
        self.refresh_options.rotate(-1)
        self.config.refresh_seconds = self.refresh_options[0]
        self.config.bucket_seconds = max(1, int(round(self.config.refresh_seconds)))
        if self._timer is not None:
            self._timer.stop()
        self._timer = self.set_interval(self.config.refresh_seconds, self._tick)
        now_bucket = floor_to_bucket_ms(now_ms(), self.config.bucket_seconds)
        self.store.state.buckets = empty_buckets(self.config.window_size, now_bucket, self.config.bucket_seconds)
        self.scheduler.mark_dirty()

    def action_toggle_totals(self) -> None:
        self.config.show_totals = not self.config.show_totals
        self._render_all()

    def action_toggle_cache(self) -> None:
        self.config.show_cache_hit = not self.config.show_cache_hit
        self._render_all()

    def action_nav_up(self) -> None:
        self.nav_selected_idx = (self.nav_selected_idx - 1) % 3
        self._render_all()

    def action_nav_down(self) -> None:
        self.nav_selected_idx = (self.nav_selected_idx + 1) % 3
        self._render_all()

    def action_nav_select(self) -> None:
        if self.nav_selected_idx == 0:
            self.action_cycle_refresh()
        elif self.nav_selected_idx == 1:
            self.action_toggle_totals()
        else:
            self.action_toggle_cache()
        self._render_all()

    def _tick(self) -> None:
        now = now_ms()

        # Periodic full rescan to discover files created before the watcher started
        # or missed due to timing. Much less frequent now that watchdog tracks changes.
        if (now - self._last_file_scan_ms) >= self._file_scan_interval_ms:
            rescanned = set(find_usage_files(self.roots))
            newly_found = rescanned - self._known_files
            self._known_files = rescanned
            self._pending_files.update(newly_found)
            self._last_file_scan_ms = now

        # Only clear dirty flag when it actually triggered the scan.
        if self.scheduler.should_run():
            self.scheduler.mark_clean()

        self.store.advance_time(now, self.config.bucket_seconds)

        # Drain pending files flagged by watchdog (or initial full scan).
        to_read = self._pending_files
        self._pending_files = set()
        for path in to_read:
            for line in self.tailer.read_new_lines(path):
                usage = parse_usage_line(line)
                if usage is None:
                    continue
                if not self.dedupe.add_if_new(usage.event_id):
                    continue
                self.store.apply_usage(usage, self.config.bucket_seconds, self.pricing)

        self.store.maybe_rescale()
        self._render_all()

    def _render_all(self) -> None:
        top = self.query_one("#top", HistogramWidget)
        bottom = self.query_one("#bottom", HistogramWidget)
        status = self.query_one("#status", Static)
        nav = self.query_one("#nav", NavWidget)

        input_scale = max(1, self.store.state.scale_input_max)
        output_scale = max(1, self.store.state.scale_output_max)
        top_body = render_histogram_grid(
            self.store.state.buckets,
            input_scale,
            mode="input",
            width=max(1, top.size.width),
            height=max(1, top.size.height - 1),
        )
        bottom_body = render_histogram_grid(
            self.store.state.buckets,
            output_scale,
            mode="output",
            width=max(1, bottom.size.width),
            height=max(1, bottom.size.height - 1),
        )
        top.set_content(top_body, input_scale)
        bottom.set_content(bottom_body, output_scale)

        if self.config.show_totals:
            lines: list[str] = ["Cumulative totals (session):"]
            for model, total in sorted(self.store.state.totals_by_model.items()):
                part = (
                    f"{model} | input tokens: {total.input_tokens} | "
                    f"output tokens: {total.output_tokens} | cost: ${total.cost_usd:.4f}"
                )
                if self.config.show_cache_hit:
                    req_cache = (
                        f"{total.last_request_cache_hit_rate*100:.1f}%"
                        if total.last_request_cache_hit_rate is not None
                        else "N/A"
                    )
                    cum_cache = (
                        f"{total.cumulative_cache_hit_rate*100:.1f}%"
                        if total.cumulative_cache_hit_rate is not None
                        else "N/A"
                    )
                    part += f" | req cache hit: {req_cache} | cumulative cache hit: {cum_cache}"
                lines.append(self._fit_line(part, max(1, status.size.width)))
            if len(lines) == 1:
                lines = ["No usage yet"]
            status.styles.height = len(lines)
            status.update("\n".join(lines))
        else:
            status.styles.height = 1
            status.update("Totals hidden")

        nav_options = [
            f"refresh interval: {self.config.refresh_seconds:g}s",
            f"totals: {'ON' if self.config.show_totals else 'OFF'}",
            f"cache-hit: {'ON' if self.config.show_cache_hit else 'OFF'}",
        ]
        nav_width = nav.size.width - 2
        if nav_width < 10:
            nav_width = max(10, self.size.width - 4)
        nav.set_options(
            nav_options,
            selected=self.nav_selected_idx,
            width=nav_width,
        )

    @staticmethod
    def _fit_line(text: str, width: int) -> str:
        if width <= 0:
            return ""
        if len(text) <= width:
            return text
        if width <= 1:
            return "…"
        return text[: width - 1] + "…"
