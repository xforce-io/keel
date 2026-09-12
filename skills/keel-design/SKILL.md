---
name: keel-design
description: >
  Use when the user says keel-design or /keel-design, or when keel routes to
  the design stage. Write the required design and stop for human approval.
  Do not self-approve, implement, or merge.
---

# keel-design

只做设计，停在人工批准。不代替 `keel-how`：现有子系统怎么工作由 how 带出处说明，本环节写该做成什么样。

套用有效 `AGENTS.md` 的 L1/L2 触发、结构、事实源和批准用语。设计停在可评审契约边界，不写实现 TODO 或代码说明书。

设计门禁触发时：发表或呈交相应提案，然后停，直到人给出所需批准。不得从沉默、从 agent 审查、或从「端到端做完」推断批准。

批准之后，按项目规则 promote 或链接设计，再把控制权交回调用方（通常是 `keel`）。

无人回复则问用户。禁止自批后大改。
