from __future__ import annotations

import unittest

from groceriesdeals.deals import get_current_discounts
from groceriesdeals.picnic_deals import (
    load_picnic_deals,
    parse_joined_text,
    parse_product_card,
)
from groceriesdeals.supermarkets import list_supermarkets


class PicnicDealParserTests(unittest.TestCase):
    def test_parse_product_with_tagline_prices_and_badge(self) -> None:
        deal = parse_product_card(
            "Fris en sappig, Nectarines >, 2.99, 4.99, XL, 1 kilo",
            discount_label="nu €2.99",
            category="fruit",
            category_label="Fruit",
        )
        assert deal is not None
        self.assertEqual(deal.name, "Nectarines")
        self.assertEqual(deal.tagline, "Fris en sappig")
        self.assertEqual(deal.price, 2.99)
        self.assertEqual(deal.was_price, 4.99)
        self.assertEqual(deal.unit, "1 kilo")
        self.assertEqual(deal.badges, ("XL",))
        self.assertEqual(deal.discount_label, "nu €2.99")

    def test_parse_product_with_brand_and_no_was_price(self) -> None:
        deal = parse_product_card(
            "Worstjes smokey chicken >, 3.99, 't Slagershuys, 5 x 65 gram",
            discount_label="2 voor €6",
        )
        assert deal is not None
        self.assertEqual(deal.name, "Worstjes smokey chicken")
        self.assertIsNone(deal.was_price)
        self.assertEqual(deal.brand, "'t Slagershuys")
        self.assertEqual(deal.unit, "5 x 65 gram")

    def test_parse_joined_text_attaches_nearest_promo(self) -> None:
        deals = parse_joined_text(
            [
                "Terug",
                "Acties",
                "50% korting",
                "Chicken schnitzel >, 2.49, 4.99, Impossible, 180 gram",
                "Chicken tenders >, 2.49, 4.99, Impossible, 180 gram",
                "Ontdek",
                "Mandje",
                "40% korting",
                "Meat balls >, 2.49, 4.99, Impossible, 180 gram",
            ],
            category="vega_plantaardig",
            category_label="Vega & plantaardig",
        )
        self.assertEqual(len(deals), 3)
        self.assertEqual(deals[0].discount_label, "50% korting")
        self.assertEqual(deals[1].discount_label, "50% korting")
        self.assertEqual(deals[2].discount_label, "40% korting")
        self.assertEqual(deals[0].brand, "Impossible")

    def test_packaged_picnic_data_loads(self) -> None:
        deals = load_picnic_deals()
        self.assertGreaterEqual(len(deals), 100)
        categories = {deal.category for deal in deals}
        self.assertIn("fruit", categories)
        self.assertIn("bakkerij", categories)


class DealsServiceTests(unittest.TestCase):
    def test_list_supermarkets_is_picnic_only(self) -> None:
        self.assertEqual(list_supermarkets(), [{"id": "picnic", "name": "Picnic"}])

    def test_get_current_discounts_for_picnic(self) -> None:
        result = get_current_discounts("picnic")
        self.assertTrue(result["available"])
        self.assertGreater(result["deal_count"], 0)
        self.assertEqual(len(result["deals"]), result["deal_count"])
        self.assertIsNone(result["message"])

    def test_get_current_discounts_category_filter(self) -> None:
        result = get_current_discounts("picnic", category="fruit")
        self.assertTrue(result["available"])
        self.assertEqual(result["deal_count"], 6)
        self.assertTrue(all(deal["category"] == "fruit" for deal in result["deals"]))

    def test_unsupported_supermarket_is_reported(self) -> None:
        result = get_current_discounts("jumbo")
        self.assertFalse(result["available"])
        self.assertEqual(result["deal_count"], 0)
        self.assertIn("Unsupported supermarket_id", result["message"])


if __name__ == "__main__":
    unittest.main()
