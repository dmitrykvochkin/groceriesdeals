"""Scroll the current Android page and collect joined ViewGroup text."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from groceriesdeals.joined_text import collect_joined_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scroll the current Android page to its end and write a JSON array "
            "containing only unique joined ViewGroup text strings."
        )
    )
    parser.add_argument(
        "--serial",
        help="ADB device serial, for example 127.0.0.1:6555",
    )
    parser.add_argument(
        "--package",
        default="com.picnic.android",
        help=(
            "Only include ViewGroups from this package "
            "(default: com.picnic.android; use 'all' for every package)"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("joined_text.json"),
        help="Output JSON file (default: joined_text.json)",
    )
    parser.add_argument(
        "--max-scrolls",
        type=int,
        default=100,
        help="Safety limit for swipe attempts (default: 100)",
    )
    parser.add_argument(
        "--unchanged-limit",
        type=int,
        default=2,
        help="Stop after this many unchanged post-scroll screens (default: 2)",
    )
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=1.0,
        help="Delay after each swipe (default: 1.0)",
    )
    parser.add_argument(
        "--swipe-scale",
        type=float,
        default=0.8,
        help="Fraction of screen height used for each upward swipe (default: 0.8)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=100,
        help="Maximum hierarchy depth requested from uiautomator2 (default: 100)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.max_scrolls < 0:
        raise SystemExit("--max-scrolls must be at least 0")
    if args.unchanged_limit < 1:
        raise SystemExit("--unchanged-limit must be at least 1")
    if args.settle_seconds < 0:
        raise SystemExit("--settle-seconds must be at least 0")
    if not 0 < args.swipe_scale <= 1:
        raise SystemExit("--swipe-scale must be greater than 0 and at most 1")

    try:
        import uiautomator2 as u2
    except ImportError:
        print(
            "uiautomator2 is required. Install it with: "
            "python -m pip install uiautomator2",
            file=sys.stderr,
        )
        return 2

    package = None if args.package.casefold() == "all" else args.package
    device = u2.connect(args.serial) if args.serial else u2.connect()

    joined_text = collect_joined_text(
        device=device,
        package=package,
        max_depth=args.max_depth,
        max_scrolls=args.max_scrolls,
        unchanged_limit=args.unchanged_limit,
        settle_seconds=args.settle_seconds,
        swipe_scale=args.swipe_scale,
        progress=lambda message: print(message, file=sys.stderr),
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(joined_text, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        f"wrote {len(joined_text)} unique joined text value(s) to "
        f"{args.output.resolve()}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
