# 在 WorkBuddy 中使用

有两个独立入口：**对话 Skill** 用自然语言查价；**本地网页** 用按钮选餐。导入 Skill 不会自动启动网页，也不会把网页变成远程 MCP Server。

## 导入对话 Skill

1. 从仓库 [下载技能包](../downloads/mcd-smart-choice-workbuddy.zip)（在GitHub文件页点下载原始文件按钮），获取 `mcd-smart-choice-workbuddy.zip`，不要使用 GitHub 的完整源码 ZIP 代替。维护者可运行 `python scripts/build_skill_package.py --output local/mcd-smart-choice-workbuddy.zip` 生成同样的包。
2. WorkBuddy 左侧“专家·技能·连接器” → “技能” → “添加技能” → “上传技能”，选择该 ZIP，导入后启用。
3. 在连接器中启用你自己的麦当劳 MCP。官方地址 `https://mcp.mcd.cn`，使用你自己的 Token；已有连接不必重复配置。不要把 Token 贴入聊天或上传仓库。
4. 新建对话，选择已启用技能和麦当劳连接器，发送下面的提示词。导入后若未被自动选中，明确提到“麦麦明白点 / 麦乐省钱侠”。

```text
使用麦麦明白点技能，让麦乐省钱侠帮我选餐。我在武汉世界城广场附近，到店自取，预算25元，想吃一个鸡肉汉堡配咖啡。先让我确认具体门店，只查价，不领券、不下单。已有券能用就比较用券前后实际付款；超预算就直说，不替我加预算。
```

进一步可以说：“汉堡保留，饮品换一种，预算不变。”“这张券到底额外省了多少？别把原有促销也算进去。”

## 额度与依赖

- 对话 Skill 会使用 WorkBuddy 的模型额度，具体由宿主套餐计费；不是导入后就无限免费。技能不另调付费模型。
- 普通查询对话不依赖完整仓库或 Python。包内包含可选 Python 计算脚本与脱敏历史示例，算差额时可以使用；宿主未提供计算能力、且没有 Python 时应如实说明限制。
- 本地网页的选餐、实时 MCP 查询和角色规则不调用模型。Windows 下载完整源码后双击 `start-ui.cmd`；需要 Python 3.10+，真实查询还需自己的 MCP 配置。网页角色是本地规则，WorkBuddy 对话角色由宿主模型按 Skill 指令扮演，两者不是相同实现。

## 已验证与待验证

2026-10-20：独立包结构、元数据、引用文件和干净目录下的历史计算已自动验证；包内不包含本机连接器配置、Token、券码或 local 数据。尚未在 WorkBuddy 客户端执行上传导入与端到端对话验收，不将打包成功描述成客户端认证通过。若界面提示格式错误，保留错误文字用于修正，不要求重新购买会员。

官方参考：[客户端技能导入](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)、[技能包结构](https://open.workbuddy.cn/docs/skill)。
