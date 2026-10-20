# 可选整数分计算

导入包内含 scripts/adapt_quotes.py、scripts/compare_quotes.py，均来自主项目，无第三方依赖。以技能安装目录为基准运行（不要假定当前工作目录就是安装目录）：

```text
python <技能安装目录>/scripts/adapt_quotes.py <本次脱敏报价JSON路径>
```

输入格式参考包内 references/historical-quotes.json。这个文件是历史回放，不能改时间后冒充新查询。

本次数据需填写：context 内 store_id、dining_mode、quote_batch；budget_fen；baseline（无满足需求基线可为 null）；candidates；同份餐的不用券报价可作为 price_reference。每组含 name、price_data.price（实际整数分应付）、business_success、meets_needs、evidence_ref、相同上下文及 basket_items（商品编码、数量和实际选配）。商品签名一致时才能计算 same_basket_saving_fen；不要通过删选配伪造一致。

business_success=true 必须有真实业务成功证据；meets_needs 可以为 true、false 或 null，不能为通过校验自行改成 true。evidence_ref 对应已脱敏记录。去掉券码、账号、Token、地址和原始响应，脚本不查询网络也不自行验证证据真伪。

输出的 payable_fen、same_basket_saving_fen、saving_fen、over_budget_fen 都是整数分。没有 Python 时，使用宿主计算工具完成同样逻辑，明确说明未运行此脚本。
