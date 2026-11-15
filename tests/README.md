# 测试说明

通用选择方法以 [测试选择准则](../skills/keel-dev/references/test-strategy.md) 为准；本文件记录本仓入口、迁移与验证范围。

## 验证边界

- `python3 -m unittest discover -s tests` 运行离线、确定性检查：真实 CLI 的返回值、JSON、文件变化及隔离行为，以及必要的仓库资源结构。
- `test_skill_assets.py` 检查 Skill 元数据、相对文件链接、路由阶段表和名词表结构。它不理解中文规则，不验证 agent 的选择或遵循情况；链接检查不验证章节锚点，也不解析代码块里的示例链接。
- 自然语言规则的决策效果按 [行为样例](../evals/README.md) 用真实 Agent 重放，再由独立评估者判断。样例存在、关键词出现、单测通过都不代表行为评测通过。
- CLI 输出中的状态、字段、错误分类和必要提示属于可观察接口，可以断言；不因它们使用字符串就删除测试。角色文件中的权限字段等机器可读约束同样保留。

规则可以等义改写；不逐句复制正文到 `assertIn`。规则变更仍须人工审阅并核对受影响行为样例。结构检查也不能发现“原句仍在但旁边加入相反规则”这类语义冲突。

## 文本测试迁移清单

基线为 PR #55 合入后的 `52369c2`。以下覆盖该基线全部直接锁定 Markdown 规则措辞的测试组，共 33 个测试方法。它们不是被证明的行为覆盖，移除后也不宣称全部语义有自动替代。

| 原测试组 | 原方法数 | 处理与理由 | 验证去向及缺口 |
|---|---:|---|---|
| `KeelHowContractTests` | 2 | 移除合同句子匹配；保留机器阶段表顺序检查 | `test_skill_assets.py`；行为样例 02 验证先调查再修复，全部出处与 skip 细节仍需合同审阅 |
| `WhenToAskContractTests` | 7 | 移除分散的措辞/标题断言，避免复制确认规则 | 本地引用结构检查；样例 01、04 验证适用性及批准恢复；其他模式的全部路径未由这些样例穷尽 |
| `ProductDesignContractTests` | 4 | 移除逐句产品规则、图要求及规则表内容匹配 | 引用检查；样例 05 验证抽象选择；具体设计是否覆盖全部用户状态、图和验收仍需设计审阅 |
| `CatModeContractTests` | 2 | 移除风格与停点的中文匹配 | 阶段表不含 cat-mode，元数据与引用结构检查；不声称已重放所有风格会话 |
| `KeelReflectContractTests` | 4 | 移除配套 skill 的步骤和术语句子匹配 | 阶段表排除配套 skill，资源引用检查；建票、进仓和复盘全部决策不在本次五组样例的覆盖承诺内 |
| `KeelReviewContractTests` | 11 | 移除审查准则的多份复述匹配 | `test_keel_check.py` 实跑审查/人工批准门禁，样例 03、04 验证复验及批准决策；团队角色发现等仍须合同和实际交接审阅 |
| `HandbookPathWordingTests` | 3 | 移除按“旧/不认”等词判定路径含义的测试 | `KeelVerifyLookupTests` 实跑新旧路径、冲突、缺件和迁移提示；不将运行行为推广为所有文档措辞正确 |

其他检查的保留与收敛：

| 位置 | 处理与理由 |
|---|---|
| `KeelInstallTests`、`KeelCopyModeTests` | 保留全部真实 CLI 安装、升级、卸载、冲突、只读和隔离行为断言 |
| `KeelReviewerAgentTests` | 保留真实挂载/占用处理，以及 `permission_mode`、禁止固定 `model` 的机器元数据检查 |
| `KeelVerifyLookupTests` | 保留全部运行测试；仓库功能文件清单由实际目录枚举，避免新增合法功能文件时修改第二份文件名清单 |
| `VerifyScratchSafetyTests` | 保留对危险 shell 变量形式的窄静态检查；它不等于所有驾驶命令已通过安全审查 |
| `test_keel_preflight.py` | 删除以历史项目名缺席证明通用性的源码字符串检查；保留同一测试中两类调用方编号空间的实际通过/缺项失败验证及其他全部 CLI 测试 |
| `test_keel_check.py`、`test_keel_reverify.py`、`test_keel_reflect_inspect.py` | 保留；它们验证实际校验、恢复、资源边界或脱敏输出，不按“含 assertIn”机械删除 |

## 改动后的验证

1. 运行结构检查：`python3 -m unittest tests.test_skill_assets`。
2. 运行完整回归：`python3 -m unittest discover -s tests`。安装相关变更另按项目要求运行 `python3 -m unittest tests.test_keel tests.test_keel_reflect_inspect`。
3. 在隔离副本中做可撤回实验：等义改写应不触发结构失败，删除真实引用目标或必需元数据应失败。记录输入改动、命令、候选及原始结果；不要破坏当前工作树。
4. 改到规则或评测输入时，根据 [重放方法](../evals/README.md) 运行受影响样例。若未执行，明确写未执行，不用结构测试替代。

原始运行材料放在 `.agents/verify-runs/<issue>/`，不提交模型输出、私人会话或凭据。本说明记录测试职责，不改变任何交付门禁或 skill 产品规则。
