# `keel-review` 人介入合同

CLI / 文件与会话入口。不合入。#41 的团队交接要有实际角色运行的证据；该验证不替代正式独立审查。

Launch 前先 `mkdir "$KEEL_VERIFY_HOME/.grok"`，以便 scratch 挂上 `reviewer`。

## 用户入口（必须都走）

1. **挂载**：Launch 之后 `$KEEL_VERIFY_HOME/.local/share/agent-skills/library/keel-review/SKILL.md` 与 `…/keel-release/SKILL.md` 指向本仓库对应 skill；`$KEEL_VERIFY_HOME/.grok/agents/reviewer.md` 指向本仓库 `agents/reviewer.md`。
2. **查找**：从已安装 library 或宿主 skill 列表读取 keel-review；local-skill 可用时也可查找，不要求安装它。
3. **合同原文**：读本仓库 `skills/keel-review/SKILL.md`、`skills/keel-release/SKILL.md`、`skills/keel-verify/SKILL.md`、`agents/reviewer.md`。
4. **团队会话**：在有授权的当前会话核实团队关系及专职角色、模型和实际调用能力；按当前候选 skill 提供只读任务并读取完整实际输出，记录精确候选、角色、宿主、模型、来源、状态及原始结果。不因状态未知或发送成功假定任务完成；不可用或无授权时该入口 BLOCKED。

## #7 S1–S3

1. 入口 1：`keel-review`、`keel-release`、`reviewer` 已挂，不是 `未安装`。
2. 入口 2：能找到 `keel-review`。
3. 入口 3：
   - 审查结论必须有恰好一个 `human: required` 或 `human: optional`；缺字段视为审查未完成。
   - 硬条件（表面 / `P0` / 三轮 / 无法独立）不得标 `optional`。
   - 只剩 `[P2][non-blocking]` 与 `P3` 时结论可以为 `PASS`；`P0`、`P1`、`[P2][blocking]` 和未标记的 `P2` 仍是 `CHANGES_REQUESTED`。
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

判定：`ls -l`、实际读取的 skill 路径、合同原文，以及 #41 的真实团队交接与角色输出、各隔离情境的判断分别存证；任一必需入口缺证不能汇总为通过。

## 不做

除 #41 的授权团队交接及 #49/#48 的合成审查情境外，不在 Drive 里调 Reviewer。不改外部 `code-review`。不对本机现网 `~/.grok/agents/reviewer.md` 做 install / uninstall。


## #49 S1–S2

基线：[L1 v1](../../../../docs/design/49-self-contained-review/product.md) §8。只 Drive 本票情境及适用保全检查，不重跑 #41 全部分支。

- S1.A1：从 scratch 安装后的 skill 读取内置准则，在没有 local-skill/code-review 的环境中给真实独立 agent 合成需求、完整差异与证据；确认能审查正确性、回归、安全和契约问题，引用具体依据并给出既有三态、人审与来源字段，不因缺外部工具阻断。合成结果不当作正式交付批准。
- S1.A2：给出缺完整差异或必要证据的情境，确认仍按原规则 BLOCKED，不以解除依赖为由放行。
- S2.A1：给定一个可读外部规则文件，实际读取并交接，验证规则对审查结果有效，记录来源和适用范围；不以同名认定合同内容。
- S2.A2：明确要求的规则路径不存在时，实际输出 BLOCKED 并点明路径，不回退成默认通过。规则冲突未解决同样阻断。

原始输入、读取路径和实际 agent 输出存入本票证据目录。S3 的 CLI 正常/缺失/占用与只读检查见 doctor.md；#7/#10 的原人审、来源及模型规则按本文件入口 3 保全，不新增平台集成。


## #48 S1–S2

基线：[L1 v1](../../../../docs/design/48-review-handoff/product.md) §8；仅执行本次对上的情境，不重跑 #41 全部团队角色分支。

1. 入口 1–3：按手册 scratch 安装、Doctor 与查找，读取已安装 keel-review；核对它对应当前候选，所有材料引用可读。沿用 #49 的内置准则和可选外部规则，不因缺 locator 或同名 skill 阻断；明确要求的附加合同不可读仍阻断。
2. S1.A1 / 交接入口：给真实 agent 一组隔离合成材料，包含需求、冻结目标与完整差异、设计验收映射、测试/驾驶证据、预检、内置审查准则及明确适用的附加合同，以及实现者“已完整覆盖”的评价和失败记录。让其按候选 skill 准备交接；检查材料齐全、必要解释标为待核实、评价不作通过依据且失败与缺口未被删掉。
3. S1.A2 / 同一入口：移除完整 diff 或当前预检，让其处理；实际输出应按原规则 BLOCKED 并指出缺口，不猜测通过。
4. S2.A1 / 结论入口：让 Reviewer 静态审阅合成差异和调用方测试输出，不执行命令；记录实际输出，区分直接审阅、亲自执行（未执行）、依赖已有证据及无法核实，注明来源且保留原结论字段。不把这个合成结果当成本票正式独立审查。
5. S2.A2 / 入口 3：核对完整 diff 和既有回归，确认没有改动模型、人审、三态、来源、三轮规则或复制 code-review checklist，没有新增 CLI/schema/校验器/门禁；正式独立审查另行核对。

原始输入、agent 输出、候选 SHA、时间和入口存入本票证据目录。上述情境不能以硬编码输出替代；缺条件记 blocked，未执行记 not_run。
