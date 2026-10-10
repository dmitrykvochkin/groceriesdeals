"""Supermarket-agnostic discount lookups used by MCP tools."""

from __future__ import annotations

from groceriesdeals.picnic_deals import get_picnic_deals, picnic_categories
from groceriesdeals.supermarkets import get_supermarket, supported_supermarket_ids


def get_current_discounts(
    supermarket_id: str,
    category: str | None = None,
) -> dict[str, object]:
    """Return active discounts for a supported supermarket."""
    supermarket = get_supermarket(supermarket_id)
    if supermarket is None:
        supported = ", ".join(supported_supermarket_ids()) or "(none)"
        return {
            "supermarket_id": supermarket_id,
            "available": False,
            "deal_count": 0,
            "deals": [],
            "categories": [],
            "message": (
                f"Unsupported supermarket_id {supermarket_id!r}. "
                f"Supported: {supported}. Call list_supermarkets for the catalog."
            ),
        }

    if supermarket.id == "picnic":
        deals = get_picnic_deals(category=category)
        categories = picnic_categories()
        if category is not None and not deals:
            return {
                "supermarket_id": supermarket.id,
                "available": True,
                "deal_count": 0,
                "deals": [],
                "categories": categories,
                "message": (
                    f"No Picnic deals found for category {category!r}. "
                    "Omit category to return all deals."
                ),
            }
        return {
            "supermarket_id": supermarket.id,
            "available": True,
            "deal_count": len(deals),
            "deals": deals,
            "categories": categories,
            "message": None,
        }

    return {
        "supermarket_id": supermarket.id,
        "available": False,
        "deal_count": 0,
        "deals": [],
        "categories": [],
        "message": f"No discount feed is wired for {supermarket.name} yet.",
    }
