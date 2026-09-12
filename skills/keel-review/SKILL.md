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
2. 冻结最新精确审查目标。只读 Reviewer 不能跑 Git 时，父代理必须在请求里提供完整 diff、相关文件、测试结果、验收/设计引用。缺证据是 `BLOCKED`，不是允许猜测，也不是让 Reviewer 去改或去拉。

宿主适配：

- **Codex：** 用原生 code review（配置的 `review_model`）。
- **Pi：** 调 `reviewer` 子代理；用户覆盖选互补模型。
- **Grok：** `subagent_type: reviewer`；禁止用会继承实现模型的 `general-purpose`。
- **OMP：** 调用户 `reviewer` agent 定义。

能观察到宿主/模型就记下来，不要只信模型自称。优先与实现不同的强模型。无法证明独立则不得进入 `keel-release`。

修复由实现代理做（回到 `keel-dev`）。每轮修复后重跑受影响测试、刷新验收表，再审新 diff。最多三轮仍非 `PASS` 则交给人。

`PASS` 才能交给发布。`P0`–`P2` 阻塞；`P3` 建议，除非项目更严。`CHANGES_REQUESTED` 回到实现；`BLOCKED` 停在缺失证据或能力。代码审查不代替验收表。
