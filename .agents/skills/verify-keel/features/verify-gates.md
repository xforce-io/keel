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


## #56 S1–S4：测试职责与行为证据

本票不改 skill 产品规则或公开 CLI。沿用本手册 scratch 安装、Doctor、Cleanup，只验证下列入口：

- S1：读取 [测试说明](../../../../tests/README.md)，核对基线全部规则文案测试组的处理去向与未覆盖部分；不把删测试说成行为覆盖提升。
- S2：在隔离副本中等义改写规则，运行 `python3 -m unittest tests.test_skill_assets` 应通过；删除真实引用目标或必需元数据后重跑应失败。原始副本、变更和命令结果保存在本票证据中，禁止改坏真实工作树。
- S3：运行 `python3 -m unittest discover -s tests`；保留安装、doctor、卸载、手册发现、check、reverify、preflight 和反射检查的运行回归。
- S4：按 [重放方法](../../../../evals/README.md) 用实际安装的当前候选重放五组样例；第 4 组首次与后续使用同一上下文，其余各用独立上下文。评估者必须独立于回答生成者，读取固定标准和原始回答判断。记录宿主、模型、候选、样例版本及结果；不做关键词打分。

结束清理本次 scratch，保留 `.agents/verify-runs/56/`。这次重放只证明五组固定输入的决策表现，不证明所有合同语义或真实交付执行正确。


## #56 追加 S5：共享测试选择准则

主要资产：[测试选择准则](../../../../skills/keel-dev/references/test-strategy.md)。本轮改变 agent 选择与审查测试的规则，依据 [L1 v1](../../../../docs/design/56-unittest-behavior-coverage/product.md) 的 S5.A1–A4；原 S1–S4 交付与候选不改写。

- S5.A1：scratch 安装、Doctor 后，从设计合同、keel-dev、keel-verify、keel-review 各自的真实引用读取同一准则，记录安装来源和文件摘要；不是依赖本仓 tests/README 才能发现规则。
- S5.A2–A3：按 evals 重放方法，实际运行06普通应用样例，独立评估测试选择、固定错误码例外及证据不足的处理，不以关键词打分。
- S5.A4：运行完整 unittest，并按当前候选重放受影响的原五组及新增06；04后续仍在同一上下文。保留原始结果与未知项，不能改旧证据SHA冒充新跑。按手册Cleanup。
