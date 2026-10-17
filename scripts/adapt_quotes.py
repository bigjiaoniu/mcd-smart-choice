"""Normalize explicitly checked, sanitized calculate-price payloads, not live MCP calls."""
import json
import sys


def basket_signature(items):
    if not items:
        return None
    if not isinstance(items, list):
        raise ValueError("basket_items 必须为列表")
    clean = []
    for item in items:
        if not isinstance(item.get("productCode"), str) or not item["productCode"]:
            raise ValueError("缺少商品编码")
        if type(item.get("quantity")) is not int or item["quantity"] <= 0:
            raise ValueError("商品数量必须为正整数")
        # Exact selected modifiers are part of the identity; coupon identifiers are not.
        clean.append({k: item[k] for k in ("productCode", "quantity", "modification", "roundList") if k in item})
    return json.dumps(sorted(clean, key=lambda x: json.dumps(x, sort_keys=True)), sort_keys=True)
from compare_quotes import compare, money


def normalize_quote(entry, context):
    # The caller must unwrap the actual MCP envelope and check tool/business errors.
    # HTTP 200 or the presence of a price field alone is not success evidence.
    if entry.get("business_success") is not True:
        raise ValueError("必须先确认工具和业务调用成功，失败响应不得作为报价")
    if not isinstance(entry.get("evidence_ref"), str) or not entry["evidence_ref"].strip():
        raise ValueError("缺少脱敏报价证据引用")
    raw = entry["price_data"]
    amount = money(raw["price"])
    needs = entry.get("meets_needs")
    if needs is not None and type(needs) is not bool:
        raise ValueError("meets_needs 只能为 true、false 或 null（待确认）")
    for key in ("store_id", "dining_mode", "quote_batch"):
        if entry.get(key) != context.get(key) or not context.get(key):
            raise ValueError("报价上下文缺失或不一致: " + key)
    # Whitelist fields: do not copy raw payloads, coupon codes or account data.
    return dict(name=entry["name"], payable_fen=amount, verified=True,
                meets_needs=needs, store_id=entry["store_id"],
                dining_mode=entry["dining_mode"], quote_batch=entry["quote_batch"],
                extra_items=entry.get("extra_items", []),
                basket_signature=basket_signature(entry.get("basket_items")))


def adapt(document):
    context = document["context"]
    baseline = document.get("baseline")
    return dict(budget_fen=money(document["budget_fen"]), context=context,
                baseline=normalize_quote(baseline, context) if baseline else None,
                price_reference=normalize_quote(document["price_reference"], context) if document.get("price_reference") else None,
                candidates=[normalize_quote(q, context) for q in document.get("candidates", [])],
                coupon_status=document.get("coupon_status", "unknown"),
                data_source=document.get("data_source", "unspecified"))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        with open(sys.argv[1], encoding="utf-8") as handle:
            print(json.dumps(compare(adapt(json.load(handle))), ensure_ascii=False, indent=2))
    except (IndexError, OSError, ValueError, KeyError, TypeError) as exc:
        print("输入错误: " + str(exc), file=sys.stderr)
        sys.exit(1)
