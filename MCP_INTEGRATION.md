# 麦当劳 MCP 集成说明

## 状态
已由 WorkBuddy 于 2026-10-17 完成首次真实调用验证。连接器状态正常，5 个核心工具均已成功调用。详细发现见 docs/MCP_DISCOVERY.md。

## 服务
- Server：https://mcp.mcd.cn
- 传输：Streamable HTTP
- 鉴权：Authorization: Bearer <本机 Token>
- 官方文档：https://github.com/M-China/mcd-mcp-server

## 计划使用的工具
| 工具 | 作用 | 验证状态 |
|---|---|---|
| query-nearby-stores | 根据用户提供的位置选择门店 | ✅ 已验证 2026-10-17 |
| query-meals | 获取选定门店菜单 | ✅ 已验证 2026-10-17 |
| query-meal-detail | 查询套餐组成及可替换项 | ✅ 已验证 2026-10-17（单品） |
| query-store-coupons | 查询该门店可用券 | ✅ 已验证 2026-10-17（返回空，该门店当前无券） |
| calculate-price | 核验基线与候选应付金额 | ✅ 已验证 2026-10-17（基线报价，无券候选） |

## 调用流程与价值
澄清需求 → 选门店与就餐方式 → 查询菜单、必要的餐品详情与券 → 生成基线和至多两个用券候选 → 分别报价 → 归一化到整数分 → 本地对比 → 解释实际支出和额外餐品。

真实工具参数以客户端发现的 schema 为准，不猜测字段。报价失败或券不适用时降级说明，不能用模型估价填补。不得把不同门店、就餐方式或时间上下文的报价直接比较。

## 真实验证记录
2026-10-17 12:09~12:13 (GMT+8)，WorkBuddy 使用 mcp__mcd-mcp 连接器完成首次验证。
- 场景：到店自取 (beType=1, orderType=1)
- 门店：麦当劳武汉世界城广场餐厅 (storeCode=1960088)
- 调用工具：query-nearby-stores ✅、query-meals ✅、query-meal-detail ✅、query-store-coupons ✅（返回空）、calculate-price ✅
- 基线报价：麦香鸡(16.50) + 纯悦(7.50) = 24.00元，在25元预算内
- 用券候选：该门店当前无可用券，未核验用券报价
- 限制：用券+calculate-price(couponId)链路未触发；套餐子项(roundList)未涉及
- 详细 schema 摘要和字段映射见 docs/MCP_DISCOVERY.md

## 后续直接验证：2026-10-17 12:47
Codex 使用只查询/试算客户端完成真实用券双报价。query-store-coupons 返回9.9元中杯冰美式券及适用商品，calculate-price 在相同餐品与默认特制下分别返回2840分（不用券）与2640分（用券）。实际少付200分，不以划线价总折扣910分代替实际节省。完整脱敏记录见 docs/MCP_COUPON_RUN_03.md；此前无券状态仅代表此前查询时点。

price_reference + basket_items 用于同款商品的价格对比，即使需求属性待确认也可验证价格差，但不会据此认定满足用户需求。baseline 仍要求需求明确符合，预算单独判断。客户端直接查询不依赖 WorkBuddy 模型额度。

## 统一实时入口
app.py live 通过scripts/run_live.py完成明确选定单品的详情查询→门店券查询→不用券报价→匹配券报价→脱敏→对比→HTML报告。每个单品1件、默认特制、到店自取；未实现自动自然语言选餐。无匹配券仍可比较预算，多张券匹配时要求用户缩小范围。客户端验证success=true及code=200后读取data.price，不保存原始券标识。需求默认待确认，整数分计算独立检查预算。

实时统一入口已实际运行；离线演示也在不带凭证的干净目录通过验证，见docs/VERIFICATION.md。

## 可视化工具（本地）
app.py ui 提供本机页面，query-nearby-stores按城市和关键词搜索→query-meals读取菜单→query-store-coupons查询适用券→用户直接选餐→run_live分别核验不用券/用券报价→在页面展示差额和预算。不再要求用户手抄编码。真实界面流程已验证，110条菜单数据中选择1450和507411，报价仍为2840分与2640分。

Token与券原始标识留在Python服务内存，不发往浏览器；页面仅使用会话内券别名。实时入口只监听127.0.0.1且校验请求来源。未建立对外托管或多用户服务。

## 预算搭配与替换
页面使用现有门店菜单和券数据，按名称偏好生成有界候选；每轮最多6组，分别通过query-meal-detail与calculate-price核验，失败不以菜单合计代替。单轮复用详情与券查询以减少重复请求。保留某一餐品时所有候选保持该商品，围绕券时可单独试算单买。返回候选只有脱敏商品与实际金额；原始券标识仍留在服务内存。
