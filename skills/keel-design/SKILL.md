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

先复用已有契约、确认和 how 依据，形成具体草稿并标明未决部分。只有依据不足、不同选择会改变产品结果时，完整读取 [按需澄清](references/clarification.md)，围绕受影响路径提问。预期明确的小 bugfix 直接复用契约，不为澄清增加访谈或新设计；调查、验证与审查仍按原环节执行。

修复任务在确定方案前引用 `keel-how` 的问题证据及未确认假设；缺适用依据时先交回 how，不先凭猜测定方案再补复现。是否需要写设计文档仍按原触发规则，与修复任务的取证顺序分开判断。

按合同写完当前适用部分后，返回：L1/L2 适用性、文档与版本、Issue/Story/验收关联、产品确认来源或待明确问题。需要 L2 时引用已经明确的 L1 基线，不复制正文；只需 L1 或纯技术 L2 时说明原因。禁止自批 Draft 为 Approved，不写实现 TODO 或代码说明书。

默认文档位置与章节见合同；有效项目 AGENTS 的结构要求须显式映射，旧定义冲突按合同迁移，不能悄悄沿用“半页 L1”而遗漏产品交互。有多个步骤或有分支的用户交互，路径必须能在一张图里看完；图可以是该 Story 自己的，或它明确指出的已有图的一段。仅在总览里出现名称不算覆盖，数据库、进程、IPC 图不能充当这张用户交互图。单步且无分支可在该 Story 下说明原因后省略，没有用户交互的纯技术 Story 可写 N/A。不要求每条 Story 各有一张图。用户可见验收必须映射应用仓库的 verify 功能文件；L2 不适用不免除该要求。

Issue 仅补短摘要与链接；若用户授权发表评论，评论只解释方案与评审点，完整文档是事实源。设计写完不自动实现、不合入，下一阶段由路由及当前用户模式决定。
