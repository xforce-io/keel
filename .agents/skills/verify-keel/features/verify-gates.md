# 功能地图与验证门禁

文件/skill 入口，使用手册的 scratch install / doctor / cleanup。不得操作现网 home。

## 用户入口（全部走）

1. 安装后确认 library 中 keel、keel-dev、keel-design、keel-release、keel-verify、keel-verify-maintain 的 SKILL.md 指向当前仓库。
2. `local-skill find keel-verify-maintain` 可发现新 skill。
3. 读取上述已安装文件的合同原文，逐项记录以下验收；不将文本检查声称为下游 agent 的实际执行。

## 验收条目

- #18 S1：dev 要求每条用户可见 Story 对应功能文件/条目；缺映射 BLOCKED，补文件与 README 后完成；pytest 不能替代地图，无用户路径 skip 有明确条件。
- #18 S2：route/dev/end-to-end 在用户可见票实现后进入 verify；release 缺 verify 表不能开或合 PR；核对 pass/允许的 skip 以及入口、证据路径。
- #18 S3：design 在须写 L2 时要求 §11 点名功能文件或 README 条目并逐条对应 Story。
- #18 S4：显式 keel-verify-maintain 无 Issue 可进入源码对照；维护循环同样允许；全图/回归才额外 Live；只改 verify-*，不改产品代码，不把完成表送 review。

保存挂载、查找输出和各条合同摘录到 .agents/verify-runs/18/；结束按手册 uninstall scratch，保留证据。


## #52 S1–S2：决策行为样例

主要资产：[evals/README.md](../../../../evals/README.md)。本票不改产品规则，只验证样例可用性。按手册先 scratch 安装、Doctor；不因本票运行 #18 的无关 locator 入口。

- S1：核对四组输入（第 4 组另有一次后续回复）、独立判断标准及来源引用，输入不含标准答案或真实私人材料。
- S2：按重放指引为每组调用独立上下文的真实 Agent，只给对应输入与已安装 skill；第 4 组在同一上下文追加固定回复。再由未产生受测回答的独立评估者读取判断标准及原始输出，逐项判定。不得以关键字检查或父代理硬编码答案冒充模型输出。
- 实际输出、SHA、宿主/模型和判定留在本票 `.agents/verify-runs/`，不要提交输出或调用凭据。决策评测不冒充真实修改/测试/合入或跨宿主的 E2E 通过；最后清理本次 scratch。
