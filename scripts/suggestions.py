"""Bounded meal search. Menu prices order candidates; only actual quotes become results."""
import itertools
import json
import re
from run_live import budget_fen

MAX_QUOTES = 6


def kind(product):
    name = product["name"]
    # Only textual menu cues, not inferred nutrition or verified ingredients.
    if re.search(r"套餐|双人|三人|四人|拼盘|精选|组合", name):
        return None
    if re.search(r"美式|咖啡|拿铁|奶铁|浓缩|红茶|绿茶|可乐|雪碧|纯悦|饮料|柠柠|橙橙|汽水", name):
        return "drink"
    if re.search(r"堡|汉堡|麦香鸡|鸡肉卷|鸡腿卷|多笋卷|麦满分", name):
        return "main"
    return None


def matches(product, category, preference):
    if kind(product) != category:
        return False
    name = product["name"]
    if category == "main":
        return preference == "any" or bool(re.search(r"鸡|板烧|多笋", name))
    patterns = {"coffee": r"美式|咖啡|拿铁|奶铁|浓缩", "tea": r"茶", "soda": r"可乐|雪碧|汽水", "water": r"纯悦|矿泉水"}
    return preference == "any" or bool(re.search(patterns[preference], name))


def plans(menu, anchor=None, main="chicken", drink="any", preferred=None):
    if main not in {"chicken", "any"} or drink not in {"any", "coffee", "tea", "soda", "water"}:
        raise ValueError("搭配偏好无效")
    if anchor is not None and anchor not in menu:
        raise ValueError("要保留的餐品不属于当前门店")
    mains = [p for p in menu.values() if matches(p, "main", main)]
    drinks = [p for p in menu.values() if matches(p, "drink", drink)]
    if anchor:
        product = menu[anchor]
        category = kind(product)
        if category == "main":
            mains = [product]  # Retained item wins over discovery preferences.
        elif category == "drink":
            drinks = [product]
        else:
            raise ValueError("目前支持保留一种汉堡/卷或饮品，套餐和小食暂不支持")
    candidates=[]
    for a,b in itertools.product(mains, drinks):
        try:
            rank = budget_fen(a["price"]) + budget_fen(b["price"])
        except (ValueError, TypeError):
            continue
        if a["id"] != b["id"]:
            candidates.append((rank,[a["id"],b["id"]]))
    candidates.sort(key=lambda item: (not bool(set(item[1]) & set(preferred or [])), item[0], tuple(item[1])))
    # Test several drinks instead of spending all requests on near-identical mains.
    ordered=[];seen=set()
    for _, pair in candidates:
        varying = pair[1] if not anchor or kind(menu[anchor]) == "main" else pair[0]
        if varying not in seen:
            ordered.append(pair);seen.add(varying)
        if len(ordered) >= MAX_QUOTES:
            break
    for _, pair in candidates:
        if pair not in ordered:
            ordered.append(pair)
        if len(ordered) >= MAX_QUOTES:
            break
    return ordered[:MAX_QUOTES], len(candidates)


class MemoClient:
    """Within one request only; keep credentials and full coupon codes in memory."""
    def __init__(self, client):
        self.client=client
        self.memo={}
    def call(self, name, arguments):
        if name not in {"query-meal-detail", "query-store-coupons"}:
            return self.client.call(name, arguments)
        key=(name,json.dumps(arguments,sort_keys=True))
        if key not in self.memo:
            self.memo[key]=self.client.call(name,arguments)
        return self.memo[key]
