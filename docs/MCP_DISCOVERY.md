# 麦当劳 MCP 接口发现记录

> 本文件记录 WorkBuddy 对麦当劳 MCP 连接器的真实调用验证结果。
> 仅保留脱敏字段结构和通用餐品信息，不含 Token、账号、手机号、详细地址或完整原始响应。

## 验证环境

- 验证时间：2026-10-17 12:09 ~ 12:23 (GMT+8)，分三轮
- 连接器：mcp__mcd-mcp（Streamable HTTP，服务端 mcp.mcd.cn）
- 验证场景：到店自取 (beType=1, orderType=1)
- 验证门店：麦当劳武汉世界城广场餐厅 (storeCode=1960088)
- 调用工具数：10（query-nearby-stores, query-meals, query-store-coupons, query-meal-detail×4, calculate-price×3, available-coupons, query-my-coupons）

## 工具 Schema 摘要

### 1. query-nearby-stores — 查询附近门店

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| beType | int | 是 | 1=到店自取, 5=得来速 |
| searchType | int | 是 | 1=收藏餐厅, 2=按位置搜索 |
| city | string | searchType=2时必填 | 城市名 |
| keyword | string | searchType=2时必填 | 位置关键词 |

**返回结构（data[] 数组）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| storeCode | string | 门店唯一编码，后续工具入参 |
| storeName | string | 门店名称 |
| address | string | 门店地址 |
| distance | int | 距离（米） |
| businessStatus | bool | 营业状态 |
| businessStartTime | string | 营业开始时间 |
| businessEndTime | string | 营业结束时间 |
| reservation | bool | 是否支持预约 |
| reservationTimeOptions | array | 预约时段选项 |
| beCode | string | 业务编码（beType=5时返回，beType=1时无此字段） |

**验证结果：** ✅ 成功。传入 city="武汉", keyword="光谷世界城步行街", beType=1, searchType=2，返回5家门店。

### 2. query-meals — 查询门店菜单

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeCode | string | 是 | 门店编码 |
| orderType | int | 是 | 1=到店, 2=外送 |
| beType | int | 是 | 1=到店取餐, 2=麦乐送, 5=得来速, 6=团餐 |
| beCode | string | 条件必填 | 得来速/外送/团餐必传；到店自取不传 |
| reservationDate | string | 否 | 预约场景必传，格式 yyyy-MM-dd HH:mm |

**返回结构（data 对象）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| categories | array | 菜单分类列表 |
| categories[].name | string | 分类名称（如"鸡肉汉堡/卷"） |
| categories[].meals | array | 该分类下餐品列表 |
| categories[].meals[].code | string | 餐品唯一编码 |
| categories[].meals[].tags | array | 餐品标签 |
| meals | object | 餐品详情映射表，key=餐品code |
| meals.{code}.name | string | 餐品名称 |
| meals.{code}.currentPrice | string | 现价（元，字符串） |
| meals.{code}.originalPrice | string | 原价/划线价（元，字符串） |
| meals.{code}.discountType | string/null | 优惠类型（null/促销优惠/麦金卡优惠/随单购麦金卡优惠等） |
| meals.{code}.canWithOrder | bool | 是否可随单购 |
| meals.{code}.withOrder | object/null | 随单购信息（membershipCode, specId等） |
| frequent | object | 常点餐品 |

**验证结果：** ✅ 成功。返回完整菜单，包含18个分类、约90+餐品。分类包括：人气热卖、小食拼盘/多人餐、精选单人餐、鸡肉汉堡/卷、蘸酱炸鸡、随心配1+1、巨无霸/牛鱼肉堡、安格斯MAX厚牛堡、炸鸡、开心乐园、小食甜品/其他、麦咖啡™、500大卡套餐、饮品等。

### 3. query-store-coupons — 查询门店可用券

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeCode | string | 是 | 门店编码（纯数字） |
| orderType | int | 是 | 1=到店, 2=外送 |
| beType | int | 是 | 业务类型 |
| beCode | string | 条件必填 | 得来速/外送/团餐必传 |
| reservationDate | string | 否 | 预约场景必传 |

**返回结构（data[] 数组）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| title | string | 券名称 |
| couponId | string | 券ID（分组标识） |
| couponCode | string | 券码（同一券ID可对应多个券码） |
| tradeDateTime | string | 有效期 |
| products | array | 适用商品列表 |
| products[].productName | string | 适用商品名称 |
| products[].productCode | string | 适用商品编码 |

**验证结果：** ✅ 调用成功（HTTP 200），但 `data` 返回空数组 `[]`。该门店当前到店自取场景下无可用优惠券。

### 4. query-meal-detail — 查询餐品详情

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeCode | string | 是 | 门店编码 |
| orderType | int | 是 | 1=到店, 2=外送 |
| beType | int | 是 | 业务类型 |
| code | string | 是 | 餐品唯一编码 |
| beCode | string | 条件必填 | 得来速/外送/团餐必传 |
| reservationDate | string | 否 | 预约场景必传 |

**返回结构（data 对象）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| code | string | 餐品编码 |
| name | string | 餐品名称 |
| image | string | 商品图片URL |
| supportModify | bool | 是否支持特调 |
| rounds | array | 选配轮次（单品为空数组，套餐有内容） |
| modification | object | 特制选项 |
| modification.items | array | 特调项列表 |
| modification.items[].maxValues | int | 最大选择数 |
| modification.items[].minValues | int | 最小选择数 |
| modification.items[].values | array | 特调商品列表 |
| modification.items[].values[].code | string | 特调商品编码 |
| modification.items[].values[].name | string | 特调项名称 |
| modification.items[].values[].price | int | 特调差价（分） |
| modification.items[].values[].selectedQuantity | int | 默认选中数量 |
| modification.items[].values[].selectedKey | string | 选中时传给calculate-price的key |
| modification.items[].values[].unselectedKey | string | 未选中时传给calculate-price的key |

**验证结果：** ✅ 成功。以麦香鸡(code=1450)为例，返回 supportModify=true，modification含2个特调组：麦香鸡酱(code=100136)和生菜(code=100168)，均可选/可不选，price=0（无差价），selectedKey="0-1"，unselectedKey="0-0"。

### 5. calculate-price — 价格计算（含优惠）

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeCode | string | 是 | 门店编码 |
| orderType | int | 是 | 1=到店, 2=外送 |
| beType | int | 是 | 业务类型 |
| items | array | 是 | 商品列表 |
| items[].productCode | string | 是 | 商品编码 |
| items[].quantity | int | 是 | 数量(≥1) |
| items[].couponId | string | 否 | 优惠券ID |
| items[].couponCode | string | 否 | 优惠券编码 |
| items[].modification | object | 否 | 特制选项 |
| items[].modification.values[] | array | 否 | 特调项列表 |
| items[].modification.values[].code | string | 是 | 特调商品code |
| items[].modification.values[].key | string | 是 | 特调key（选中用selectedKey，未选中用unselectedKey） |
| items[].modification.values[].quantity | int | 是 | 特调数量 |
| items[].roundList | array | 否 | 套餐子项 |
| beCode | string | 条件必填 | 得来速/外送/团餐必传 |
| reservationDate | string | 否 | 预约场景必传 |
| needTableware | bool | 否 | 是否需要餐具费 |
| withOrder | object | 否 | 随单购商品 |
| gmServiceCode | string | 否 | 团餐助餐服务code |

**返回结构（data 对象）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| productOriginalPrice | int | 商品原价（分） |
| productPrice | int | 商品现价（分） |
| originalPrice | int | 订单原价（分） |
| discount | int | 优惠金额（分） |
| price | int | 现价/应付金额（分） |
| productList | array | 商品明细列表 |
| productList[].productCode | string | 商品编码 |
| productList[].productName | string | 商品名称 |
| productList[].quantity | int | 数量 |
| productList[].originalSubtotal | int | 商品原小计（分） |
| productList[].subtotal | int | 商品小计（分） |
| takeWayList | array | 取餐方式选项 |
| takeWayList[].code | string | 取餐方式code |
| takeWayList[].title | string | 取餐方式标题 |
| takeWayList[].subtitle | string | 取餐方式副标题 |
| enjoyed | object | 已享受的优惠 |
| enjoyed.amountType | string | 1=特价 2=折扣 3=立减 |
| enjoyed.realDiscount | number | 实际优惠值（元） |
| enjoyed.balance | int | 门槛差额（分） |
| enjoyable | object | 可享受的优惠（未达门槛） |
| deliveryPrice | int | 运费（分，外送场景） |
| packingPrice | int | 打包费（分） |
| tablewarePrice | int | 餐具费（分） |

**验证结果：** ✅ 成功。以麦香鸡(1450)x1 + 纯悦(3757)x1 为例：
- productPrice=2400（24.00元）
- originalPrice=2400, discount=0, price=2400
- productList: [麦香鸡 1650分, 纯悦 750分]
- takeWayList: [堂食(eat-in), 外带(locker-in)]
- 无 deliveryPrice/packingPrice（到店自取无运费和打包费）

## 基线报价验证

### 需求
一个鸡肉汉堡 + 一杯无糖饮料，预算25元，到店自取。

### 候选分析

**鸡肉汉堡单品（"鸡肉汉堡/卷"分类）：**

| 餐品名称 | code | 现价(元) |
|---------|------|---------|
| 麦香鸡 | 1450 | 16.5 |
| 酥酥多笋卷 | 521816 | 20.5 |
| 麦辣鸡腿汉堡 | 1440 | 22.5 |
| 板烧鸡腿堡 | 1406 | 23.5 |
| 鸡肉堡单品精选 | 9900008746 | 23.5 |
| 龙焰鸡腿堡 | 521952 | 24.0 |

**茶/咖啡/汽水类饮料候选（含糖量均为待确认，MCP 返回无含糖量字段）：**

| 餐品名称 | code | 现价(元) | 含糖量 | 备注 |
|---------|------|---------|--------|------|
| 纯悦（矿泉水） | 3757 | 7.5 | 不适用 | 瓶装水，本次需求不接受 |
| 锡兰红茶 | 3505 | 11.0 | 待确认 | supportModify=false，无糖量字段 |
| 麦咖啡™冰美式中杯 | 507411 | 11.9 | 待确认 | modification 仅冰量选项(标准/去冰/多冰/少冰)，无糖量选项 |
| 浓缩咖啡 | 507389 | 15.0 | 待确认 | supportModify=false，无糖量字段 |
| 麦咖啡™奶铁 | 507409 | 13.9 | 待确认 | 促销价，无糖量字段 |
| 雪碧 | 3060 | 10.0 | 待确认 | 汽水，无糖量字段 |
| 可乐 | 9900008751 | 9.5 | 待确认 | 汽水，无糖量字段 |
| 怡泉+C | 515520 | 11.5 | 待确认 | 汽水，无糖量字段 |

> 本次查询的菜单(query-meals)和餐品详情(query-meal-detail)未发现含糖量相关字段。query-meal-detail 返回的 modification 仅包含冰量、酱料等特调选项。官方另有 list-nutrition-foods 工具，未验证其是否提供糖含量及规格匹配。因此所有茶/咖啡/汽水的含糖量均标记"待确认"，不根据名称自行判断。

**已核验报价的组合：**

| 组合 | 菜单价合计(元) | 报价应付(元) | 优惠(元) | 预算内 | 含糖量 | 满足需求 |
|------|--------------|-------------|---------|--------|--------|---------|
| 麦香鸡 + 纯悦 | 24.0 | 24.00 | 0.00 | ✅ | 不适用 | ❌ 不接受瓶装水 |
| 麦香鸡 + 锡兰红茶 | 27.5 | 27.50 | 0.00 | ❌ | 待确认 | ❌ 超预算 |
| 麦香鸡 + 麦咖啡™冰美式 | 28.4 | 28.40 | 7.10(促销) | ❌ | 待确认 | ❌ 超预算 |

> 注意：以上为已核验报价的部分组合，并非穷举。不宣称最低价或最低预算。

### 基线核验结果

**历史基线方案：麦香鸡 + 纯悦（已标记为不满足本次需求）**

| 项目 | 值 |
|------|-----|
| 门店 | 世界城广场餐厅 (1960088) |
| 就餐方式 | 到店自取 (beType=1, orderType=1) |
| 餐品1 | 麦香鸡 (code=1450, qty=1) |
| 餐品2 | 纯悦 (code=3757, qty=1) |
| 商品原价 | 2400分 (24.00元) |
| 优惠 | 0分 (0.00元) |
| 应付金额 | 2400分 (24.00元) |
| 预算 | 2500分 (25.00元) |
| 预算内 | ✅ 是 |
| 满足需求 | ❌ 否 — 纯悦为瓶装水，本次需求不接受 |
| 调用时间 | 2026-10-17 12:13:03 |

> 保留此报价记录作为历史数据，但不作为有效基线。

**追加核验：麦香鸡 + 锡兰红茶**

| 项目 | 值 |
|------|-----|
| 门店 | 世界城广场餐厅 (1960088) |
| 就餐方式 | 到店自取 (beType=1, orderType=1) |
| 餐品1 | 麦香鸡 (code=1450, qty=1, subtotal=1650分) |
| 餐品2 | 锡兰红茶 (code=3505, qty=1, subtotal=1100分) |
| 商品原价 | 2750分 (27.50元) |
| 优惠 | 0分 (0.00元) |
| 应付金额 | 2750分 (27.50元) |
| 预算 | 2500分 (25.00元) |
| 预算内 | ❌ 否（超预算250分/2.50元） |
| 含糖量 | 待确认 |
| 满足需求 | ❌ 超预算 |
| 调用时间 | 2026-10-17 12:22:50 |

**追加核验：麦香鸡 + 麦咖啡™冰美式中杯**

| 项目 | 值 |
|------|-----|
| 门店 | 世界城广场餐厅 (1960088) |
| 就餐方式 | 到店自取 (beType=1, orderType=1) |
| 餐品1 | 麦香鸡 (code=1450, qty=1, subtotal=1650分) |
| 餐品2 | 麦咖啡™冰美式中杯 (code=507411, qty=1, originalSubtotal=1900分, subtotal=1190分) |
| 商品原价 | 3550分 (35.50元) |
| 优惠 | 710分 (7.10元，促销优惠) |
| 应付金额 | 2840分 (28.40元) |
| 预算 | 2500分 (25.00元) |
| 预算内 | ❌ 否（超预算340分/3.40元） |
| 含糖量 | 待确认 |
| 满足需求 | ❌ 超预算 |
| 调用时间 | 2026-10-17 12:22:50 |

### 有效基线结论

**未找到满足本次需求的有效基线。**

原因：
1. 本次需求不接受瓶装水，只考虑经核实为无糖的茶、咖啡或汽水。
2. 本次查询的菜单和餐品详情未发现含糖量相关字段，无法从工具数据确认茶/咖啡/汽水是否无糖，全部标记"待确认"。官方另有 list-nutrition-foods 工具，未验证其是否提供糖含量及规格匹配。
3. 本次核验的两个组合（麦香鸡+锡兰红茶=27.50元、麦香鸡+冰美式中杯=28.40元）均超过25元预算。不宣称已穷举所有组合，也不宣称不存在其他可能满足需求的组合。
4. 不扩大预算、不替换需求。

用券验证保持未完成状态（不领券，卡包和门店均无券）。

### 用券候选

该门店当前到店自取场景无可用优惠券（query-store-coupons 返回空数组），无法核验用券候选报价。如实记录，不编造。

### 用券报价验证尝试（2026-10-17 12:15~12:16）

为验证用券报价链路，额外调用了两个券相关工具：

**1. available-coupons — 查询可领取的麦麦省券**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| （无参数） | — | — | 查询当前账号可领取的券列表 |

**返回结构：** 券列表，每项含 title（券名）、状态（可领取）、图片URL。无 couponId/couponCode/productCode 字段——这些是待领取的券，不携带报价所需的券编码。

**验证结果：** ✅ 调用成功，返回4张可领取券：巧克力味厚松饼猪柳蛋套餐、免费脆薯饼、人气麦旋风买一送一、9.9元中杯冰美式。但均为"可领取"状态，尚未在卡包中。

**2. query-my-coupons — 查询用户卡包券**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | string | 否 | 页码，默认1，最多5页 |
| pageSize | string | 否 | 每页条数，默认200，最大200 |

**返回结构：** 卡包中已拥有的券列表。注意：该接口不进行门店/渠道/配送方式校验，不承诺可用于当前订单。

**验证结果：** ✅ 调用成功，返回"暂无可用优惠券"。用户卡包中当前无已领取的券。

**用券报价验证结论：** 如实停止。用户卡包无券，门店维度也无券，不领券（遵守不领券约束），因此 calculate-price + couponId/couponCode 的用券报价链路未实际触发。available-coupons 中的4张券为待领取状态，领取后可通过 query-store-coupons 查询其在该门店的适用性，再通过 calculate-price 核验报价——此链路待后续有券时验证。

## 报价链路验证结论

**报价链路可用。** calculate-price 工具成功返回以"分"为单位的价格数据，包括商品明细、优惠金额和应付总额。返回的 `price` 字段（整数分）可直接用于本地对比器的整数分计算。

## 适配层所需字段

从 MCP 返回到本地对比器输入的适配需要以下字段映射：

| 对比器输入 | MCP 来源 | 说明 |
|-----------|---------|------|
| productCode | meals.{code} 或 meals.categories[].meals[].code | 餐品编码 |
| productName | meals.{code}.name | 餐品名称 |
| currentPrice（分） | calculate-price → productList[].subtotal | 商品小计（分），需从菜单的"元"字符串转分或直接用报价返回 |
| quantity | calculate-price → items[].quantity | 数量 |
| totalPrice（分） | calculate-price → data.price | 订单应付总额（分） |
| discount（分） | calculate-price → data.discount | 优惠金额（分） |
| originalPrice（分） | calculate-price → data.originalPrice | 订单原价（分） |
| couponId | calculate-price → items[].couponId | 使用的券ID（如有） |
| storeCode | query-nearby-stores → data[].storeCode | 门店编码 |
| beType | 用户选择 | 业务类型 |
| orderType | 由 beType 推导 | 订单类型 |
| reservationDate | 用户选择（可选） | 预约时间 |

**关键转换：**
- 菜单价格字段 `currentPrice`/`originalPrice` 为字符串类型的"元"，需 `× 100` 转为整数分。
- calculate-price 返回值已为整数分，可直接使用。
- 特调项的 key 规则：选中的用 `selectedKey`，未选中的用 `unselectedKey`，均需传入 calculate-price。

## 限制与注意事项

1. **用券报价链路未触发**：门店券(query-store-coupons)返回空、用户卡包(query-my-coupons)也返回空。available-coupons 返回4张可领取券但均为待领取状态，未领券（遵守约束）。calculate-price + couponId/couponCode 链路待后续有券时验证。
2. **beType=1 不传 beCode**：到店自取场景 beCode 为无效参数，传入会报错。
3. **特调传参规则**：对于含 unselectedKey 的特调组，该组内所有特调项都必须传入 calculate-price，选中的用 selectedKey，未选中的用 unselectedKey。
4. **套餐子项**：roundList 用于套餐内子商品的选配，本次验证使用单品未涉及。
5. **预约场景**：reservationDate 仅预约时必传，非预约不传。
6. **无糖饮料范围**：本次需求不接受瓶装水，只考虑经核实为无糖的茶、咖啡或汽水。本次查询的菜单(query-meals)和餐品详情(query-meal-detail)未发现含糖量相关字段，query-meal-detail 的 modification 仅含冰量、酱料等特调选项。所有茶/咖啡/汽水的含糖量均标记"待确认"，不根据名称自行判断。官方另有 list-nutrition-foods 工具，未验证其是否提供糖含量及规格匹配，留待后续确认。
7. **不宣称最低价**：本文档中的组合列表为部分查询结果，非穷举。不宣称任何"最低预算"或"最低价"结论。
8. **有效基线未找到**：本次核验的两个组合（麦香鸡+锡兰红茶=27.50元、麦香鸡+冰美式中杯=28.40元）均超25元预算。不扩大预算、不替换需求。不宣称已穷举所有组合。

## 下一步

1. **实现报价适配层**：将 calculate-price 返回的脱敏字段映射到本地对比器输入（见上方"适配层所需字段"表）。关键转换：菜单价格从"元"字符串转整数分，calculate-price 返回值已为整数分可直接使用。
2. **无有效基线时的结果输出**：对比器需要处理"未找到满足需求的有效基线"的情况——不编造方案、不扩大预算，如实输出未找到的原因（超预算、含糖量待确认、无可用券等）。
3. **list-nutrition-foods 待验证**：后续可调用此工具确认是否提供糖含量数据及规格匹配，以解决含糖量"待确认"问题。
4. **用券报价链路待验证**：待用户有券后，验证 calculate-price + couponId/couponCode 的完整报价链路。
