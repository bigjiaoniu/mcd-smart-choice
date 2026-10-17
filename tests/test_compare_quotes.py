import importlib.util
from pathlib import Path
import unittest

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("quotes", root / "scripts/compare_quotes.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class CompareTests(unittest.TestCase):
    def setUp(self):
        self.base = dict(name="基线", payable_fen=2200, verified=True, meets_needs=True,
                         store_id="demo", dining_mode="pickup", quote_batch="demo-batch")
    def run_quote(self, **changes):
        quote = dict(self.base, name="候选")
        quote.update(changes)
        return module.compare(dict(budget_fen=2500, baseline=self.base, candidates=[quote]))
    def test_extra_spend_is_negative_saving(self):
        out = self.run_quote(payable_fen=2400, extra_items=["配餐"])
        self.assertEqual(out["results"][1]["saving_fen"], -200)
        self.assertEqual(out["lowest_verified_options"], ["基线"])
    def test_real_saving(self):
        out = self.run_quote(payable_fen=2000)
        self.assertEqual(out["results"][1]["saving_fen"], 200)
        self.assertEqual(out["lowest_verified_options"], ["候选"])
    def test_invalid_candidates_excluded(self):
        for changes in [dict(verified=False), dict(meets_needs=False), dict(store_id="other"),
                        dict(dining_mode="delivery"), dict(quote_batch="old")]:
            with self.subTest(changes=changes):
                out = self.run_quote(payable_fen=1000, **changes)
                self.assertIsNone(out["results"][1]["saving_fen"])
                self.assertEqual(out["lowest_verified_options"], ["基线"])
    def test_over_budget(self):
        out = self.run_quote(payable_fen=2600)
        self.assertFalse(out["results"][1]["within_budget"])
    def test_invalid_money(self):
        for amount in [-1, 1.1, True]:
            with self.assertRaises(ValueError):
                self.run_quote(payable_fen=amount)
    def test_unverified_baseline_has_no_savings(self):
        self.base["verified"] = False
        out = self.run_quote()
        self.assertEqual(out["baseline_status"], "unavailable")
        self.assertTrue(all(q["saving_fen"] is None for q in out["results"]))

    def test_no_baseline_and_pending_needs(self):
        quote = dict(self.base, meets_needs=None, payable_fen=2750)
        out = module.compare(dict(budget_fen=2500, context=self.base,
                                  baseline=None, candidates=[quote]))
        self.assertEqual(out["status"], "no_eligible_option")
        self.assertEqual(out["results"][0]["over_budget_fen"], 250)
        self.assertIn("需求属性待确认", out["results"][0]["reasons"])
        self.assertIsNone(out["results"][0]["saving_fen"])

    def test_qualifying_candidate_without_baseline(self):
        out = module.compare(dict(budget_fen=2500, context=self.base,
                                  candidates=[self.base]))
        self.assertEqual(out["status"], "options_found")
        self.assertIsNone(out["results"][0]["saving_fen"])

    def test_empty_candidates(self):
        out = module.compare(dict(budget_fen=2500, context=self.base))
        self.assertEqual(out["status"], "no_eligible_option")
        self.assertEqual(out["lowest_verified_options"], [])

if __name__ == "__main__":
    unittest.main()
