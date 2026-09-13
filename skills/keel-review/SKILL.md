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

审查模型按本次解析，缺一层走下一层，禁止发明。本 skill 不写死 slug：

1. 本会话用户点名的 slug（且本宿主能跑）
2. 本机绑定文件 `$KEEL_HOME/.config/keel/reviewer`（默认 `~/.config/keel/reviewer`）：非空、非 `#` 行，格式 `host slug`；`host` 为 `cursor` / `grok` / `codex` / `pi` / `omp` 之一。取当前宿主那一行。
3. 宿主配置：Codex `review_model`；Grok `reviewer.md` 的 `model:` 或 `~/.grok/config.toml` `[subagents.models]`；其它宿主的等价项
4. 互补默认：与实现不同厂或不同家族、且本宿主能跑
5. 以上皆无，或点名/绑定的 slug 本宿主跑不了 → `BLOCKED`，问一次。禁止 `inherit`，禁止未声明自选，禁止把跑不了的 slug 映射成另一家。

宿主适配：

- **Codex：** 用原生 code review。slug 按上面的顺序解析（宿主配置是 `review_model`）。
- **Pi：** 调 `reviewer` 子代理。slug 按上面的顺序解析。
- **Grok：** `subagent_type: reviewer`；禁止用会继承实现模型的 `general-purpose`。类型来自 `keel install` 挂到 `~/.grok/agents/reviewer.md` 的角色文件（`permission_mode: plan`）。
- **Cursor：** 没有 `reviewer` 子代理类型时，只允许带**显式 model** 的只读子代理；slug 只来自上面的解析。绑定不写进 `~/.cursor`。
- **OMP：** 调用户 `reviewer` agent 定义。slug 按上面的顺序解析。

`keel install` 不创建绑定文件、不写入 slug。能观察到宿主/模型就记下来，不要只信模型自称。用户点名优先于互补默认。无法证明独立（且用户也没有点名/绑定）则不得进入 `keel-release`。

修复由实现代理做（回到 `keel-dev`）。每轮修复后重跑受影响测试、刷新验收表，再经 `keel-verify`（对新 SHA 重跑驾驶证明，或按该环节规则写明 skip），然后审查新 diff。禁止把上一轮的 verify 证据挂到新目标上。最多三轮仍非 `PASS` 则交给人。

`PASS` 且 `human: optional` 才能交给发布。`P0`–`P2` 阻塞；`P3` 建议，除非项目更严。`CHANGES_REQUESTED` 回到 `keel-dev` → `keel-verify` 后再审；`BLOCKED` 停在缺失证据或能力。代码审查不代替验收表。

结论必须同时有恰好一个三态（`PASS` / `CHANGES_REQUESTED` / `BLOCKED`）、恰好一个 `human: required` 或 `human: optional`，以及 `reviewer_host`、`reviewer_model`、`source`（恰好一个：`user` / `bind-file` / `host-config` / `complementary`）。缺 `human`、缺三列任一、两个都写、或其它取值 → 审查未完成，不得进入 `keel-release`。不要收成第四个三态。`CHANGES_REQUESTED` / `BLOCKED` 时 `human` 与三列仍必须出现。`human` 由 Reviewer 给出；父代理不得补写或改写。外部 `code-review` 仍只管缺陷、证据与 `P0`–`P3`。

`PASS` + `human: required` → 停，把分级意见给人，不进入 `keel-release`。

硬条件（任一成立必须 `human: required`，不得 `optional`）：

1. **表面**：冻结目标改了 agent 所遵循的 skill 合同（`SKILL.md` / 角色文件的行为条款）、安装/卸载/doctor/挂载、鉴权（凭据、token、权限、登录门）、或用户可调用的公开 CLI（命令、flag、帮助、默认行为）。
2. **`P0`**：本轮审查标出任一 `P0`。
3. **三轮**：同一目标已满三轮仍非 `PASS`。
4. **独立**：无法证明 Reviewer 与实现不同模型/上下文。

无硬条件时，模型仍可因爆炸半径或吃不准标 `required`。父代理发现硬条件成立却标了 `optional` → 结论无效，按 `required` 停，不得发布。吃不准硬条件是否成立 → `required`。
