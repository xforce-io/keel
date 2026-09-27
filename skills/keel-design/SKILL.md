---
name: keel-design
description: >
  Use when the user says keel-design or /keel-design, or when keel routes to
  design. Define product behavior and acceptance in L1, then the necessary
  technical contract in L2. Do not self-approve, implement, or merge.
---

# keel-design

只写所需设计，交回路由。不判断要不要人，不给出 `human: required` 或 `human: optional`；流程推进与产品确认按 `../keel/references/when-to-ask.md`。不代替 keel-how 的现有机制说明。

先完整读取：

1. `../keel/references/when-to-write.md`：逐份判定 L1/L2 write、reuse 或 skip，不以 AGENTS.md 的触发列表为准。
2. [产品与技术设计合同](references/design-contract.md)：L1 产品大纲、L1.8 验收表、L2 技术大纲、关联及迁移规则。

L1 是完整产品设计，L2 是技术设计；不是概要/详细，也不再增加两套深度。先定位 Issue 范围、已有产品约定与确认，再写产品路径和可判定验收。产品未明确时只完成 L1 与必要可行性调查，不先用 L2 固定实现方向。

按合同写完当前适用部分后，返回：L1/L2 适用性、文档与版本、Issue/Story/验收关联、产品确认来源或待明确问题。需要 L2 时引用已经明确的 L1 基线，不复制正文；只需 L1 或纯技术 L2 时说明原因。禁止自批 Draft 为 Approved，不写实现 TODO 或代码说明书。

默认文档位置与章节见合同；有效项目 AGENTS 的结构要求须显式映射，旧定义冲突按合同迁移，不能悄悄沿用“半页 L1”而遗漏产品交互。用户可见验收必须映射应用仓库的 verify 功能文件；L2 不适用不免除该要求。

Issue 仅补短摘要与链接；若用户授权发表评论，评论只解释方案与评审点，完整文档是事实源。设计写完不自动实现、不合入，下一阶段由路由及当前用户模式决定。
