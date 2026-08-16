import json
import time
import xml.etree.ElementTree as ET

import uiautomator2 as u2

PACKAGE = "com.picnic.android"
MAX_SCROLLS = 100
OUTPUT_FILE = "picnic_promotions.json"


def visible_items(device):
    xml = device.dump_hierarchy(
        compressed=False,
        pretty=False,
        max_depth=50,
    )

    root = ET.fromstring(xml)
    items = []

    for node in root.iter("node"):
        text = node.attrib.get("text", "").strip()
        description = node.attrib.get("content-desc", "").strip()
        resource_id = node.attrib.get("resource-id", "").strip()
        bounds = node.attrib.get("bounds", "")

        if not text and not description:
            continue

        items.append(
            {
                "text": text,
                "description": description,
                "resource_id": resource_id,
                "bounds": bounds,
            }
        )

    return items


def item_key(item):
    return (
        item["text"],
        item["description"],
        item["resource_id"],
    )


def main():
    device = u2.connect()
    device.implicitly_wait(10)

    print("Connected:", device.device_info)

    device.app_start(PACKAGE)
    if not device.app_wait(PACKAGE, front=True, timeout=20):
        raise RuntimeError("Picnic did not start")

    input(
        "Navigate to the Promotions screen in Genymotion, "
        "then press Enter here..."
    )

    collected = {}
    unchanged_rounds = 0

    for page_number in range(MAX_SCROLLS):
        page_items = visible_items(device)
        previous_count = len(collected)

        for item in page_items:
            collected[item_key(item)] = item

        print(
            f"Page {page_number + 1}: "
            f"{len(page_items)} visible nodes, "
            f"{len(collected)} unique nodes"
        )

        if len(collected) == previous_count:
            unchanged_rounds += 1
        else:
            unchanged_rounds = 0

        if unchanged_rounds >= 3:
            print("No new elements after three scrolls; stopping.")
            break

        device.swipe_ext("up", scale=0.8)
        time.sleep(1.5)

    results = list(collected.values())

    with open(OUTPUT_FILE, "w", encoding="utf-8") as output:
        json.dump(results, output, ensure_ascii=False, indent=2)

    print(f"Saved {len(results)} nodes to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()