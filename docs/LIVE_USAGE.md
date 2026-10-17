# 实时查询使用指南

## 1. 准备自己的 Token
在 https://open.mcd.cn/mcp 登录并申请 Token。项目不需要 Cursor / WorkBuddy 会员，也不调用模型API。用自己的账号查询，券和门店供应可能因账号及时点不同。

Windows PowerShell 可安全输入 Token，避免直接写入命令历史：
```powershell
$tokenInput = Read-Host "输入麦当劳 MCP Token" -AsSecureString
$env:MCD_MCP_TOKEN = [System.Net.NetworkCredential]::new('', $tokenInput).Password
```
只对当前终端生效。完成后可执行 `Remove-Item Env:MCD_MCP_TOKEN`。

或使用你已配置好的本机 MCP JSON 文件，命令添加 `--config "本机配置文件路径"`。文件应有 `mcpServers.mcd-mcp.url`（官方地址）及 `headers.Authorization`。程序不会修改该文件。环境变量存在时优先使用环境变量。

## 2. 选择门店和餐品
实时入口要求明确的门店与餐品编码。请通过已连接客户端的 query-nearby-stores、query-meals 查询，不凭名称猜编码。程序会再次读取详情并报价。第一版只支持默认规格的单品，每件1份，到店自取。支持编码的历史示例见 README；不承诺当前一定可售。

```powershell
python app.py live --store 1960088 --product 1450 --product 507411 --coupon-product 507411 --budget 25 --need "一个鸡肉汉堡和一份无糖饮品，不接受瓶装水"
```

已配置 WorkBuddy 时可在命令末尾显式添加：
```powershell
--config "$env:USERPROFILE\.workbuddy-ai\mcp.json"
```
此选项只读取已有连接器配置，不启动WorkBuddy、不消耗其模型额度。不要求其他用户安装WorkBuddy。

## 3. 结果
- local/live-report.html：中文报告。
- local/live-report.quotes.json：脱敏适配输入，可离线重放。
- local/live-report.evidence.json：工具名、成功状态和价格等白名单记录。

没有券或没有匹配餐品券时只报价不用券方案；有多张匹配券时停止并提示使用 `--coupon-title "券名关键词"`。用券报价失败不伪装成成功。失败时不生成本轮报告，输出目录可能仍保留旧报告，请查看时间，不能当作新的结果。

默认 `--needs-status pending`，不会从名称判断无糖等属性。confirmed仅用于你已确认全部餐品/口味要求的情形；预算总由代码单独核验。程序不验证用户输入事实，不自动选餐。

## 故障处理
401：Token无效或过期；429：稍后再试；网络错误：检查网络后重试。套餐或缺少必选规格：通过客户端明确选配后用适配器，当前实时入口不支持。自定义需求文字不要含私人地址、账号、Token。
