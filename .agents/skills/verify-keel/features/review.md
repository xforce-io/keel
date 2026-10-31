# `keel-review` 人介入合同

CLI / 文件与会话入口。不合入。#41 的团队交接要有实际角色运行的证据；该验证不替代正式独立审查。

Launch 前先 `mkdir "$HOME/.grok"`，以便 scratch 挂上 `reviewer`。

## 用户入口（必须都走）

1. **挂载**：Launch 之后 `$HOME/.local/share/agent-skills/library/keel-review/SKILL.md` 与 `…/keel-release/SKILL.md` 指向本仓库对应 skill；`$HOME/.grok/agents/reviewer.md` 指向本仓库 `agents/reviewer.md`。
2. **查找**：`local-skill find keel-review` 退出码 `0`。
3. **合同原文**：读本仓库 `skills/keel-review/SKILL.md`、`skills/keel-release/SKILL.md`、`skills/keel-verify/SKILL.md`、`agents/reviewer.md`。
4. **团队会话**：在有授权的当前会话核实团队关系及专职角色、模型和实际调用能力；按当前候选 skill 提供只读任务并读取完整实际输出，记录精确候选、角色、宿主、模型、来源、状态及原始结果。不因状态未知或发送成功假定任务完成；不可用或无授权时该入口 BLOCKED。

## #7 S1–S3

1. 入口 1：`keel-review`、`keel-release`、`reviewer` 已挂，不是 `未安装`。
2. 入口 2：能找到 `keel-review`。
3. 入口 3：
   - 审查结论必须有恰好一个 `human: required` 或 `human: optional`；缺字段视为审查未完成。
   - 硬条件（表面 / `P0` / 三轮 / 无法独立）不得标 `optional`。
   - `keel-release` 可发布 = `PASS` 且 `human: optional`，或 `human: required` 且已有当前候选的真实批准；缺字段或所需批准 → `BLOCKED`。

## #10 S1–S3

1. 入口 3 / `keel-review`：宿主表有 Cursor；模型顺序是用户点名 → `~/.config/keel/reviewer` → 宿主配置 → 互补 → `BLOCKED`；禁止 `inherit` 与未声明自选。
2. 入口 3 / 结论：必须有 `reviewer_host`、`reviewer_model`、`source`（`user` / `bind-file` / `host-config` / `complementary`）；缺一则审查未完成。`keel-release` 缺三列 → `BLOCKED`。
3. 入口 3 / `keel-verify`：有「维护回归（无 Issue / 全图）」段；完成表不交 `keel-review`。

## #41 S1–S3

- S1.A1 / 入口 4：有合规团队审查角色时优先交付冻结目标及依据，读取该角色实际输出并核对身份、模型来源、目标和结论；送达、等待超时或未知状态不能当完成。
- S2.A1 / 入口 3：分别检验角色不存在、不可调用、无法证明独立；每种均要说明拒绝原因并依合同回退或 BLOCKED。发现失败不冒充无角色，不自审。隔离情境不冒充真实宿主失效。
- S3.A1 / 入口 3：明确指定角色或模型可用时遵循指定；不能满足时 BLOCKED，不静默替换。模型规则按实际角色宿主解析。
- S3.A2 / 入口 3：非 PASS 不能发布；`human: required` 需当前候选真实批准。原三态及 `reviewer_host`、`reviewer_model`、`source` 保持。

在本次目标真实团队会话记录实际交接；其余拒绝/回退条件用隔离情境实际检验并记录结果。合同原文和自动检查不能替代实际角色输出，模拟不能冒充宿主故障或人审批准。

判定：`ls -l`、`local-skill find`、合同原文，以及 #41 的真实团队交接与角色输出、各隔离情境的判断分别存证；任一必需入口缺证不能汇总为通过。

## 不做

除 #41 所需的授权团队交接外，不在 Drive 里调 Reviewer。不改外部 `code-review`。不对本机现网 `~/.grok/agents/reviewer.md` 做 install / uninstall。
