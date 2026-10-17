"""Compare normalized quotes; does not call MCP or verify source evidence."""
import json
import sys


def money(value):
    if type(value) is not int or value < 0:
        raise ValueError("金额必须是非负整数分")
    return value


def compare(data):
    budget = money(data["budget_fen"])
    base = data.get("baseline")
    context = data.get("context") or base
    if context is None:
        raise ValueError("无基线时必须提供 context")
    for key in ("store_id", "dining_mode", "quote_batch"):
        if not context.get(key):
            raise ValueError("缺少报价上下文: " + key)
    valid_base = (base is not None and base.get("verified") is True
                  and base.get("meets_needs") is True
                  and all(base.get(k) == context[k] for k in ("store_id", "dining_mode", "quote_batch")))
    if base is not None:
        money(base["payable_fen"])
    reference = data.get("price_reference")
    if reference is not None:
        money(reference["payable_fen"])
    results = []
    quotes = ([base] if base is not None else []) + data.get("candidates", [])
    for quote in quotes:
        amount = money(quote["payable_fen"])
        same_context = all(quote.get(k) == context[k] for k in ("store_id", "dining_mode", "quote_batch"))
        qualified = quote.get("verified") is True and quote.get("meets_needs") is True and same_context
        reasons = []
        if quote.get("verified") is not True:
            reasons.append("报价未核验")
        if quote.get("meets_needs") is False:
            reasons.append("不满足原始需求")
        elif quote.get("meets_needs") is not True:
            reasons.append("需求属性待确认")
        if not same_context:
            reasons.append("报价上下文不一致")
        if amount > budget:
            reasons.append("超预算")
        comparable = qualified and valid_base
        same_basket = (reference is not None and reference.get("verified") is True
                       and quote.get("verified") is True and same_context
                       and all(reference.get(k) == context[k] for k in ("store_id", "dining_mode", "quote_batch"))
                       and bool(reference.get("basket_signature"))
                       and reference.get("basket_signature") == quote.get("basket_signature"))
        results.append({"name": quote["name"], "payable_fen": amount,
                        "qualified": qualified, "comparable": comparable,
                        "within_budget": amount <= budget,
                        "over_budget_fen": max(0, amount - budget),
                        "saving_fen": base["payable_fen"] - amount if comparable else None,
                        "same_basket_saving_fen": reference["payable_fen"] - amount if same_basket else None,
                        "extra_items": quote.get("extra_items", []), "reasons": reasons})
    eligible = [q for q in results if q["qualified"] and q["within_budget"]]
    lowest = min((q["payable_fen"] for q in eligible), default=None)
    return {"data_source": data.get("data_source", "unspecified"),
            "status": "options_found" if eligible else "no_eligible_option",
            "baseline_status": "valid" if valid_base else "unavailable",
            "coupon_status": data.get("coupon_status", "unknown"),
            "results": results,
            "lowest_verified_options": [q["name"] for q in eligible if q["payable_fen"] == lowest],
            "scope": "仅比较输入的已核验候选，不保证全局最低价；无有效基线时不计算节省金额；核验标记由调用方负责提供证据"}


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        with open(sys.argv[1], encoding="utf-8") as handle:
            print(json.dumps(compare(json.load(handle)), ensure_ascii=False, indent=2))
    except (IndexError, OSError, ValueError, KeyError, TypeError) as exc:
        print("输入错误: " + str(exc), file=sys.stderr)
        sys.exit(1)
