---
name: keel
description: >
  Use when the user says keel, /keel, 处理 Issue, 设计 Issue, 开发 Issue,
  端到端完成, 端到端改, 开票, 建 Issue, 跟踪这个需求, keel-start, code start,
  打开这个项目, 待办, 分支什么情况, or asks to ship, merge, or continue a
  guarded delivery lifecycle. Routes to stage skills, or to keel-ticket /
  keel-start when those companion skills apply. Do not use for isolated
  code review, post-task reflection, or monastery.
---

# keel

只做**路由**。推进**一个**任务的下一合法交付阶段。环节规则在独立 skill 里，这里不抄。

进入流程前完整读取 `references/when-to-ask.md` 与 `references/when-to-write.md`。要不要问人、要不要写设计以那两份为准，不把表抄进本文件。

服从当前有效的全局与项目 `AGENTS.md`。不复制项目规则、不代替 `code-review`、不发明部署手册。

## 环节 skill

按顺序。每次完整读取对应 `SKILL.md` 再执行。定位：与本 skill 同级的目录，或 `local-skill find <name>` 返回的 `skill_file`。读不到则 `BLOCKED`，不要凭记忆补环节。

| 顺序 | skill | 环节 |
|---|---|---|
| 1 | `keel-issue` | 定位仓库、Issue、验收与已完成阶段 |
| 2 | `keel-how` | 讲清将改现有子系统怎么工作（带出处） |
| 3 | `keel-design` | 若需 L1：写出提案并交回 |
| 4 | `keel-dev` | 实现已定位范围，填写 `S1…Sn` |
| 5 | `keel-verify` | 按应用仓库 `.agents/skills/verify-*` 驾驶手册与功能地图证明 S1 |
| 6 | `keel-review` | 独立审查；未 `PASS` 不得进入发布 |
| 7 | `keel-release` | CI、PR/MR、合入；有 runbook 则部署与健康检查 |

状态机：`intake → keel-how → design-write-if-triggered → implementation → tests → keel-verify → independent-review → CI → merge → deploy → health-verify`

凭证据续跑，不重放已完成阶段。跳过某环节须写明原因。更窄的「把剩下代码写完」清单不能替换这台机器。

## 选择模式

在「先读 `keel-issue`」之前先看意图是不是进仓或开票：

- **打开项目 / 待办 / 分支什么情况 / code start / `keel-start`** → 只读 `keel-start`，停。不要进入 route / design / dev / end-to-end，不要先扫全仓再处理 Issue。
- **已有 Issue N**，或续跑这张票 → 先读 `keel-issue`（本会话已定位过则可 `skip: 已定位`）。然后按下述 mode。不要先跑 `keel-start`。
- **没有 Issue 号**，且意图是开票 / 建 Issue / 跟踪需求 / `keel-ticket` → 只读 `keel-ticket`，建完停。不要进入 route / design / dev / end-to-end。
- **没有 Issue 号**，且意图是处理 / 设计 / 开发 / 端到端 → 只读 `keel-issue`（它会问号）。禁止改道 `keel-ticket` 去建票。

已定位之后：

- **route** — 「处理 Issue N」：只执行下一合法环节一份，然后停。下一刀是设计或实现、且还没有对将改子系统的机制说明时，下一合法环节是 `keel-how`。实现已做、尚未按手册在真路径上证明时，下一合法环节是 `keel-verify`。
- **design** — 「设计 Issue N」：`keel-how`（可按该环节 skip）→ `keel-design`，停在人工批准。
- **dev** — 「开发 Issue N」：`keel-how`（可按该环节 skip）→ 若需 L1 且无提案则先 `keel-design`（写完继续，不等批）→ `keel-dev` → `keel-verify` → `keel-review`，停在可发布，不合入。
- **end-to-end** — 「端到端完成」/「端到端改」：从下一合法环节执行到 `keel-release`；`keel-how` 在设计/实现前，`keel-verify` 在 `keel-review` 之前。用户要端到端但计划漏了 how/验证/审查/CI/合入时，计划不完整：补上或 `BLOCKED`。禁止默默丢掉。

「端到端完成」授权的是这条有范围的生命周期，不是绕过仓库策略、保护分支、审查硬条件、或未授权的合入/部署。`when-to-ask.md` 里未授权的项不得做，即使流程是 `end-to-end`。

## 完成

说出停在哪一阶段、读过哪些环节 skill。带上该阶段要求的证据（验收表、审查结果、PR/MR 或合入 SHA、若有的部署结果）。未合入则说 `BLOCKED` 和那一个下一步决策。门禁挡住时，把挡住说清楚才算有效。

沉淀不在本状态机内。用户说 `keel-reflect` / `reflection` / 复盘时，再完整读取 `keel-reflect`。不要在端到端结束时默认跑复盘。

建票不在本状态机内。用户说 `keel-ticket` / 开票 / 建 Issue 时，再完整读取 `keel-ticket`。建完不默认 `route`。

进仓不在本状态机内。用户说 `keel-start` / code start / 打开这个项目 / 待办时，再完整读取 `keel-start`。看完不默认 `route`。不调用 monastery。

风格不在本状态机内。用户说 `cat-mode` 时再完整读取 `cat-mode`。`cat-mode` 不启动 route / design / dev / end-to-end。

Grok Bot 技能同步不在本状态机内。用户说 `keel-sync` / keel 更新了 时再完整读取 `keel-sync`。`keel-sync` 不启动 route / design / dev / end-to-end。
