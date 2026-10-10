"""Registry of supermarkets exposed by the MCP deals tools."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Supermarket:
    """A supermarket clients can query for active discounts."""

    id: str
    name: str


# v1: only Picnic has packaged deal data. Add retailers here when their
# scrapes ship with the server so list_supermarkets stays the source of truth.
_SUPERMARKETS: tuple[Supermarket, ...] = (
    Supermarket(id="picnic", name="Picnic"),
)


def list_supermarkets() -> list[dict[str, str]]:
    """Return the currently supported supermarket catalog."""
    return [{"id": item.id, "name": item.name} for item in _SUPERMARKETS]


def get_supermarket(supermarket_id: str) -> Supermarket | None:
    """Return a supermarket by id, or None when it is not supported yet."""
    normalized = supermarket_id.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "picnic": "picnic",
        "albert_heijn": "albert_heijn",
        "albertheijn": "albert_heijn",
        "ah": "albert_heijn",
        "jumbo": "jumbo",
    }
    canonical = aliases.get(normalized, normalized)
    for item in _SUPERMARKETS:
        if item.id == canonical:
            return item
    return None


def supported_supermarket_ids() -> list[str]:
    """Return supported supermarket ids for tool descriptions and errors."""
    return [item.id for item in _SUPERMARKETS]
