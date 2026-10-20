"""Loopback-only UI: no credentials in browser, readonly MCP and price calculation."""
import argparse
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
from threading import Lock
from types import SimpleNamespace
from urllib.parse import urlsplit, parse_qs
from urllib.error import HTTPError, URLError
import webbrowser

from adapt_quotes import adapt
from compare_quotes import compare
from mcp_read_client import Client
from run_live import run_live, checked_call, budget_fen
from suggestions import plans, MemoClient

ROOT = Path(__file__).resolve().parents[1]

class Service:
    def __init__(self, config=None, factory=None):
        self.config = config
        self.factory = factory
        self.client = None
        self.store_cache = {}
        self.menu_cache = {}
        self.coupon_cache = {}
        self.lock = Lock()

    @property
    def configured(self):
        return bool(self.factory or os.environ.get("MCD_MCP_TOKEN") or self.config)

    def get_client(self):
        if not self.client:
            self.client = self.factory() if self.factory else Client(self.config)
        return self.client

    def demo(self, case="coupon", budget="25"):
        choices = {"coupon": ("coupon-price-only.json", True), "extra": ("demo-quotes.json", False),
                   "none": ("latest-quotes.json", True)}
        if case not in choices:
            raise ValueError("未知演示案例")
        filename, needs_adapt = choices[case]
        doc = json.loads((ROOT / "examples" / filename).read_text(encoding="utf-8"))
        doc["budget_fen"] = budget_fen(budget)
        normalized = adapt(doc) if needs_adapt else doc
        result = compare(normalized)
        return {"result": result, "report": doc.get("report", {}), "budget_fen": doc["budget_fen"],
                "mode": "demo", "case": case, "historical": True}

    def stores(self, city, keyword):
        if not city.strip() or not keyword.strip():
            raise ValueError("请填写城市和商圈或门店关键词")
        payload = checked_call(self.get_client(), "query-nearby-stores", dict(city=city, keyword=keyword, searchType=2, beType=1))
        if not isinstance(payload.get("data"), list):
            raise ValueError("门店返回格式不支持")
        stores = []
        for item in payload["data"]:
            code = str(item.get("storeCode", ""))
            if not code.isdigit():
                continue
            store = {"id": code, "name": str(item.get("storeName", "麦当劳餐厅")),
                     "open": item.get("businessStatus"), "hours": str(item.get("businessStartTime", "")) + "–" + str(item.get("businessEndTime", ""))}
            self.store_cache[code] = store
            stores.append(store)
        return {"stores": stores}

    def menu(self, store):
        if store not in self.store_cache:
            raise ValueError("请先搜索并选择门店")
        client = self.get_client()
        params = dict(storeCode=store, orderType=1, beType=1)
        menu = checked_call(client, "query-meals", params)["data"]
        products = menu.get("meals", {})
        if not isinstance(products, dict):
            raise ValueError("菜单返回格式不支持")
        categories = {}
        for cat in menu.get("categories", []):
            for product in cat.get("meals", []):
                categories.setdefault(str(product.get("code")), str(cat.get("name", "其他")))
        clean = []
        for code, product in products.items():
            if not isinstance(product, dict):
                continue
            clean.append({"id": str(code), "name": str(product.get("name", "餐品")),
                          "price": str(product.get("currentPrice", "")), "category": categories.get(str(code), "其他")})
        self.menu_cache[store] = {p["id"]: p for p in clean}
        coupon_payload = checked_call(client, "query-store-coupons", params)
        raw = coupon_payload["data"]
        if not isinstance(raw, list):
            raise ValueError("券返回格式不支持")
        clean_coupons = []
        self.coupon_cache[store] = {}
        for c in raw:
            # Browser only gets a random, per-process alias, never usable coupon codes.
            alias = secrets.token_urlsafe(12)
            self.coupon_cache[store][alias] = c
            clean_coupons.append({"id": alias, "title": str(c.get("title", "优惠券")),
                                  "products": [{"id": str(v.get("productCode")), "name": str(v.get("productName", ""))} for v in c.get("products", [])]})
        return {"products": clean, "coupons": clean_coupons, "store": self.store_cache[store]}

    def calculate(self, data, client=None):
        store = str(data.get("store", ""))
        codes = data.get("products", [])
        if store not in self.menu_cache or not isinstance(codes, list) or not 1 <= len(codes) <= 5:
            raise ValueError("请先选择门店，再选择1至5种单品")
        if any(not isinstance(c, str) or c not in self.menu_cache[store] for c in codes):
            raise ValueError("所选餐品不属于当前门店，请重新选择")
        coupon = None
        coupon_product = None
        if data.get("coupon"):
            coupon = self.coupon_cache.get(store, {}).get(data["coupon"])
            if not coupon:
                raise ValueError("优惠券选择已失效，请刷新门店菜单")
            available = {str(p.get("productCode")) for p in coupon.get("products", [])}
            matching = [c for c in codes if c in available]
            if len(matching) != 1:
                raise ValueError("请选中这张券对应的一种餐品，或取消用券")
            coupon_product = matching[0]
        # The UI requests exact named products, without implicit sugar/nutrition constraints.
        need = "＋".join(self.menu_cache[store][c]["name"] for c in codes) + "；到店自取，默认规格，各1份。"
        args = SimpleNamespace(config=self.config, store=store, product=codes, coupon_product=coupon_product,
                               coupon_title=None, coupon_identity=(coupon.get("couponId"), coupon.get("couponCode")) if coupon else None,
                               budget=str(data.get("budget", "25")), needs_status="confirmed", need=need,
                               output=ROOT / "local/ui-report.html")
        doc, _ = run_live(args, client or self.get_client())
        doc["report"]["store_label"] = self.store_cache[store]["name"] + " · 到店自取"
        return {"result": compare(adapt(doc)), "report": doc["report"], "budget_fen": doc["budget_fen"],
                "mode": "live", "historical": False}


    def suggest(self, data):
        store=str(data.get("store", ""))
        if store not in self.menu_cache:
            raise ValueError("请先搜索并选择门店")
        budget=budget_fen(str(data.get("budget", "25")))
        anchor=data.get("anchor") or None

        alias=data.get("coupon") or ""
        coupon=None
        if alias:
            coupon=self.coupon_cache.get(store,{}).get(alias)
            if not coupon:
                raise ValueError("所选优惠券已失效，请刷新门店菜单")
        coupon_products={str(p.get("productCode")) for p in coupon.get("products", [])} if coupon else set()
        ordered,total=plans(self.menu_cache[store],anchor,data.get("main", "chicken"),data.get("drink", "any"),coupon_products)
        # When a chosen coupon fits a shortlisted basket, price it first; no stacking.
        if coupon:
            ordered.sort(key=lambda pair: not bool(set(pair)&coupon_products))
        if data.get("coupon_focus"):
            if not coupon or anchor not in coupon_products:
                raise ValueError("请先选定一张券及其对应餐品")
            ordered=([[anchor]]+[pair for pair in ordered if pair != [anchor]])[:6]
            total+=1
        client=MemoClient(self.get_client())
        options=[];failed=0
        for codes in ordered:
            use_coupon=alias if len(set(codes)&coupon_products)==1 else ""
            try:
                response=self.calculate(dict(store=store,products=codes,budget=str(data.get("budget", "25")),coupon=use_coupon),client)
            except ValueError:
                failed+=1
                continue
            rows=response["result"]["results"]
            # User can pick the cheaper actual payment, including not using the coupon.
            best=min(rows,key=lambda q:q["payable_fen"])
            option=dict(products=codes,names=[self.menu_cache[store][c]["name"] for c in codes],
                        payable_fen=best["payable_fen"],within_budget=best["payable_fen"]<=budget,
                        over_budget_fen=max(0,best["payable_fen"]-budget),coupon=use_coupon if best is rows[-1] and len(rows)>1 else "",
                        coupon_applied=bool(use_coupon and best is rows[-1] and len(rows)>1),
                        queried_at=response["report"]["queried_at"],comparison=response)
            options.append(option)
        options.sort(key=lambda o:(o["payable_fen"],tuple(o["products"])))
        return dict(options=options[:3],tested=len(ordered),successful=len(options),failed=failed,
                    pool_size=total,budget_fen=budget,anchor=anchor,mode="live",
                    scope="按名称与分类筛选单品；菜单价仅用于安排核验顺序。最多核验6组，非穷举、不保证最低价。围绕券的搜索可包含只买券餐品的方案。",
                    note="所选券只用于匹配餐品的方案，不适用时核验不用券价格；各方案默认规格、各1份。")


    def demo_suggestions(self, data):
        # Reuse only baskets with recorded successful quotes. Never sum fake new combinations.
        budget=budget_fen(str(data.get("budget", "25")))
        anchor=data.get("anchor") or None
        drink=data.get("drink", "any")
        main=data.get("main", "chicken")
        if main not in {"chicken", "any"} or drink not in {"any", "coffee", "tea", "soda", "water"}:
            raise ValueError("搭配偏好无效")
        variants=[(["1450","507411"],["麦香鸡","中杯冰美式"],"coffee"),(["1450","3505"],["麦香鸡","锡兰红茶"],"tea")]
        options=[]
        for codes,names,kind in variants:
            if anchor and anchor not in codes or drink not in {"any", kind}:
                continue
            if kind=="coffee":
                doc=json.loads((ROOT/"examples/coupon-price-only.json").read_text(encoding="utf-8"))
                if not data.get("coupon"):
                    doc["candidates"]=[]
                    doc["coupon_status"]="unknown"
            else:
                doc=json.loads((ROOT/"examples/latest-quotes.json").read_text(encoding="utf-8"))
                entry=copy.deepcopy(doc["candidates"][0])
                entry["meets_needs"]=True
                doc["baseline"]=entry;doc["candidates"]=[]
                doc["report"]["need"]="麦香鸡＋锡兰红茶；到店自取，只比较指定餐品的价格。"
            doc["budget_fen"]=budget
            response=dict(result=compare(adapt(doc)),report=doc["report"],budget_fen=budget,mode="demo",case="coupon",historical=True)
            rows=response["result"]["results"]
            best=min(rows,key=lambda q:q["payable_fen"])
            applied=kind=="coffee" and bool(data.get("coupon")) and best is rows[-1] and len(rows)>1
            options.append(dict(products=codes,names=names,payable_fen=best["payable_fen"],within_budget=best["payable_fen"]<=budget,
                                over_budget_fen=max(0,best["payable_fen"]-budget),coupon="demo" if applied else "",coupon_applied=applied,
                                queried_at=doc["report"]["queried_at"],comparison=response))
        options.sort(key=lambda o:o["payable_fen"])
        return dict(options=options,tested=len(options),successful=len(options),failed=0,pool_size=len(options),
                    budget_fen=budget,anchor=anchor,mode="demo",scope="只筛选两组已记录的历史报价，不查询当前菜单或推算新组合。",
                    note="各方案时间见明细；历史记录只验证该时点的价格，不代表现在可购买。")


def make_handler(service, nonce):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, status, body, kind="application/json; charset=utf-8"):
            raw = json.dumps(body, ensure_ascii=False).encode() if isinstance(body, dict) else body
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(raw)

        def valid_host(self):
            return self.headers.get("Host") == "127.0.0.1:" + str(self.server.server_port)

        def do_GET(self):
            if not self.valid_host():
                return self.send(403, {"error": "请使用终端显示的127.0.0.1地址"})
            route = urlsplit(self.path)
            if route.path == "/api/status":
                return self.send(200, {"configured": service.configured, "csrf": nonce})
            if route.path == "/api/demo":
                try:
                    q = parse_qs(route.query)
                    return self.send(200, service.demo(q.get("case", ["coupon"])[0], q.get("budget", ["25"])[0]))
                except (ValueError, KeyError, TypeError):
                    return self.send(400, {"error": "演示参数无效"})
            routes = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                      "/style.css": ("style.css", "text/css; charset=utf-8"),
                      "/buddy-rules.js": ("buddy-rules.js", "text/javascript; charset=utf-8"),
                      "/buddy.js": ("buddy.js", "text/javascript; charset=utf-8"),
                      "/meal-tools.js": ("meal-tools.js", "text/javascript; charset=utf-8")}
            if route.path in routes:
                file, kind = routes[route.path]
                return self.send(200, (ROOT / "web" / file).read_bytes(), kind)
            self.send(404, {"error": "页面不存在"})

        def do_POST(self):
            if not self.valid_host() or self.headers.get("X-Local-CSRF") != nonce:
                return self.send(403, {"error": "请求来源校验失败，请刷新页面"})
            origin = self.headers.get("Origin")
            if origin and origin != "http://127.0.0.1:" + str(self.server.server_port):
                return self.send(403, {"error": "拒绝跨站请求"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 16384:
                    raise ValueError("请求大小无效")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("请求格式无效")
                with service.lock:
                    if self.path == "/api/demo-suggest":
                        result = service.demo_suggestions(data)
                    elif self.path == "/api/stores":
                        result = service.stores(str(data.get("city", "")), str(data.get("keyword", "")))
                    elif self.path == "/api/menu":
                        result = service.menu(str(data.get("store", "")))
                    elif self.path == "/api/suggest":
                        result = service.suggest(data)
                    elif self.path == "/api/compare":
                        result = service.calculate(data)
                    else:
                        return self.send(404, {"error": "接口不存在"})
                self.send(200, result)
            except HTTPError as exc:
                self.send(502, {"error": "官方接口连接失败，HTTP " + str(exc.code) + "。请检查Token或稍后重试。"})
            except (URLError, TimeoutError):
                self.send(502, {"error": "连接超时或网络不可用，请重试。旧结果不会作为本次报价。"})
            except ValueError as exc:
                # ValueError texts originate in local validation, not raw service errors.
                safe = str(exc) if not isinstance(exc, json.JSONDecodeError) else "请求格式无效"
                self.send(400, {"error": safe})
            except (KeyError, TypeError, OSError):
                self.send(400, {"error": "配置或接口数据格式不支持，请检查本机连接配置及餐品规格。"})
    return Handler


def serve(config=None, port=8765, open_browser=False):
    service = Service(config)
    handler = make_handler(service, secrets.token_urlsafe(32))
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    url = "http://127.0.0.1:" + str(server.server_port)
    print("麦麦明白点已启动：" + url, flush=True)
    print("演示无需Token；实时查询使用启动时配置。按 Ctrl+C 结束。", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
