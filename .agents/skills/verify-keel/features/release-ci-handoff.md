# PR 的 CI 失败交接（#64）

## 入口与验收

按手册在 scratch home 安装并运行 Doctor，核对已安装的 `keel-release/SKILL.md` 来自当前候选。按 [行为样例重放手册](../../../../evals/README.md) 从该入口执行 [07 样例](../../../../evals/inputs/07-release-ci-handoff.md)，由独立评估者判定输出。

| 验收 | 样例 |
|---|---|
| S1.A1 | A，代码回归在原 PR 接回，修复候选复验 |
| S2.A1 | B，环境故障交接及恢复 |
| S2.A2 | C，证据不足时在核实前保持停点 |
| S2.A3 | D，等待在跑的必需检查 |

在 `.agents/verify-runs/64/` 记录安装、Doctor、候选、输入、实际结果与评估依据，结束后清理 scratch 安装。样例验证 Skill 决策，平台写入及真实 CI 运行沿用各项目流程。
