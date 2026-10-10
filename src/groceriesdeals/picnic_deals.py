"""Load and parse Picnic Acties scrapes into structured deal records."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path


_NAV_CHROME = frozenset(
    {
        "terug",
        "acties",
        "ontdek",
        "favorieten",
        "koken",
        "zoeken",
        "mandje",
    }
)

_BADGE_TOKENS = frozenset(
    {
        "xl",
        "klein",
        "prijskampioen",
        "diepvries",
        "vegan",
        "nl",
        "thuis afbakken",
        "bio",
    }
)

_UNIT_RE = re.compile(
    r"(?i)^(?:"
    r"\d+(?:[.,]\d+)?\s*(?:kilo|kg|gram|g|liter|l|ml|stuks?|cl)"
    r"|ca\.\s*\d+(?:[.,]\d+)?\s*(?:kilo|kg|gram|g)"
    r"|\d+\s*x\s*\d+(?:[.,]\d+)?\s*(?:gram|g|ml)"
    r"|\d+\s*stuks?"
    r")$"
)

_PRICE_RE = re.compile(r"^\d+(?:[.,]\d{1,2})?$")
_PRODUCT_MARKER_RE = re.compile(r"(?:\xa0|>)\s*>")
_PRODUCT_LINE_RE = re.compile(r">\s*,\s*\d")
_PROMO_RE = re.compile(
    r"(?i)^(?:"
    r"(?:tot\s+)?\d+%\s*korting"
    r"|nu\s+(?:voor\s+)?€\s*\d+(?:[.,]\d{2})?"
    r"|\d+\s*voor\s+€\s*\d+(?:[.,]\d{2})?"
    r"|2e\s*(?:=?\s*\d+%\s*korting|halve\s+prijs)"
    r"|3\s*\+\s*1\s*gratis"
    r"|€\s*\d+(?:[.,]\d{2})?\s*korting"
    r")$"
)

_CATEGORY_LABELS = {
    "fruit": "Fruit",
    "aardappelen_groente": "Aardappelen & groente",
    "vlees_vis": "Vlees & vis",
    "vega_plantaardig": "Vega & plantaardig",
    "bakkerij": "Bakkerij",
}


@dataclass(frozen=True, slots=True)
class Deal:
    """One discounted Picnic product."""

    name: str
    price: float
    currency: str = "EUR"
    was_price: float | None = None
    tagline: str | None = None
    unit: str | None = None
    brand: str | None = None
    discount_label: str | None = None
    category: str | None = None
    category_label: str | None = None
    badges: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["badges"] = list(self.badges)
        return payload


def _parse_price(token: str) -> float | None:
    if not _PRICE_RE.match(token.strip()):
        return None
    return float(token.strip().replace(",", "."))


def _is_product_line(text: str) -> bool:
    return ">" in text and bool(_PRODUCT_LINE_RE.search(text))


def _is_promo_label(text: str) -> bool:
    return bool(_PROMO_RE.match(text.strip()))


def _category_from_filename(path: Path) -> tuple[str, str]:
    stem = path.stem
    slug = re.sub(r"^\d+-", "", stem).replace("-", "_")
    label = _CATEGORY_LABELS.get(slug, slug.replace("_", " ").title())
    return slug, label


def parse_product_card(
    text: str,
    *,
    discount_label: str | None = None,
    category: str | None = None,
    category_label: str | None = None,
) -> Deal | None:
    """Parse one Picnic product content-description into a Deal."""
    cleaned = text.replace("\xa0", " ").strip()
    if not _is_product_line(cleaned):
        return None

    marker = cleaned.find(">")
    if marker < 0:
        return None

    left = cleaned[:marker].rstrip(" ,")
    right = cleaned[marker + 1 :].lstrip(" ,")
    if "," in left:
        tagline, name = left.rsplit(",", 1)
        tagline = tagline.strip() or None
        name = name.strip()
    else:
        tagline = None
        name = left.strip()

    if not name:
        return None

    tokens = [part.strip() for part in right.split(",") if part.strip()]
    prices: list[float] = []
    rest: list[str] = []
    for token in tokens:
        price = _parse_price(token)
        if price is not None and len(prices) < 2 and not rest:
            prices.append(price)
        else:
            rest.append(token)

    if not prices:
        return None

    unit: str | None = None
    brand: str | None = None
    badges: list[str] = []
    for token in rest:
        lowered = token.lower()
        if unit is None and _UNIT_RE.match(token):
            unit = token
        elif lowered in _BADGE_TOKENS:
            badges.append(token)
        elif brand is None:
            brand = token
        else:
            badges.append(token)

    return Deal(
        name=name,
        price=prices[0],
        was_price=prices[1] if len(prices) > 1 else None,
        tagline=tagline,
        unit=unit,
        brand=brand,
        discount_label=discount_label,
        category=category,
        category_label=category_label,
        badges=tuple(badges),
    )


def parse_joined_text(
    entries: list[str],
    *,
    category: str | None = None,
    category_label: str | None = None,
) -> list[Deal]:
    """Turn a scraped Acties string list into structured deals."""
    deals: list[Deal] = []
    current_promo: str | None = None

    for raw in entries:
        text = raw.replace("\xa0", " ").strip()
        if not text:
            continue
        if text.lower() in _NAV_CHROME:
            continue
        if _is_promo_label(text):
            current_promo = text
            continue
        if _is_product_line(text):
            deal = parse_product_card(
                text,
                discount_label=current_promo,
                category=category,
                category_label=category_label,
            )
            if deal is not None:
                deals.append(deal)
            continue
        # Section headers and duplicate badge chips are ignored.

    return deals


def _picnic_data_dir() -> Path:
    return Path(__file__).resolve().parent / "data" / "picnic"


@lru_cache(maxsize=1)
def load_picnic_deals() -> tuple[Deal, ...]:
    """Load all packaged Picnic category scrapes."""
    data_dir = _picnic_data_dir()
    deals: list[Deal] = []
    for path in sorted(data_dir.glob("*.json")):
        category, category_label = _category_from_filename(path)
        entries = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(entries, list):
            continue
        deals.extend(
            parse_joined_text(
                [str(item) for item in entries],
                category=category,
                category_label=category_label,
            )
        )
    return tuple(deals)


def get_picnic_deals(*, category: str | None = None) -> list[dict[str, object]]:
    """Return Picnic deals, optionally filtered by category slug."""
    deals = load_picnic_deals()
    if category is not None:
        needle = category.strip().lower().replace(" ", "_").replace("-", "_")
        deals = tuple(deal for deal in deals if deal.category == needle)
    return [deal.to_dict() for deal in deals]


def picnic_categories() -> list[dict[str, str]]:
    """Return category ids present in the packaged Picnic data."""
    seen: dict[str, str] = {}
    for deal in load_picnic_deals():
        if deal.category and deal.category not in seen:
            seen[deal.category] = deal.category_label or deal.category
    return [{"id": key, "label": value} for key, value in seen.items()]
