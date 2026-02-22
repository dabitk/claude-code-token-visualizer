from __future__ import annotations

from rich.text import Text
from textual.widgets import Static


class HistogramWidget(Static):
    def __init__(self, title: str, **kwargs) -> None:
        super().__init__("", **kwargs)
        self.title = title

    def set_content(self, body: str, scale_max: int) -> None:
        self.update(f"{self.title}  (y-max: {scale_max})\n{body}")


class StatusLineWidget(Static):
    pass


class NavWidget(Static):
    def set_options(self, options: list[str], selected: int, width: int) -> None:
        text = Text()
        for idx, opt in enumerate(options):
            prefix = "› " if idx == selected else "  "
            line = f"{prefix}{idx + 1}) {opt}"
            if len(line) > width:
                line = line[: max(1, width - 1)] + "…"
            line = line.ljust(width)
            if idx == selected:
                text.append(line, style="reverse bold")
            else:
                text.append(line)
            if idx < len(options) - 1:
                text.append("\n")
        self.update(text)


class HintsWidget(Static):
    HINTS = "  q  quit   ↑/↓  navigate   Enter  select"

    def on_mount(self) -> None:
        self.update(self.HINTS)
