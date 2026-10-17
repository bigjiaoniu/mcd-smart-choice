import copy
import json
import sys
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from adapt_quotes import adapt
from compare_quotes import compare
from mcp_read_client import Client
from render_report import render

class CouponComparisonTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((ROOT / "examples/coupon-verified-quotes.json").read_text(encoding="utf-8"))
    def test_same_items_save_two_yuan_without_claiming_needs_met(self):
        result = compare(adapt(self.doc))
        candidate = result["results"][1]
        self.assertEqual(candidate["same_basket_saving_fen"], 200)
        self.assertIsNone(candidate["saving_fen"])
        self.assertEqual(candidate["over_budget_fen"], 140)
        self.assertEqual(result["status"], "no_eligible_option")
    def test_changed_item_quantity_or_modifier_cannot_compare_as_same(self):
        changes = [("productCode", "other"), ("quantity", 2), ("modification", {"values": []})]
        for key, value in changes:
            with self.subTest(key=key):
                doc = copy.deepcopy(self.doc)
                doc["candidates"][1]["basket_items"][0][key] = value
                result = compare(adapt(doc))
                self.assertIsNone(result["results"][1]["same_basket_saving_fen"])
    def test_missing_item_identity_disables_comparison(self):
        del self.doc["candidates"][1]["basket_items"]
        self.assertIsNone(compare(adapt(self.doc))["results"][1]["same_basket_saving_fen"])
    def test_report_shows_actual_difference_and_budget_limit(self):
        html = render(self.doc, adapted=True)
        self.assertIn("少花 ¥2.00", html)
        self.assertIn("超出 ¥1.40", html)
        self.assertIn("还没查清这款冰美式是否无糖", html)
        self.assertNotIn("少花 ¥9.10", html)
    def test_client_disallows_external_mutations_before_network(self):
        client = Client.__new__(Client)
        for name in ["create-order", "auto-bind-coupons", "mall-create-order", "draw-lottery", "cancel-order"]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                client.call(name, {})
