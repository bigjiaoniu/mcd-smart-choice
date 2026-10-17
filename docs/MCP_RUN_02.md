# MCP_RUN_02 — 真实报价→适配→本地计算 全链路验证

> 本文件记录 2026-10-17 第四轮真实 MCP 调用、脱敏适配输入和本地代码运行的完整证据。
> 不含 Token、账号、完整券码、私人地址或完整原始响应。

## 查询环境

| 项目 | 值 |
|------|-----|
| 日期时间 | 2026-10-17 12:32:34 ~ 12:32:41 (GMT+8) |
| 连接器 | mcp__mcd-mcp |
| 门店 | 世界城广场餐厅 (storeCode=1960088) |
| 就餐方式 | 到店自取 (beType=1, orderType=1, 不传 beCode) |
| quote_batch | mcp-run-02-2026-10-17 |

## 工具调用记录

### 1. query-meals — 重新查询当前菜单

| 项目 | 值 |
|------|-----|
| 工具 | mcp__mcd-mcp__query-meals |
| 参数 | storeCode=1960088, orderType=1, beType=1 |
| 调用时间 | 2026-10-17 12:32:34 |
| traceId | 8c62a08281d0121a84d7a05d6adfd9a7 |
| success | true |
| code | 200 |
| 结果 | 菜单返回成功，鸡肉汉堡和饮品分类中目标餐品仍在售 |

菜单确认（目标餐品仍可售）：

| 餐品 | code | currentPrice(元) |
|------|------|-----------------|
| 麦香鸡 | 1450 | 16.5 |
| 锡兰红茶 | 3505 | 11.0 |
| 麦咖啡™美式 | 507411 | 11.9 (促销价, 原价19) |

### 2. calculate-price — 报价1：麦香鸡＋锡兰红茶

| 项目 | 值 |
|------|-----|
| 工具 | mcp__mcd-mcp__calculate-price |
| 参数 | storeCode=1960088, orderType=1, beType=1, items=[{productCode:1450,qty:1},{productCode:3505,qty:1}] |
| 调用时间 | 2026-10-17 12:32:41 |
| traceId | 487a6daed68b9cf4d13df2a839e57408 |
| success | true |
| code | 200 |

实际返回价格字段（整数分）：

| 字段 | 值(分) | 值(元) |
|------|--------|--------|
| originalPrice | 2750 | 27.50 |
| productOriginalPrice | 2750 | 27.50 |
| productPrice | 2750 | 27.50 |
| discount | 0 | 0.00 |
| price | **2750** | **27.50** |

productList 明细：
- 麦香鸡(1450): originalSubtotal=1650, subtotal=1650
- 锡兰红茶(3505): originalSubtotal=1100, subtotal=1100

takeWayList: [堂食(eat-in), 外带(locker-in)]

**业务成功判断依据：** success=true, code=200, price 字段为非负整数分(2750)，productList 含两件商品且 subtotal 之和等于 price。无 deliveryPrice/packingPrice（到店自取）。

### 3. calculate-price — 报价2：麦香鸡＋冰美式中杯

| 项目 | 值 |
|------|-----|
| 工具 | mcp__mcd-mcp__calculate-price |
| 参数 | storeCode=1960088, orderType=1, beType=1, items=[{productCode:1450,qty:1},{productCode:507411,qty:1}] |
| 调用时间 | 2026-10-17 12:32:41 |
| traceId | f34e0e453fbc226ed0d798dbafb52ede |
| success | true |
| code | 200 |

实际返回价格字段（整数分）：

| 字段 | 值(分) | 值(元) |
|------|--------|--------|
| originalPrice | 3550 | 35.50 |
| productOriginalPrice | 3550 | 35.50 |
| productPrice | 2840 | 28.40 |
| discount | 710 | 7.10 (促销优惠) |
| price | **2840** | **28.40** |

productList 明细：
- 麦香鸡(1450): originalSubtotal=1650, subtotal=1650
- 麦咖啡™冰美式中杯(507411): originalSubtotal=1900, subtotal=1190

takeWayList: [堂食(eat-in), 外带(locker-in)]

**业务成功判断依据：** success=true, code=200, price 字段为非负整数分(2840)，productList 含两件商品，subtotal 之和(1650+1190=2840)等于 price，discount(710)等于 originalPrice-price(3550-2840)。

## 需求符合状态

| 组合 | 含糖量 | meets_needs | 原因 |
|------|--------|-------------|------|
| 麦香鸡＋锡兰红茶 | 待确认 | null | 本次查询的菜单和详情未发现含糖量字段；不根据名称判断 |
| 麦香鸡＋冰美式中杯 | 待确认 | null | 同上；modification 仅含冰量选项，无糖量字段 |

baseline=null — 无有效基线（本次核验的两个组合均超25元预算，含糖量待确认）。

## 适配输入

文件：examples/latest-quotes.json

- price_data.price 使用 calculate-price 实际返回的整数分（2750, 2840）
- business_success=true（依据：success=true, code=200, price 为非负整数分，subtotal 之和等于 price）
- evidence_ref 指向本文档对应报价编号
- meets_needs=null（含糖量待确认）
- baseline=null（无有效基线）
- context: store_id=1960088, dining_mode=pickup, quote_batch=mcp-run-02-2026-10-17
- coupon_status=none_available（前轮验证门店和卡包均无券）

## 程序运行结果

### adapt_quotes.py

```
python scripts/adapt_quotes.py examples/latest-quotes.json
```

输出（JSON）：

```json
{
  "status": "no_eligible_option",
  "baseline_status": "unavailable",
  "coupon_status": "none_available",
  "results": [
    {
      "name": "麦香鸡＋锡兰红茶",
      "payable_fen": 2750,
      "qualified": false,
      "within_budget": false,
      "over_budget_fen": 250,
      "reasons": ["需求属性待确认", "超预算"]
    },
    {
      "name": "麦香鸡＋冰美式中杯",
      "payable_fen": 2840,
      "qualified": false,
      "within_budget": false,
      "over_budget_fen": 340,
      "reasons": ["需求属性待确认", "超预算"]
    }
  ],
  "lowest_verified_options": [],
  "scope": "仅比较输入的已核验候选，不保证全局最低价；无有效基线时不计算节省金额；核验标记由调用方负责提供证据"
}
```

### unittest

```
python -m unittest discover -s tests -v
```

```
Ran 13 tests in 0.003s
OK
```

13 个测试全部通过，包括 test_no_baseline_and_pending_needs（无有效基线+需求待确认场景）。

## 修改的文件

| 文件 | 操作 | 说明 |
|------|------|------|
| examples/latest-quotes.json | 新建 | 本轮真实报价的脱敏适配输入 |
| docs/MCP_RUN_02.md | 新建 | 本文件 |

未修改 scripts/adapt_quotes.py、scripts/compare_quotes.py、CONTEST_DECLARATION.md。

## 未验证项

1. **用券报价链路**：门店和卡包均无券，calculate-price + couponId/couponCode 未实际触发
2. **含糖量**：本次查询的菜单和详情未发现含糖量字段，所有茶/咖啡含糖量待确认。官方另有 list-nutrition-foods 工具，未验证其是否提供糖含量及规格匹配
3. **套餐子项 roundList**：本次使用单品，未涉及套餐选配
4. **不宣称穷举**：本次仅核验两个组合，不宣称不存在其他可能满足需求的组合
