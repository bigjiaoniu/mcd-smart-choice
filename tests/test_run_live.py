import copy
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_live import run_live, budget_fen, default_item
from adapt_quotes import adapt
from compare_quotes import compare

class FakeClient:
    def __init__(self, coupons=True, fail_price=False):
        self.calls = []
        self.coupons = coupons
        self.fail_price = fail_price
    def call(self, name, args):
        self.calls.append((name, copy.deepcopy(args)))
        if name == "query-meal-detail":
            data = dict(code=args["code"], name="商品" + args["code"], rounds=[], modification={"items": []})
        elif name == "query-store-coupons":
            data = [dict(title="测试券", couponId="PRIVATE-ID", couponCode="PRIVATE-CODE",
                         products=[{"productCode": "2"}])] if self.coupons else []
        else:
            used = any("couponId" in i for i in args["items"])
            data = {"price": 2640 if used else 2840}
        return {"structuredContent": dict(success=not self.fail_price or name != "calculate-price", code=200, data=data)}

class LiveTests(unittest.TestCase):
    def args(self):
        return SimpleNamespace(store="1960088", product=["1", "2"], coupon_product="2", coupon_title=None,
                               budget="25", config=None, need="测试需求", needs_status="pending", output=Path("local/test.html"))
    def test_pipeline_only_queries_and_preserves_private_ids_in_memory(self):
        client = FakeClient()
        doc, evidence = run_live(self.args(), client)
        result = compare(adapt(doc))
        self.assertEqual(result["results"][1]["same_basket_saving_fen"], 200)
        self.assertEqual(result["status"], "no_eligible_option")
        self.assertNotIn("PRIVATE", str(doc) + str(evidence))
        self.assertEqual(len([c for c in client.calls if c[0] == "calculate-price"]), 2)
        self.assertTrue(all(c[0] in {"query-meal-detail", "query-store-coupons", "calculate-price"} for c in client.calls))
    def test_no_coupon_still_quotes_direct_purchase(self):
        client = FakeClient(coupons=False)
        doc, _ = run_live(self.args(), client)
        self.assertEqual(len(doc["candidates"]), 1)
        self.assertEqual(doc["coupon_status"], "none_available")
    def test_business_failure_not_treated_as_quote(self):
        with self.assertRaises(ValueError):
            run_live(self.args(), FakeClient(fail_price=True))
    def test_selected_basket_must_include_coupon_product(self):
        args = self.args()
        args.coupon_product = "missing"
        with self.assertRaises(ValueError):
            run_live(args, FakeClient())
    def test_needs_confirmed_not_implied_by_budget(self):
        args = self.args()
        args.needs_status = "confirmed"
        doc, _ = run_live(args, FakeClient())
        result = compare(adapt(doc))
        self.assertEqual(result["status"], "no_eligible_option")
        self.assertEqual(result["baseline_status"], "valid")
    def test_decimal_budget_is_exact(self):
        self.assertEqual(budget_fen("25.01"), 2501)
        for value in ["25.001", "NaN", "Infinity", "-1"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                budget_fen(value)
    def test_combo_and_unspecified_required_options_rejected(self):
        for detail in [{"rounds": [1]}, {"modification": {"items": [{"minValues": 1, "values": [{"selectedQuantity": 0}]}]}}]:
            with self.assertRaises(ValueError):
                default_item("1", detail)
