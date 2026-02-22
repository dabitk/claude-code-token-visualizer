from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FileDirty:
    ts_ms: int


@dataclass(frozen=True)
class Tick:
    ts_ms: int


@dataclass(frozen=True)
class ResizeEvent:
    width: int
    height: int
