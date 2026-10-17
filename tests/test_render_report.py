import json
import sys
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from render_report import render

class ReportTests(unittest.TestCase):
    def load(self, name):
        return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))
    def test_history_shows_pending_and_budget_without_invented_savings(self):
        html = render(self.load("latest-quotes.json"), adapted=True)
        for expected in ["历史报价回放", "¥27.50", "超出 ¥2.50", "超出 ¥3.40", "还没查清这款饮品是否无糖"]:
            self.assertIn(expected, html)
        self.assertNotIn("少花 ¥", html)
        self.assertNotIn("相比原需求基线", html)
        self.assertNotIn("暂不计算", html)
        self.assertNotIn("未记录额外餐品", html)
    def test_extra_spend_and_real_saving(self):
        self.assertIn("多花 ¥2.00", render(self.load("demo-quotes.json")))
        self.assertIn("少花 ¥2.00", render(self.load("demo-saving.json")))
    def test_untrusted_content_escaped(self):
        d = self.load("demo-quotes.json")
        d["candidates"][0]["name"] = '<script>alert(1)</script>'
        d["report"]["need"] = '<img src=x onerror=alert(1)>'
        html = render(d)
        self.assertNotIn('<script>', html)
        self.assertNotIn('<img ', html)
        self.assertIn('&lt;script&gt;', html)

    def test_price_only_demo_does_not_inherit_sugar_constraint(self):
        html = render(self.load("coupon-price-only.json"), adapted=True)
        self.assertNotIn("是否无糖", html)
        self.assertNotIn("暂不推荐", html)
        self.assertIn("少花 ¥2.00", html)
        self.assertIn("超出 ¥1.40", html)
        self.assertIn("没有加购", html)
        self.assertIn("非官方产品", html)
