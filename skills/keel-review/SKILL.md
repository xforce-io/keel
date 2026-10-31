---
name: keel-review
description: >
  Use when the user says keel-review or /keel-review, or when keel routes to
  independent review. Run a host Reviewer on the newest exact target. Do not
  implement fixes in the reviewer, and do not merge.
---

# keel-review

独立、只读审查最新精确目标。不在实现上下文里审。

送审前：

1. `local-skill find code-review`，选精确匹配，完整读取返回的 `skill_file`，把该合同交给 Reviewer。找不到则 `BLOCKED`，不要用记忆或宿主口癖顶替。
2. 冻结最新精确审查目标。只读 Reviewer 不能跑 Git 时，父代理必须在请求里提供完整 diff、相关文件、测试结果、验收/设计引用，以及 `keel-verify` 的证据路径（若该环节 `skip` 则写明原因）。缺证据是 `BLOCKED`，不是允许猜测，也不是让 Reviewer 去改或去拉。

送审材料还须包含适用 L1/L2 的版本、产品确认来源、Issue S → L1.8 → 测试/驾驶证据映射；不适用项附依据。按 [设计合同](../keel-design/references/design-contract.md) 核对产品路径是否遗漏、L2 是否缩减产品承诺、必需子项是否全部有当前候选证据、是否为通过而事后降低标准。只有 S 汇总或 `keel check` PASS 不足以证明产品验收；缺必要材料为 BLOCKED，已发现契约违背按缺陷给出结论。

交接材料还须包含当前候选的 `keel preflight` 结果。预检失败、结果缺失，或结果绑定的候选与关联证据和冻结目标不一致，均为 `BLOCKED`。结构通过只说明编号、分支、入口和声明关联已核对，不是产品验收，也不代替本环节审查或 `keel check`。

审查本次变更涉及的项目知识是否与当前实现及引用依据一致，区分设计意图与实现；不因此扩展为全库知识巡检。

## 选择审查角色

先按当前会话提供的团队上下文和可用宿主能力，发现团队审查角色。读取相应工具/skill 的操作合同，核实角色实际身份、所属团队关系、可调用性、独立上下文及能否按只读约束审查；名称或自称不能单独证明这些条件。用户明确指定角色时优先核实该角色；没有指定时优先已有且合规的团队审查角色，不以当前宿主的默认适配覆盖它。多个合格角色按当前团队关系及可核对性择一并记录理由，不擅自操作其他团队的角色。

按所选角色**实际宿主**解析下述模型规则，并核对宿主可观察的实际模型与来源；用户明确指定的模型优先，绑定不可运行或不能核实时不得换成别的 slug。用户明确指定的角色或模型无法满足时，报告原因并 `BLOCKED`，不要静默替换。无用户明确指定时，团队角色不存在、不可调用、无法证明独立或发现能力不可用，各自记录事实和原因，再判断下列宿主适配能否满足原有独立性、模型与只读合同；能则说明依据后回退，不能则 `BLOCKED`。发现失败不等于已证实没有角色；实现者自审不能作为回退。

交接冻结候选、完整合并差异或可读取方式、适用设计/确认、验收、验证、预检及 `code-review` 合同。使用会话提供的渠道提交后等待并**读取实际输出**，核对角色身份、审查目标和结果；记录团队审查或回退方式、选择/拒绝原因及实际角色、宿主、模型和来源。发送成功不是审查完成；超时、未知状态或交付不确定时先读取状态和输出，未确认未送达不得盲目重发，也不得猜测结果。若遇到权限确认或问题，按宿主合同交给用户，不替用户回答。角色无权限读取 Git 时仍提供完整 diff 和相关材料；缺依据 `BLOCKED`。

审查模型按本次解析，缺一层走下一层，禁止发明。本 skill 不写死 slug：

1. 本会话用户点名的 slug（且本宿主能跑）
2. 本机绑定文件 `$KEEL_HOME/.config/keel/reviewer`（默认 `~/.config/keel/reviewer`）：非空、非 `#` 行，格式 `host slug`；`host` 为 `cursor` / `grok` / `codex` / `pi` / `omp` 之一。取当前宿主那一行。
3. 宿主配置：Codex `review_model`；Grok `reviewer.md` 的 `model:` 或 `~/.grok/config.toml` `[subagents.models]`；其它宿主的等价项
4. 互补默认：与实现不同厂或不同家族、且本宿主能跑
5. 以上皆无，或点名/绑定的 slug 本宿主跑不了 → `BLOCKED`，问一次。禁止 `inherit`，禁止未声明自选，禁止把跑不了的 slug 映射成另一家。

无合格团队角色且允许回退时的宿主适配：

- **Codex：** 用原生 code review。slug 按上面的顺序解析（宿主配置是 `review_model`）。
- **Pi：** 调 `reviewer` 子代理。slug 按上面的顺序解析。
- **Grok：** `subagent_type: reviewer`；禁止用会继承实现模型的 `general-purpose`。类型来自 `keel install` 挂到 `~/.grok/agents/reviewer.md` 的角色文件（`permission_mode: plan`）。
- **Cursor：** 没有 `reviewer` 子代理类型时，只允许带**显式 model** 的只读子代理；slug 只来自上面的解析。绑定不写进 `~/.cursor`。
- **OMP：** 调用户 `reviewer` agent 定义。slug 按上面的顺序解析。

`keel install` 不创建绑定文件、不写入 slug。能观察到宿主/模型就记下来，不要只信模型自称。用户点名优先于互补默认。无法证明独立（且用户也没有点名/绑定）则不得进入 `keel-release`。

修复由实现代理做（回到 `keel-dev`）。每轮先补同类边界检查，再按 `keel-verify` 的[复验准备合同](../keel-verify/references/reverification.md)核对影响、必要真实路径和预算，刷新当前候选的验收表及适用性依据后审查完整合并差异。不得把旧证据改 SHA 冒充新跑；历史原始依据按合同核对依赖及适用范围，不自动重做全部业务分析。

同一任务累计三轮仍非 `PASS` 则交给人，不因新 SHA、目录或暂停恢复清零。明确授权追加时保留总轮次/成本及授权原文，先说明共同根因、策略变化、剩余缺口和退出条件，再核对预算；只允许获准的追加范围，不能默认原样重启全套流程。READY 不代替独立审查或解除任何发布门禁。

`PASS` 且（`human: optional`，或 `human: required` 已获得当前候选的真实人工批准）才能交给发布。`P0`–`P2` 阻塞；`P3` 建议，除非项目更严。`CHANGES_REQUESTED` 回到 `keel-dev` → `keel-verify` 后再审；`BLOCKED` 停在缺失证据或能力。代码审查不代替验收表。

结论必须同时有恰好一个三态（`PASS` / `CHANGES_REQUESTED` / `BLOCKED`）、恰好一个 `human: required` 或 `human: optional`，以及 `reviewer_host`、`reviewer_model`、`source`（恰好一个：`user` / `bind-file` / `host-config` / `complementary`）。缺 `human`、缺三列任一、两个都写、或其它取值 → 审查未完成，不得进入 `keel-release`。不要收成第四个三态。`CHANGES_REQUESTED` / `BLOCKED` 时 `human` 与三列仍必须出现。`human` 由 Reviewer 给出；父代理不得补写或改写。外部 `code-review` 仍只管缺陷、证据与 `P0`–`P3`。

`PASS` + `human: required` → 未获当前候选的人工批准时停，把分级意见给人。获得真实批准后，按 [交付校验合同](../keel-release/references/check.md) 记录独立的 `human_approval`，重新校验后可进入 `keel-release`；保留 Reviewer 原始 `human: required`，不改成 optional。会话批准有效，不强制用户重复去平台批准；候选改变后须重新人审。人工批准不能覆盖 `CHANGES_REQUESTED` / `BLOCKED`。

硬条件（任一成立必须 `human: required`，不得 `optional`）：

1. **表面**：冻结目标改了 agent 所遵循的 skill 合同（`SKILL.md` / 角色文件的行为条款）、安装/卸载/doctor/挂载、鉴权（凭据、token、权限、登录门）、或用户可调用的公开 CLI（命令、flag、帮助、默认行为）。
2. **`P0`**：本轮审查标出任一 `P0`。
3. **三轮**：同一目标已满三轮仍非 `PASS`。
4. **独立**：无法证明 Reviewer 与实现不同模型/上下文。

无硬条件时，模型仍可因爆炸半径或吃不准标 `required`。父代理发现硬条件成立却标了 `optional` → 结论无效，按 `required` 停，不得发布。吃不准硬条件是否成立 → `required`。
