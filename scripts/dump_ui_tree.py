"""Dump every accessibility node and text value from the current Android screen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from groceriesdeals.joined_text import (
    extract_direct_prices,
    extract_view_groups,
    non_empty_text,
)


def serialize_node(
    element: ET.Element,
    path: str,
    depth: int,
    flat_text: list[dict[str, object]],
) -> dict[str, object]:
    """Serialize a node recursively and calculate its complete subtree text."""
    attributes = dict(element.attrib)
    own_text = non_empty_text(attributes)

    for entry in own_text:
        flat_text.append(
            {
                "path": path,
                "depth": depth,
                "attribute": entry["attribute"],
                "value": entry["value"],
                "bounds": attributes.get("bounds", ""),
                "resource_id": attributes.get("resource-id", ""),
                "class": attributes.get("class", ""),
            }
        )

    children = [
        serialize_node(child, f"{path}/{index}", depth + 1, flat_text)
        for index, child in enumerate(element)
    ]

    subtree_text = [dict(entry) for entry in own_text]
    for child in children:
        subtree_text.extend(child["subtree_text"])

    return {
        "path": path,
        "depth": depth,
        "tag": element.tag,
        "attributes": attributes,
        "own_text": own_text,
        "subtree_text": subtree_text,
        "children": children,
    }


def parse_hierarchy(xml: str) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Parse a UIAutomator XML hierarchy into nested and flat representations."""
    root = ET.fromstring(xml)
    flat_text: list[dict[str, object]] = []
    tree = serialize_node(root, "0", 0, flat_text)
    return tree, flat_text


def extract_prices(element: ET.Element, path: str = "0") -> list[dict[str, object]]:
    """Reconstruct Picnic prices split across Amount/Divider/Cents siblings."""
    prices = extract_direct_prices(element, path)
    for index, child in enumerate(element):
        prices.extend(extract_prices(child, f"{path}/{index}"))
    return prices


def write_dump(
    output_dir: Path,
    mode: str,
    xml: str,
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    tree, flat_text = parse_hierarchy(xml)
    xml_root = ET.fromstring(xml)
    prices = extract_prices(xml_root)
    view_groups = extract_view_groups(xml_root)

    (output_dir / f"ui-tree-{mode}.xml").write_text(xml, encoding="utf-8")
    (output_dir / f"ui-tree-{mode}.json").write_text(
        json.dumps(tree, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / f"ui-text-{mode}.json").write_text(
        json.dumps(flat_text, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / f"ui-prices-{mode}.json").write_text(
        json.dumps(prices, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / f"ui-view-groups-{mode}.json").write_text(
        json.dumps(view_groups, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return flat_text, prices, view_groups


def report_matches(
    mode: str,
    flat_text: list[dict[str, object]],
    prices: list[dict[str, object]],
    searches: list[str],
) -> None:
    for search in searches:
        matches = [
            entry
            for entry in flat_text
            if search.casefold() in str(entry["value"]).casefold()
        ]
        print(f"{mode}: {search!r} -> {len(matches)} match(es)")
        for match in matches:
            print(
                f"  {match['path']} {match['attribute']} "
                f"{match['bounds']}: {match['value']!r}"
            )

        price_matches = [price for price in prices if search in str(price["value"])]
        for price in price_matches:
            print(
                f"  reconstructed price {price['parent_path']}: "
                f"{price['value']}"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Dump the complete UIAutomator accessibility tree for the current "
            "screen, including all attributes and recursively aggregated text."
        )
    )
    parser.add_argument(
        "--serial",
        help="ADB device serial, for example 127.0.0.1:6555",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("ui_tree_dump"),
        help="Destination directory (default: ui_tree_dump)",
    )
    parser.add_argument(
        "--find",
        action="append",
        default=[],
        help="Search all extracted text values; may be specified multiple times",
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
    args.output_dir.mkdir(parents=True, exist_ok=True)

    serial = device.device_info.get("serial") or args.serial or "device"
    print(f"Connected to {serial}")

    all_text: dict[str, list[dict[str, object]]] = {}
    all_prices: dict[str, list[dict[str, object]]] = {}
    all_view_groups: dict[str, list[dict[str, object]]] = {}
    for mode, compressed in (("uncompressed", False), ("compressed", True)):
        xml = device.dump_hierarchy(
            compressed=compressed,
            pretty=True,
            max_depth=args.max_depth,
        )
        (
            all_text[mode],
            all_prices[mode],
            all_view_groups[mode],
        ) = write_dump(args.output_dir, mode, xml)
        print(f"{mode}: captured {len(all_text[mode])} text value(s)")
        print(f"{mode}: reconstructed {len(all_prices[mode])} price(s)")
        print(f"{mode}: joined {len(all_view_groups[mode])} ViewGroup(s)")
        report_matches(mode, all_text[mode], all_prices[mode], args.find)

    combined = {
        mode: entries
        for mode, entries in all_text.items()
    }
    (args.output_dir / "ui-text-all.json").write_text(
        json.dumps(combined, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.output_dir / "ui-prices-all.json").write_text(
        json.dumps(all_prices, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.output_dir / "ui-view-groups-all.json").write_text(
        json.dumps(all_view_groups, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Wrote UI tree dumps to {args.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
