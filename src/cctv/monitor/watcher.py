from __future__ import annotations

from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver


class _Handler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[Path], None]) -> None:
        super().__init__()
        self._callback = callback

    def on_any_event(self, event: FileSystemEvent) -> None:
        if getattr(event, "is_directory", False):
            return
        p = Path(event.src_path)
        if p.suffix == ".jsonl":
            self._callback(p)


class UsageWatcher:
    def __init__(self, roots: list[Path], on_change: Callable[[Path], None]) -> None:
        self._roots = roots
        self._on_change = on_change
        self._observer: Observer | None = None

    def start(self) -> None:
        handler = _Handler(self._on_change)
        # Try native observer first (FSEvents on macOS, inotify on Linux).
        # Fall back to polling if the native backend fails to start.
        observer: Observer = Observer()
        try:
            for root in self._roots:
                if root.exists():
                    observer.schedule(handler, str(root), recursive=True)
            observer.start()
            self._observer = observer
            return
        except Exception:
            observer.stop()
            observer.join(timeout=1.0)

        fallback = PollingObserver()
        for root in self._roots:
            if root.exists():
                fallback.schedule(handler, str(root), recursive=True)
        fallback.start()
        self._observer = fallback

    def stop(self) -> None:
        if self._observer is None:
            return
        self._observer.stop()
        self._observer.join(timeout=1.0)
        self._observer = None
