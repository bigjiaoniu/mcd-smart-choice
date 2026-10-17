import copy
import json
from pathlib import Path
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ui_server import Service, make_handler

class FakeMCP:
    def __init__(self):
        self.calls = []
    def call(self, name, args):
        self.calls.append((name, copy.deepcopy(args)))
        if name == "query-nearby-stores":
            data = [{"storeCode": "123", "storeName": "测试餐厅", "address": "PRIVATE-ADDRESS", "businessStatus": True}]
        elif name == "query-meals":
            data = {"categories": [{"name": "单品", "meals": [{"code": "1"}, {"code": "2"}]}],
                    "meals": {"1": {"name": "汉堡", "currentPrice": "16.50"}, "2": {"name": "咖啡", "currentPrice": "11.90"}}}
        elif name == "query-store-coupons":
            data = [{"title": "测试咖啡券", "couponId": "PRIVATE-ID", "couponCode": "PRIVATE-CODE", "products": [{"productCode": "2", "productName": "咖啡"}]}]
        elif name == "query-meal-detail":
            data = {"code": args["code"], "name": "餐品" + args["code"], "rounds": [], "modification": {"items": []}}
        elif name == "calculate-price":
            data = {"price": 2640 if any("couponId" in i for i in args["items"]) else 2840}
        else:
            raise AssertionError("Unexpected tool")
        return {"structuredContent": {"success": True, "code": 200, "data": data}}

class UITests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeMCP()
        self.service = Service(factory=lambda: self.fake)
    def populate(self):
        stores = self.service.stores("武汉", "测试")
        menu = self.service.menu("123")
        return stores, menu
    def test_stores_and_coupon_ids_are_sanitized(self):
        stores, menu = self.populate()
        self.assertNotIn("PRIVATE", json.dumps([stores, menu]))
        self.assertEqual(len(menu["products"]), 2)
        self.assertEqual(menu["coupons"][0]["products"][0]["id"], "2")
    def test_compare_uses_alias_but_never_returns_real_coupon(self):
        _, menu = self.populate()
        result = self.service.calculate({"store": "123", "products": ["1", "2"], "coupon": menu["coupons"][0]["id"], "budget": "25"})
        self.assertEqual(result["result"]["results"][1]["same_basket_saving_fen"], 200)
        self.assertNotIn("PRIVATE", json.dumps(result))
        self.assertNotIn("无糖", result["report"]["need"])
    def test_cannot_quote_products_from_another_store(self):
        self.populate()
        with self.assertRaises(ValueError):
            self.service.calculate({"store": "123", "products": ["unknown"]})
    def test_selected_coupon_requires_its_product(self):
        _, menu = self.populate()
        with self.assertRaises(ValueError):
            self.service.calculate({"store": "123", "products": ["1"], "coupon": menu["coupons"][0]["id"]})
    def test_unknown_alias_does_not_call_price_tool(self):
        self.populate()
        with self.assertRaises(ValueError):
            self.service.calculate({"store": "123", "products": ["1", "2"], "coupon": "invalid"})
        self.assertFalse(any(t == "calculate-price" for t, _ in self.fake.calls))
    def test_demo_uses_no_network_and_budget_is_recomputed(self):
        result = self.service.demo("coupon", "30")
        self.assertEqual(result["result"]["status"], "options_found")
        self.assertEqual(self.fake.calls, [])
    def test_http_requires_csrf_and_rejects_cross_origin(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.service, "nonce"))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = "http://127.0.0.1:" + str(server.server_port)
        try:
            with urlopen(base + "/api/status") as response:
                self.assertEqual(json.load(response)["csrf"], "nonce")
            for headers in [{}, {"X-Local-CSRF": "nonce", "Origin": "https://evil.example"}]:
                request = Request(base + "/api/stores", data=b'{}', headers=headers)
                with self.assertRaises(HTTPError) as raised:
                    urlopen(request)
                self.assertEqual(raised.exception.code, 403)
            self.assertEqual(self.fake.calls, [])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
