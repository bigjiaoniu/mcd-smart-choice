"""Render a standalone offline HTML report. No network calls or model usage."""
import argparse
from html import escape
import json
from pathlib import Path
from adapt_quotes import adapt
from compare_quotes import compare


def text(value):
    return escape(str(value), quote=True)


def yuan(value):
    return f"¥{value // 100}.{value % 100:02d}"


def render(document, adapted=False):
    normalized = adapt(document) if adapted else document
    result = compare(normalized)
    meta = document.get("report", {})
    rows = result["results"]
    ref = normalized.get("price_reference") or normalized.get("baseline")
    savings = [q.get("same_basket_saving_fen") if q.get("same_basket_saving_fen") is not None
               else q.get("saving_fen") for q in rows]
    positive = [v for v in savings if v is not None and v > 0]
    headline = "用券少付 " + yuan(max(positive)) if positive else "这次点餐，多少钱？"
    intro = "同一份餐，对比用券前后的实际付款。" if positive else "看实际付款，再决定怎么选。"
    record_tag = "模拟演示" if any(w in normalized.get("data_source", "") for w in ("虚构", "模拟")) else "历史报价"
    pending = meta.get("pending_question", "还有餐品要求待确认")
    output_rows = []
    for i, q in enumerate(rows):
        is_ref = ref is not None and q["name"] == ref["name"]
        saving = savings[i]
        difference = "—"
        if saving is not None and not is_ref:
            difference = ("少花 " + yuan(saving)) if saving > 0 else (("多花 " + yuan(-saving)) if saving < 0 else "花费相同")
        budget = "预算内" if q["within_budget"] else "超出 " + yuan(q["over_budget_fen"])
        notes = []
        if "需求属性待确认" in q["reasons"]:
            notes.append(pending)
        for reason in q["reasons"]:
            if reason not in {"需求属性待确认", "超预算"}:
                notes.append({"不满足原始需求": "不符合你的餐品要求", "报价未核验": "付款金额未确认",
                              "报价上下文不一致": "查询条件不同，不能直接比价"}.get(reason, reason))
        if q["extra_items"]:
            notes.append("多买了：" + "、".join(q["extra_items"]))
        note = f'<p class="item-note">{text("；".join(notes))}</p>' if notes else ""
        style = "receipt-row chosen" if saving is not None and saving > 0 else "receipt-row"
        output_rows.append(f'<div class="{style}"><div class="item"><h3>{text(q["name"])}</h3>{note}</div>'
                           f'<div class="amount">{yuan(q["payable_fen"])}</div>'
                           f'<div class="difference">{difference}<small>{budget}</small></div></div>')
    if not rows:
        output_rows.append('<p class="empty">还没有成功报价，请先查询餐品价格。</p>')
    picks = "、".join(result["lowest_verified_options"])
    advice = ("本次符合要求且在预算内的方案中，可以选：" + picks) if picks else meta.get("no_option_advice", "本次还没有符合全部要求、且在预算内的方案。可以继续找其他搭配，预算由你决定。")
    css = Path(__file__).with_name("report.css").read_text(encoding="utf-8")
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>麦麦明白点 · 用券对比</title><style>{css}</style></head><body>
<header class="topbar"><div class="topbar-inner"><div class="wordmark"><span class="mark">券</span>麦麦明白点</div><span class="project-label">独立开发 · 非官方产品</span></div></header>
<main><div class="breadcrumb">点餐账单 / 用券对比</div>
<section class="heading"><div><h1>{headline}</h1><p>{intro}</p></div><span class="record-tag">{record_tag}</span></section>
<section class="receipt"><div class="receipt-head"><span class="section-label">这次想吃</span><p>{text(meta.get('need', '餐品见下方报价'))}</p><div class="store">{text(meta.get('store_label', '门店见查询记录'))}<span>预算 {yuan(normalized['budget_fen'])}</span></div></div>
<div class="table-label"><span>买法 / 餐品</span><span>实际付款</span><span>差额 / 预算</span></div>
{''.join(output_rows)}
<div class="receipt-bottom"><span>只比较这次查到的方案</span><span>报价时间 {text(meta.get('queried_at', '见查询记录'))}</span></div></section>
<section class="conclusion"><span class="conclusion-label">怎么算更明白</span><p>{text(advice)}</p></section>
<p class="explanation">{text(meta.get('comparison_explanation', '别只看券面优惠：最后少付多少钱，有没有多买东西，才是这次比较的重点。'))}</p>
<details class="data-details"><summary>查看数据来源与使用说明</summary><p>{text(meta.get('data_label', '离线报告，不会自动刷新价格。'))}</p><p>{text(normalized.get('data_source', '未说明'))}</p><p>{text(meta.get('evidence', '请查阅输入中的证据引用'))}</p></details>
<footer>非麦当劳官方产品。历史报价仅供参考，价格及优惠以官方实时结果为准。此报告不下单、不核销券。</footer>
</main></body></html>"""


def main():
    parser = argparse.ArgumentParser(description="生成离线中文报价报告，不调用 MCP")
    parser.add_argument("input", type=Path)
    parser.add_argument("--adapted", action="store_true", help="输入为适配器格式，含 price_data")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    document = json.loads(args.input.read_text(encoding="utf-8"))
    html = render(document, adapted=args.adapted)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print("HTML report created.")


if __name__ == "__main__":
    main()
