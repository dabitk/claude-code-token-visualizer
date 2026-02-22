from __future__ import annotations

from cctv.config import parse_args
from cctv.paths import default_usage_roots
from cctv.pricing import load_pricing
from cctv.util.logging import configure_logging


def main(argv: list[str] | None = None) -> None:
    config = parse_args(argv)
    configure_logging(config.log_level)
    pricing = load_pricing(config.pricing_path)
    roots = default_usage_roots()
    from cctv.tui.app import CctvApp
    app = CctvApp(config=config, pricing=pricing, roots=roots)
    app.run()


if __name__ == "__main__":
    main()
