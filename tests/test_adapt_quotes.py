import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from adapt_quotes import adapt

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.context = dict(store_id="demo", dining_mode="pickup", quote_batch="one")
        self.entry = dict(self.context, name="报价", price_data={"price": 2750, "token": "DROP"},
                          business_success=True, evidence_ref="脱敏记录", meets_needs=None)
    def document(self):
        return dict(context=self.context, budget_fen=2500, candidates=[self.entry])
    def test_exact_price_mapping_and_pending_needs(self):
        result = adapt(self.document())["candidates"][0]
        self.assertEqual(result["payable_fen"], 2750)
        self.assertIsNone(result["meets_needs"])
        self.assertNotIn("token", str(result))
    def test_success_and_evidence_required(self):
        for field, value in [("business_success", False), ("evidence_ref", "")]:
            with self.subTest(field=field):
                original = self.entry[field]
                self.entry[field] = value
                with self.assertRaises(ValueError):
                    adapt(self.document())
                self.entry[field] = original
    def test_context_mismatch_rejected(self):
        self.entry["store_id"] = "other"
        with self.assertRaises(ValueError):
            adapt(self.document())
    def test_invalid_price_rejected(self):
        for price in [True, 27.5, -1, "2750"]:
            with self.subTest(price=price):
                self.entry["price_data"]["price"] = price
                with self.assertRaises(ValueError):
                    adapt(self.document())
