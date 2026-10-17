import copy
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from suggestions import plans, MAX_QUOTES
from ui_server import Service

MENU={"1":{"id":"1","name":"麦香鸡","price":"16.5"},
      "2":{"id":"2","name":"板烧鸡腿堡","price":"23.5"},
      "3":{"id":"3","name":"锡兰红茶","price":"11"},
      "4":{"id":"4","name":"中杯冰美式","price":"11.9"},
      "5":{"id":"5","name":"纯悦矿泉水","price":"7.5"}}

class MealClient:
    def __init__(self):self.calls=[];self.fail=set()
    def call(self,name,args):
        self.calls.append((name,copy.deepcopy(args)))
        if name=="query-meal-detail":
            data=dict(code=args["code"],name=MENU[args["code"]]["name"],rounds=[],modification={"items":[]})
        elif name=="query-store-coupons":
            data=[dict(title="咖啡券",couponId="PRIVATE-ID",couponCode="PRIVATE-CODE",products=[{"productCode":"4"}])]
        elif name=="calculate-price":
            ids=[i["productCode"] for i in args["items"]]
            if tuple(ids) in self.fail:return {"structuredContent":{"success":False,"code":400}}
            amount=sum(round(float(MENU[i]["price"])*100) for i in ids)
            if any("couponCode" in i for i in args["items"]):amount-=200
            data={"price":amount}
        else:raise AssertionError(name)
        return {"structuredContent":{"success":True,"code":200,"data":data}}

class SuggestionTests(unittest.TestCase):
    def service(self):
        client=MealClient();s=Service(factory=lambda:client)
        s.menu_cache["123"]=copy.deepcopy(MENU);s.store_cache["123"]={"name":"测试店"}
        s.coupon_cache["123"]={"alias":{"couponId":"PRIVATE-ID","couponCode":"PRIVATE-CODE","products":[{"productCode":"4"}]}}
        return s,client
    def test_plans_include_mcx_chicken_without_word_burger(self):
        candidates,_=plans(MENU,main="chicken")
        self.assertTrue(any(pair[0]=="1" for pair in candidates))
        self.assertLessEqual(len(candidates),MAX_QUOTES)
    def test_retain_product_in_every_plan(self):
        candidates,_=plans(MENU,anchor="4")
        self.assertTrue(candidates)
        self.assertTrue(all("4" in pair for pair in candidates))
    def test_retain_does_not_reduce_drink_preference_when_swapping_main(self):
        candidates,_=plans(MENU,anchor="1",drink="tea")
        self.assertEqual(candidates,[["1","3"]])
    def test_menu_price_not_used_as_verified_payment(self):
        s,c=self.service()
        out=s.suggest({"store":"123","budget":"27","coupon":"alias","drink":"coffee"})
        self.assertEqual(out["options"][0]["payable_fen"],2640)
        self.assertTrue(out["options"][0]["coupon_applied"])
        self.assertNotIn("PRIVATE",str(out))
        self.assertTrue(any(name=="calculate-price" for name,_ in c.calls))
    def test_preserved_and_budget_filter_uses_actual_quote(self):
        s,c=self.service();out=s.suggest({"store":"123","budget":"25","anchor":"1"})
        self.assertTrue(all("1" in o["products"] for o in out["options"]))
        self.assertEqual(out["options"][0]["payable_fen"],2400)
        self.assertTrue(out["options"][0]["within_budget"])
        self.assertEqual(sum(name=="query-store-coupons" for name,_ in c.calls),1)
    def test_quote_failure_is_not_silently_replaced_with_menu_sum(self):
        s,c=self.service();c.fail={("1","3")}
        out=s.suggest({"store":"123","budget":"25","anchor":"1","drink":"tea"})
        self.assertEqual(out["options"],[]);self.assertEqual(out["failed"],1)
    def test_no_preference_match_produces_no_made_up_option(self):
        s,_=self.service();out=s.suggest({"store":"123","drink":"soda"})
        self.assertEqual(out["options"],[])
    def test_unknown_store_and_coupon_rejected(self):
        s,_=self.service()
        for data in [{"store":"wrong"},{"store":"123","coupon":"wrong"}]:
            with self.assertRaises(ValueError):s.suggest(data)
    def test_demo_suggestions_use_only_recorded_baskets(self):
        s=Service();out=s.demo_suggestions({"budget":"27","coupon":"demo","anchor":"1450"})
        self.assertEqual([o["payable_fen"] for o in out["options"]],[2640,2750])
        self.assertEqual([o["within_budget"] for o in out["options"]],[True,False])
        self.assertEqual(s.demo_suggestions({"budget":"27","drink":"water"})["options"],[])

    def test_coupon_focus_includes_verified_single_item_not_inferred_subtotal(self):
        s,c=self.service();out=s.suggest({"store":"123","budget":"12","anchor":"4","coupon":"alias","coupon_focus":True})
        first=out["options"][0]
        self.assertEqual(first["products"],["4"])
        self.assertEqual(first["payable_fen"],990)
        self.assertTrue(any(name=="calculate-price" and len(args["items"])==1 for name,args in c.calls))
