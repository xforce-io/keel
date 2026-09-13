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

宿主适配：

- **Codex：** 用原生 code review（配置的 `review_model`）。
- **Pi：** 调 `reviewer` 子代理；用户覆盖选互补模型。
- **Grok：** `subagent_type: reviewer`；禁止用会继承实现模型的 `general-purpose`。类型来自 `keel install` 挂到 `~/.grok/agents/reviewer.md` 的角色文件（`permission_mode: plan`）。具体模型 slug 由本机 frontmatter 或 `~/.grok/config.toml` 的 `[subagents.models]` 绑定，不写进 keel skill。
- **OMP：** 调用户 `reviewer` agent 定义。

能观察到宿主/模型就记下来，不要只信模型自称。优先与实现不同的强模型。无法证明独立则不得进入 `keel-release`。

修复由实现代理做（回到 `keel-dev`）。每轮修复后重跑受影响测试、刷新验收表，再经 `keel-verify`（对新 SHA 重跑驾驶证明，或按该环节规则写明 skip），然后审查新 diff。禁止把上一轮的 verify 证据挂到新目标上。最多三轮仍非 `PASS` 则交给人。

`PASS` 且 `human: optional` 才能交给发布。`P0`–`P2` 阻塞；`P3` 建议，除非项目更严。`CHANGES_REQUESTED` 回到 `keel-dev` → `keel-verify` 后再审；`BLOCKED` 停在缺失证据或能力。代码审查不代替验收表。

结论必须同时有恰好一个三态（`PASS` / `CHANGES_REQUESTED` / `BLOCKED`）和恰好一个 `human: required` 或 `human: optional`。缺 `human`、两个都写、或其它取值 → 审查未完成，不得进入 `keel-release`。不要收成第四个三态。`CHANGES_REQUESTED` / `BLOCKED` 时 `human` 仍必须出现。`human` 由 Reviewer 给出；父代理不得补写或改写。外部 `code-review` 仍只管缺陷、证据与 `P0`–`P3`。

`PASS` + `human: required` → 停，把分级意见给人，不进入 `keel-release`。

硬条件（任一成立必须 `human: required`，不得 `optional`）：

1. **表面**：冻结目标改了 agent 所遵循的 skill 合同（`SKILL.md` / 角色文件的行为条款）、安装/卸载/doctor/挂载、鉴权（凭据、token、权限、登录门）、或用户可调用的公开 CLI（命令、flag、帮助、默认行为）。
2. **`P0`**：本轮审查标出任一 `P0`。
3. **三轮**：同一目标已满三轮仍非 `PASS`。
4. **独立**：无法证明 Reviewer 与实现不同模型/上下文。

无硬条件时，模型仍可因爆炸半径或吃不准标 `required`。父代理发现硬条件成立却标了 `optional` → 结论无效，按 `required` 停，不得发布。吃不准硬条件是否成立 → `required`。
