"""Reusable Android ViewGroup joined-text extraction."""

from __future__ import annotations

import time
from typing import Any, Callable
import xml.etree.ElementTree as ET


TEXT_ATTRIBUTES = ("text", "content-desc", "hint", "label", "value")
ProgressCallback = Callable[[str], None]


def non_empty_text(attributes: dict[str, str]) -> list[dict[str, str]]:
    """Return every non-empty text-like attribute without losing its source."""
    return [
        {"attribute": name, "value": attributes.get(name, "").strip()}
        for name in TEXT_ATTRIBUTES
        if attributes.get(name, "").strip()
    ]


def extract_direct_prices(element: ET.Element, path: str) -> list[dict[str, object]]:
    """Reconstruct prices whose parts are direct children of one element."""
    prices: list[dict[str, object]] = []
    children = list(element)

    for index, child in enumerate(children):
        if child.attrib.get("resource-id") != "Price.Amount":
            continue

        amount = child.attrib.get("text", "").strip()
        divider = "."
        cents = ""
        cents_index: int | None = None

        for following_index in range(index + 1, len(children)):
            following = children[following_index]
            resource_id = following.attrib.get("resource-id", "")

            if resource_id == "Price.Amount":
                break
            if resource_id == "Price.Divider":
                divider = following.attrib.get("text", ".").strip() or "."
            if resource_id == "Price.Cents":
                cents = following.attrib.get("text", "").strip()
                cents_index = following_index
                break

        if amount and cents and cents_index is not None:
            prices.append(
                {
                    "parent_path": path,
                    "amount_path": f"{path}/{index}",
                    "cents_path": f"{path}/{cents_index}",
                    "amount": amount,
                    "divider": divider,
                    "cents": cents,
                    "value": f"{amount}.{cents.zfill(2)}",
                    "amount_bounds": child.attrib.get("bounds", ""),
                    "cents_bounds": children[cents_index].attrib.get("bounds", ""),
                }
            )

    return prices


def extract_view_groups(
    element: ET.Element,
    path: str = "0",
) -> list[dict[str, object]]:
    """Join ordered text exposed by direct children of each Android ViewGroup."""
    groups: list[dict[str, object]] = []
    children = list(element)

    if element.attrib.get("class") == "android.view.ViewGroup":
        direct_prices = extract_direct_prices(element, path)
        prices_by_amount_path = {
            price["amount_path"]: price for price in direct_prices
        }
        consumed_price_paths = {
            price_path
            for price in direct_prices
            for price_path in (price["amount_path"], price["cents_path"])
        }

        joined_parts: list[str] = []
        direct_text: list[dict[str, str]] = []

        for index, child in enumerate(children):
            child_path = f"{path}/{index}"

            if child_path in prices_by_amount_path:
                joined_parts.append(str(prices_by_amount_path[child_path]["value"]))
                continue

            resource_id = child.attrib.get("resource-id", "")
            if child_path in consumed_price_paths or resource_id == "Price.Divider":
                continue

            child_entries = non_empty_text(dict(child.attrib))
            direct_text.extend(
                {
                    "path": child_path,
                    "attribute": entry["attribute"],
                    "value": entry["value"],
                }
                for entry in child_entries
            )
            joined_parts.extend(entry["value"] for entry in child_entries)

        if joined_parts or direct_prices:
            groups.append(
                {
                    "path": path,
                    "package": element.attrib.get("package", ""),
                    "bounds": element.attrib.get("bounds", ""),
                    "resource_id": element.attrib.get("resource-id", ""),
                    "content_description": element.attrib.get("content-desc", "").strip(),
                    "direct_text": direct_text,
                    "prices": direct_prices,
                    "joined_text": " | ".join(joined_parts),
                }
            )

    for index, child in enumerate(children):
        groups.extend(extract_view_groups(child, f"{path}/{index}"))

    return groups


def joined_text_on_screen(
    device: Any,
    package: str | None,
    max_depth: int,
) -> list[str]:
    """Return ordered, non-empty joined ViewGroup text from the current screen."""
    xml = device.dump_hierarchy(
        compressed=False,
        pretty=False,
        max_depth=max_depth,
    )
    groups = extract_view_groups(ET.fromstring(xml))

    return [
        str(group["joined_text"]).strip()
        for group in groups
        if str(group["joined_text"]).strip()
        and (package is None or group["package"] == package)
    ]


def collect_joined_text(
    device: Any,
    package: str | None,
    max_depth: int = 100,
    max_scrolls: int = 100,
    unchanged_limit: int = 2,
    settle_seconds: float = 1.0,
    swipe_scale: float = 0.8,
    progress: ProgressCallback | None = None,
) -> list[str]:
    """Collect unique joined text until repeated screens indicate list end."""
    collected: list[str] = []
    seen: set[str] = set()
    previous_screen: tuple[str, ...] | None = None
    unchanged_count = 0

    for screen_number in range(max_scrolls + 1):
        screen_text = joined_text_on_screen(device, package, max_depth)
        screen_fingerprint = tuple(screen_text)

        added = 0
        for text in screen_text:
            if text not in seen:
                seen.add(text)
                collected.append(text)
                added += 1

        if progress:
            progress(
                f"screen {screen_number + 1}: "
                f"{len(screen_text)} ViewGroup text value(s), {added} new"
            )

        if screen_fingerprint == previous_screen:
            unchanged_count += 1
        else:
            unchanged_count = 0

        if unchanged_count >= unchanged_limit:
            if progress:
                progress("end reached: screen no longer changes")
            break

        if screen_number == max_scrolls:
            if progress:
                progress("stopped: maximum scroll count reached")
            break

        previous_screen = screen_fingerprint
        device.swipe_ext("up", scale=swipe_scale)
        time.sleep(settle_seconds)

    return collected
