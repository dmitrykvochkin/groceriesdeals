"""Navigate Picnic's selected category promotion screens."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import time
from typing import Any

from groceriesdeals.joined_text import collect_joined_text


PICNIC_PACKAGE = "com.picnic.android"

# Edit this list to control which categories are visited. Categories not in
# this list are ignored, even when they are visible under "Alle categorieën".
CATEGORIES = [
    "Fruit",
    "Aardappelen & groente",
    "Vlees & vis",
    "Vega & plantaardig",
    "Bakkerij",
    "Zuivel & eieren",
    "Kaas",
    "Pasta, rijst & wereldkeuken",
    "Diepvries",
    "Voorraadkast"
]


def case_insensitive_exact(value: str) -> str:
    return rf"(?i)^{re.escape(value)}$"


def label_selectors(device: Any, label: str) -> list[Any]:
    """Build selectors for labels exposed as text or content descriptions."""
    pattern = case_insensitive_exact(label)
    return [
        device(text=label),
        device(description=label),
        device(textMatches=pattern),
        device(descriptionMatches=pattern),
    ]


def find_label(device: Any, label: str) -> Any | None:
    for selector in label_selectors(device, label):
        if selector.exists:
            return selector
    return None


def wait_for_label(device: Any, label: str, timeout: float = 15.0) -> Any | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        selector = find_label(device, label)
        if selector is not None:
            return selector
        time.sleep(0.25)
    return None


def wait_for_stable_tree(
    device: Any,
    timeout: float = 15.0,
    stable_reads: int = 2,
) -> None:
    """Wait until consecutive accessibility hierarchy reads are identical."""
    deadline = time.monotonic() + timeout
    previous_xml: str | None = None
    unchanged = 0

    while time.monotonic() < deadline:
        xml = device.dump_hierarchy(compressed=False, pretty=False, max_depth=100)
        if xml == previous_xml:
            unchanged += 1
            if unchanged >= stable_reads:
                return
        else:
            unchanged = 0
            previous_xml = xml
        time.sleep(0.35)


def click_label(device: Any, label: str, timeout: float = 15.0) -> None:
    selector = wait_for_label(device, label, timeout)
    if selector is None:
        raise RuntimeError(f"Could not find {label!r}")
    selector.click()
    wait_for_stable_tree(device)


def scroll_to_label(
    device: Any,
    label: str,
    max_swipes: int = 20,
    swipe_scale: float = 0.65,
) -> Any | None:
    """Scroll down until a text/content-description label becomes visible."""
    previous_xml: str | None = None

    for _ in range(max_swipes + 1):
        selector = find_label(device, label)
        if selector is not None:
            return selector

        xml = device.dump_hierarchy(compressed=False, pretty=False, max_depth=100)
        if xml == previous_xml:
            return None
        previous_xml = xml

        device.swipe_ext("up", scale=swipe_scale)
        time.sleep(0.7)

    return None


def click_scrolled_label(
    device: Any,
    label: str,
    max_swipes: int = 20,
) -> bool:
    selector = scroll_to_label(device, label, max_swipes=max_swipes)
    if selector is None:
        return False
    selector.click()
    wait_for_stable_tree(device)
    return True


def click_top_left_back(device: Any) -> None:
    """Click Picnic's top-left Terug control, falling back to Android back."""
    selector = wait_for_label(device, "Terug", timeout=8.0)
    if selector is not None:
        selector.click()
    else:
        print(
            "warning: top-left 'Terug' was not exposed; using Android back",
            file=sys.stderr,
        )
        device.press("back")
    wait_for_stable_tree(device)


def open_search_categories(device: Any) -> None:
    click_label(device, "Zoeken")

    categories_heading = scroll_to_label(device, "Alle categorieën")
    if categories_heading is None:
        raise RuntimeError("Could not find 'Alle categorieën' on the Zoeken screen")


def category_output_path(output_dir: Path, index: int, category: str) -> Path:
    slug = re.sub(r"[^a-z0-9]+", "-", category.casefold()).strip("-")
    return output_dir / f"{index:02d}-{slug or 'category'}.json"


def scrape_actions_page(
    device: Any,
    category: str,
    output_path: Path,
    max_scrolls: int,
    unchanged_limit: int,
    settle_seconds: float,
) -> list[str]:
    """Scrape one loaded Acties page and persist only joined text strings."""
    print(f"scraping Acties: {category}", file=sys.stderr)
    joined_text = collect_joined_text(
        device=device,
        package=PICNIC_PACKAGE,
        max_depth=100,
        max_scrolls=max_scrolls,
        unchanged_limit=unchanged_limit,
        settle_seconds=settle_seconds,
        swipe_scale=0.8,
        progress=lambda message: print(
            f"  [{category}] {message}",
            file=sys.stderr,
        ),
    )

    output_path.write_text(
        json.dumps(joined_text, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        f"saved {len(joined_text)} joined text value(s): {output_path}",
        file=sys.stderr,
    )
    return joined_text


def visit_category_actions(
    device: Any,
    category_index: int,
    category: str,
    max_swipes: int,
    actions_wait: float,
    output_dir: Path,
    scrape_max_scrolls: int,
    scrape_unchanged_limit: int,
    scrape_settle_seconds: float,
) -> bool:
    """Open one selected category, visit Acties, then return two screens."""
    print(f"category: {category}", file=sys.stderr)

    category_selector = scroll_to_label(
        device,
        category,
        max_swipes=max_swipes,
    )
    if category_selector is None:
        print(f"warning: category not found, skipping: {category}", file=sys.stderr)
        return False

    category_selector.click()
    wait_for_stable_tree(device)

    if not click_scrolled_label(device, "Acties", max_swipes=max_swipes):
        print(
            f"warning: 'Acties' not found for {category}; returning",
            file=sys.stderr,
        )
        click_top_left_back(device)
        return False

    print(f"opened Acties: {category}", file=sys.stderr)
    if actions_wait:
        time.sleep(actions_wait)

    scrape_actions_page(
        device=device,
        category=category,
        output_path=category_output_path(output_dir, category_index, category),
        max_scrolls=scrape_max_scrolls,
        unchanged_limit=scrape_unchanged_limit,
        settle_seconds=scrape_settle_seconds,
    )

    # Acties -> category page -> Zoeken/Alle categorieën.
    click_top_left_back(device)
    click_top_left_back(device)

    # The list normally preserves its scroll position. Confirm that we are
    # back on Zoeken; the heading may be just outside the viewport.
    if find_label(device, "Zoeken") is None:
        raise RuntimeError(f"Did not return to Zoeken after category {category!r}")

    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Open Picnic, navigate to Zoeken > Alle categorieën, and visit "
            "Acties only for the configured category names."
        )
    )
    parser.add_argument(
        "--serial",
        help="ADB device serial, for example 127.0.0.1:6555",
    )
    parser.add_argument(
        "--category",
        action="append",
        dest="categories",
        help=(
            "Category to visit; repeat to provide a list. When omitted, the "
            "CATEGORIES constant in the script is used."
        ),
    )
    parser.add_argument(
        "--max-swipes",
        type=int,
        default=20,
        help="Maximum swipes while searching for one label (default: 20)",
    )
    parser.add_argument(
        "--actions-wait",
        type=float,
        default=1.0,
        help="Seconds to remain on each Acties screen (default: 1.0)",
    )
    parser.add_argument(
        "--keep-app-state",
        action="store_true",
        help="Start Picnic without force-stopping its existing process",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("acties_joined_text"),
        help="Directory for per-category JSON files (default: acties_joined_text)",
    )
    parser.add_argument(
        "--scrape-max-scrolls",
        type=int,
        default=100,
        help="Maximum swipes while scraping one Acties page (default: 100)",
    )
    parser.add_argument(
        "--scrape-unchanged-limit",
        type=int,
        default=2,
        help="Stop after this many unchanged Acties screens (default: 2)",
    )
    parser.add_argument(
        "--scrape-settle-seconds",
        type=float,
        default=1.0,
        help="Delay after each scraping swipe (default: 1.0)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    categories = args.categories or CATEGORIES

    if not categories:
        raise SystemExit("No categories configured")
    if args.max_swipes < 1:
        raise SystemExit("--max-swipes must be at least 1")
    if args.actions_wait < 0:
        raise SystemExit("--actions-wait must be at least 0")
    if args.scrape_max_scrolls < 0:
        raise SystemExit("--scrape-max-scrolls must be at least 0")
    if args.scrape_unchanged_limit < 1:
        raise SystemExit("--scrape-unchanged-limit must be at least 1")
    if args.scrape_settle_seconds < 0:
        raise SystemExit("--scrape-settle-seconds must be at least 0")

    try:
        import uiautomator2 as u2
    except ImportError:
        print(
            "uiautomator2 is required. Install it with: "
            "python -m pip install uiautomator2",
            file=sys.stderr,
        )
        return 2

    device = u2.connect(args.serial) if args.serial else u2.connect()
    device.implicitly_wait(2.0)

    print("opening Picnic", file=sys.stderr)
    device.app_start(PICNIC_PACKAGE, stop=not args.keep_app_state)
    if not device.app_wait(PICNIC_PACKAGE, front=True, timeout=30.0):
        raise RuntimeError("Picnic did not reach the foreground")
    wait_for_stable_tree(device, timeout=30.0)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    open_search_categories(device)

    visited = 0
    for category_index, category in enumerate(categories, start=1):
        if visit_category_actions(
            device=device,
            category_index=category_index,
            category=category,
            max_swipes=args.max_swipes,
            actions_wait=args.actions_wait,
            output_dir=args.output_dir,
            scrape_max_scrolls=args.scrape_max_scrolls,
            scrape_unchanged_limit=args.scrape_unchanged_limit,
            scrape_settle_seconds=args.scrape_settle_seconds,
        ):
            visited += 1

    print(
        f"done: visited {visited} of {len(categories)} configured categories",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
