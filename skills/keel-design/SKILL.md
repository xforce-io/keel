---
name: keel-design
description: >
  Use when the user says keel-design or /keel-design, or when keel routes to
  the design stage. Write the required design and return control. Do not
  self-approve, implement, or merge.
---

# keel-design

只写所需设计，交回路由。不决定停不停，不判断要不要人，不给出 `human: required` 或 `human: optional`。停不停由流程和 `../keel/references/when-to-ask.md`。不代替 `keel-how`：现有子系统怎么工作由 how 带出处说明，本环节写该做成什么样。

写不写 L1 / L2 以 `../keel/references/when-to-write.md` 为准（先完整读取），不以 AGENTS.md 的触发列表为准。章节结构、事实源、批准用语仍套用有效 `AGENTS.md`。设计停在可评审契约边界，不写实现 TODO 或代码说明书。须写 L2 且含用户可见 Story 时，测试计划节必须点名要新增或更新的 `.agents/skills/verify-*/features/<file>.md`（或 README 条目），并与用户可见 `S1…Sn` 一一对应；只写「E2E：人在某页看见…」而不点文件名则不算过。

按 `../keel/references/when-to-write.md` 须写 L1 则发表或呈交提案，然后交回路由。禁止自批后把 Draft promote 成 Approved。
