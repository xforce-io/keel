---
name: keel
description: >
  Use when the user says keel, /keel, 处理 Issue, 设计 Issue, 开发 Issue,
  端到端完成, 端到端改, or asks to ship, merge, or continue a guarded delivery
  lifecycle. Do not use for isolated code review or post-task reflection.
---

# keel

推进**一个**任务走过下一合法交付阶段。服从当前有效的全局与项目 `AGENTS.md`。
不复制项目规则、不代替 `code-review`、不发明部署手册。

## 选择模式

- **route** — 「处理 Issue N」：看现状，只推进一步合法阶段。
- **design** — 「设计 Issue N」：只完成所需设计，停在人工批准。
- **dev** — 「开发 Issue N」：实现、测试、独立审查通过；停在可发布，不合入。
- **end-to-end** — 「端到端完成」/「端到端改」：从当前状态走到独立审查、CI、合入；项目若有部署与健康检查则继续。

只读当前阶段需要的参考：[issue](references/issue.md)、[design](references/design.md)、[development](references/development.md)、[release](references/release.md)。

## 状态机

`intake → design-required? → human-approved → implementation → tests → independent-review → CI → merge → deploy → verify`

行动前先确认：实际仓库、有效指令、托管平台、Issue 或任务验收、已有设计、当前 diff、项目 runbook。凭证据续跑，不重放已完成阶段。

更窄的「把剩下代码写完」清单不能替换这台机器。用户要端到端、但计划漏了审查/CI/合入时，计划不完整：补上这些阶段，或 `BLOCKED` 并写明缺口。禁止默默丢掉。

## 硬门禁

- 禁止自批设计。需要批准却没有时，交出提案并停下。
- 独立、只读的审查者看最新精确目标。读 [reviewer adapters](references/reviewers.md)。优先使用与实现不同的强模型。能观察到宿主/模型就记下来；无法证明独立则在合入前停下。
- 修复由实现代理做，重跑受影响测试，再审新目标。最多三轮；未解决的阻塞项交给人。
- 发布、合入或生产部署前必须 `PASS`。`P0`–`P2` 阻塞；`P3` 建议，除非项目更严。`CHANGES_REQUESTED` 回到实现；`BLOCKED` 停在缺失证据或能力。
- 不编造目标环境、合入策略、部署命令、健康检查或回滚。项目 runbook 缺事实时，对外变更前只问一个问题。
- 生产部署在合入之后。预合入部署仅当项目明确记录了 staging / preview。
- 「端到端完成」授权的是这条有范围的生命周期，不是绕过仓库策略、保护分支、人工批准或缺失的部署事实。
- 本地重启进程、脏工作区、对未提交文件跑测试，都不是合入。合入 = 默认分支（或项目写明的集成分支）包含该变更。缺 Issue 号就问，不是跳过发布。

## 红旗 — 未完成

- 用户要端到端后，diff 未提交或未推送
- 把重启/本地进程说成已发布
- 端到端模式下，计划的非目标把合入排除了
- 实现测试通过却没有独立审查 + CI + 合入
- 没有把每条 Story 映射到这个 SHA 上一条命令的 `S1…Sn` 表

| 借口 | 实际 |
|---|---|
| 「目标计划没写合入。」 | 端到端仍含审查、CI、合入。更窄的计划不是豁免。 |
| 「守护进程已经重启。」 | 那是本地进程，不是 `origin` 默认分支。 |
| 「没有 Issue 号。」 | 按项目规则问或建；不要跳过 PR/MR。 |
| 「PR 以后再开。」 | 没有 PR/MR（或写明的门）时终点是 `BLOCKED`，不是完成。 |
| 「测试过了。」 | 每条 Issue Story 为 `pass`、`fail` 或规则允许的 `skip` 之前，不算完。 |
| 「跳过了，所以接受。」 | `skip` 是缺口，从来不等于 Story 已满足。 |

## 完成

说出停在哪一阶段。带上 `S1…Sn` 验收表（命令 + `pass|fail|skip`）、审查结果、PR/MR URL 或合入 SHA，以及若有的部署结果。未合入则说 `BLOCKED` 和那一个下一步决策。门禁挡住时，把挡住说清楚才算有效。
