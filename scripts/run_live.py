"""One live query/quote/report pipeline for an explicitly selected pickup basket."""
import copy
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
import uuid
from mcp_read_client import Client, unpack
from compare_quotes import money


def budget_fen(value):
    try:
        amount = Decimal(value) * 100
        if not amount.is_finite() or amount < 0 or amount != amount.to_integral_value():
            raise ValueError("预算必须为非负金额，最多两位小数")
        return int(amount)
    except InvalidOperation:
        raise ValueError("预算格式错误") from None


def checked_call(client, name, arguments):
    payload = unpack(client.call(name, arguments))
    if payload.get("success") is not True or payload.get("code") != 200:
        # Service messages can contain private details; never print raw responses.
        raise ValueError("接口业务失败：" + name + "；请检查门店、餐品与券是否适用")
    return payload


def default_item(code, detail):
    if detail.get("rounds"):
        raise ValueError("当前入口仅支持单品默认规格，套餐请通过 Skill 查询后使用适配器")
    values = []
    for group in (detail.get("modification") or {}).get("items", []):
        options = group.get("values", [])
        selected = [v for v in options if v.get("selectedQuantity", 0) > 0]
        count = sum(v["selectedQuantity"] for v in selected)
        if options and count < group.get("minValues", 0):
            raise ValueError("餐品存在未选择的必选规格，不能自动猜测")
        for v in options:
            quantity = v.get("selectedQuantity", 0)
            if quantity > 0:
                if not v.get("selectedKey"):
                    raise ValueError("缺少默认规格参数")
                values.append(dict(code=v["code"], key=v["selectedKey"], quantity=quantity))
            elif v.get("unselectedKey"):
                values.append(dict(code=v["code"], key=v["unselectedKey"], quantity=0))
    item = dict(productCode=code, quantity=1)
    if values:
        item["modification"] = {"values": values}
    return item


def run_live(args, client=None):
    client = client or Client(args.config)
    if not args.store.isdigit():
        raise ValueError("门店编码必须为数字")
    if not args.product or len(set(args.product)) != len(args.product):
        raise ValueError("请提供不重复的单品编码；第一版每个单品数量为1")
    if args.coupon_product and args.coupon_product not in args.product:
        raise ValueError("用券商品必须属于本次选购餐品")
    budget = budget_fen(args.budget)
    common = dict(storeCode=args.store, orderType=1, beType=1)
    items, names, evidence = [], [], []
    for code in args.product:
        payload = checked_call(client, "query-meal-detail", dict(common, code=code))
        detail = payload["data"]
        if str(detail.get("code")) != code:
            raise ValueError("详情返回的商品编码不匹配")
        items.append(default_item(code, detail))
        names.append(detail["name"])
        evidence.append(dict(tool="query-meal-detail", product_code=code, success=True))
    # Coupons are held in memory only. No raw coupon identifiers reach generated files.
    coupons_payload = checked_call(client, "query-store-coupons", common)
    coupons = coupons_payload["data"]
    if not isinstance(coupons, list):
        raise ValueError("优惠券响应格式不支持")
    matching = []
    if args.coupon_product:
        matching = [c for c in coupons if any(str(v.get("productCode")) == args.coupon_product
                    for v in c.get("products", [])) and (not args.coupon_title or args.coupon_title in c.get("title", ""))]
        if len(matching) > 1:
            raise ValueError("多张券符合条件，请用 --coupon-title 缩小范围；本程序不假定其中一张更优惠")
    now = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    context = dict(store_id=args.store, dining_mode="pickup", quote_batch="live-" + uuid.uuid4().hex[:12])
    needs = {"confirmed": True, "pending": None, "rejected": False}[args.needs_status]
    record_path = Path(args.output).with_suffix(".evidence.json")
    def quote(label, actual):
        payload = checked_call(client, "calculate-price", dict(common, items=actual))
        price = money(payload["data"]["price"])
        evidence.append(dict(tool="calculate-price", label=label, success=True,
                             code=200, payable_fen=price, server_time=payload.get("datetime")))
        return dict(context, name=label + "：" + "＋".join(names), price_data={"price": price},
                    business_success=True, meets_needs=needs, evidence_ref=record_path.name,
                    basket_items=items, extra_items=[])
    direct = quote("不用券", items)
    candidates = [direct]
    coupon_status = "none_available" if not coupons else "unknown"
    if matching:
        actual = copy.deepcopy(items)
        for item in actual:
            if item["productCode"] == args.coupon_product:
                item["couponId"] = matching[0]["couponId"]
                item["couponCode"] = matching[0]["couponCode"]
        candidates.append(quote("用券", actual))
        coupon_status = "available_verified"
    evidence.append(dict(tool="query-store-coupons", returned_count=len(coupons), matched_count=len(matching)))
    base = direct if needs is True else None
    # Avoid displaying the same direct quote twice when it is also the valid baseline.
    choices = candidates[1:] if base else candidates
    doc = dict(context=context, budget_fen=budget, baseline=base, price_reference=direct,
               candidates=choices, coupon_status=coupon_status,
               data_source="项目直连麦当劳官方 MCP，以下为本轮脱敏查询结果。",
               report=dict(need=args.need, store_label="门店 " + args.store + " · 到店自取", queried_at=now,
                           data_label="真实查询结果回放，打开报告不会自动刷新价格；未下单或核销优惠券。",
                           evidence=record_path.name,
                           pending_question="你提出的部分要求尚未确认，不能仅凭餐品名称认定符合",
                           comparison_explanation="同款餐品的少付金额由两次应付报价相减；它不代表无糖等要求已经满足。"))
    return doc, dict(queried_at=now, context=context, tools=evidence,
                     limits=["单品默认规格，每件数量1，到店自取；未自动选餐、未下单", "需求符合状态由用户或Skill提供，程序不凭名称推断"])
