---
name: mcd-smart-choice
description: 根据用户预算与原始点餐需求，通过麦当劳 MCP 查询门店菜单和优惠券、核验候选报价，比较用券是否真正减少支出。适用于点餐方案对比，不自动下单。
---

# 麦麦明白点

先明确原始需求、预算、门店与就餐方式。位置不明确时询问用户，不读取私人地址记录代替用户选择。

使用已连接的麦当劳 MCP，先查看实际可用工具与参数 schema。参考 query-nearby-stores、query-meals、query-meal-detail、query-store-coupons 和 calculate-price。缺少必需工具时说明受限能力，不伪造调用或价格。

生成一个满足原始需求的基线方案，再生成最多两个用券候选。候选必须保留原始需求，列出额外餐品、券使用条件和适用时间。不假定优惠券可叠加，不以临期为购买理由。

分别核验应付总价，保证同一门店、就餐方式及同一轮查询上下文。报价失败时标记未核验，不参加确定推荐。使用整数分进行预算和差额计算；实际节省是基线应付减去候选应付。可使用项目 scripts/compare_quotes.py 对归一化数据计算，数据格式参考 examples/demo-quotes.json。schema 中的满足需求和已核验标记需要根据真实返回和用户需求确定，不能为通过校验自行设为真。

输出原始需求、候选餐品、应付金额、额外餐品、相对基线节省或多花金额、预算结果、查询时间和限制。仅在核验过的候选内比较，不承诺绝对最低价。若直接购买更合适，明确建议不用券。

本 Skill 只查询和比较，不调用创建/取消订单、领券、积分兑换或抽奖工具。展示结果时去除账号、地址、Token 和订单标识。

## 本地报告交付
项目仓库根目录下，已脱敏的报价输入按 examples/latest-quotes.json 格式组织；查验工具和业务成功后才写 business_success=true，并填写证据引用。报告的 need、store_label、queried_at、data_label 和 evidence 应与实际查询一致，旧报价明确标记历史数据。不要输出私人地址或完整券码。

需求属性无法核实则 meets_needs=null；不满足则 false。没有有效基线时 baseline=null，仍保留候选与原因，不伪造基线。预算独立判断，不用预算代替口味等需求符合状态。缺券不阻塞普通报价；同一任务已确认无券时不重复查询。

运行：
```powershell
python scripts/render_report.py examples/latest-quotes.json --adapted --output local/report.html
```
报告只重现输入，不自动查询数据。执行失败应说明，不能宣称已生成文件。用户仅需离线回放时，运行现有输入即可，不调用工具消耗额度。

## 统一命令入口
已明确单品与门店编码时，优先使用app.py live，避免由模型手工抄写每个报价JSON。参数与支持范围见仓库docs/LIVE_USAGE.md。自然语言需求仍需先澄清，默认needs-status=pending；只有获得明确证据后才能使用confirmed。遇到套餐/非默认规格需说明实时入口不支持，不能擅自替换成单品。

仅离线展示时使用python app.py demo，不调用MCP或反复查询。不要为了整理日志或生成报告让用户重复消耗WorkBuddy额度。
