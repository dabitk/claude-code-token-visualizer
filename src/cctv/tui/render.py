from __future__ import annotations

import math
from typing import Iterable, Sequence

from cctv.domain.models import BucketPoint
from cctv.util.math import nice_step

FULL = "█"
GRID = "┈"


def _pick_values(buckets: Sequence[BucketPoint], mode: str) -> list[int]:
    if mode == "input":
        return [b.input_tokens for b in buckets]
    return [b.output_tokens for b in buckets]


def _downsample(values: Sequence[int], width: int) -> list[int]:
    if width <= 0:
        return []
    if not values:
        return [0] * width
    if len(values) <= width:
        pad = [0] * (width - len(values))
        return pad + list(values)

    chunk = len(values) / width
    out: list[int] = []
    for i in range(width):
        start = int(i * chunk)
        end = int((i + 1) * chunk)
        if end <= start:
            end = start + 1
        out.append(max(values[start:end]))
    return out


def _format_tokens(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}m"
    if value >= 1_000:
        v = value / 1_000
        if abs(v - int(v)) < 1e-9:
            return f"{int(v)}k"
        return f"{v:.1f}k"
    return str(value)


def _build_ticks(scale_max: int) -> list[int]:
    if scale_max <= 100:
        step = 10
    else:
        step = nice_step(scale_max / 10)
    ticks = list(range(step, scale_max + 1, step))
    if not ticks or ticks[-1] != scale_max:
        ticks.append(scale_max)
    return ticks


def _build_uniform_tick_rows(height: int, scale_max: int) -> dict[int, int]:
    if height <= 1:
        return {0: scale_max}
    max_lines = min(6, height)
    lines = max_lines
    while lines > 3 and (height - 1) % (lines - 1) != 0:
        lines -= 1
    if lines < 3:
        lines = min(3, height)

    row_step = (height - 1) / (lines - 1)
    val_step = scale_max / (lines - 1)
    out: dict[int, int] = {}
    for i in range(lines):
        row = int(round(i * row_step))
        val = int(round(scale_max - (i * val_step)))
        row = max(0, min(height - 1, row))
        out[row] = val
    return out


def render_histogram_grid(
    buckets: Iterable[BucketPoint],
    scale_max: int,
    mode: str,
    width: int,
    height: int,
) -> str:
    if width <= 0 or height <= 0:
        return ""
    bucket_list = list(buckets)
    values = _pick_values(bucket_list, mode)
    if scale_max <= 0:
        scale_max = 1

    # 8 chars label + separator + graph area
    label_width = 8
    if width <= label_width + 1:
        return ""
    graph_width = width - label_width - 1
    columns = _downsample(values, graph_width)
    # Keep bars proportional to current y-scale and panel height.
    # Using floor-like conversion avoids sticky 1-row bars after rescaling.
    bar_heights: list[int] = []
    for v in columns:
        h = min(height, max(0, int((v / scale_max) * height)))
        if v > 0 and h == 0:
            h = 1
        bar_heights.append(h)

    row_labels = _build_uniform_tick_rows(height, scale_max)

    rows: list[str] = []
    for r in range(height):
        threshold = height - r
        label_val = row_labels.get(r)
        label = _format_tokens(label_val) if label_val is not None else ""
        label = label.rjust(label_width)
        is_major = label_val is not None
        fill_char = GRID if is_major else " "
        line = "".join(FULL if h >= threshold else fill_char for h in bar_heights)
        rows.append(f"{label}│{line}")
    return "\n".join(rows)
