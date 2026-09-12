---
name: keel
description: >
  Use when the user says keel, /keel, 处理 Issue, 设计 Issue, 开发 Issue,
  端到端完成, 端到端改, or asks to ship, merge, or continue a guarded delivery
  lifecycle. Routes to stage skills; do not use for isolated code review or
  post-task reflection.
---

# keel

只做**路由**。推进**一个**任务的下一合法交付阶段。环节规则在独立 skill 里，这里不抄。

服从当前有效的全局与项目 `AGENTS.md`。不复制项目规则、不代替 `code-review`、不发明部署手册。

## 环节 skill

按顺序。每次完整读取对应 `SKILL.md` 再执行。定位：与本 skill 同级的目录，或 `local-skill find <name>` 返回的 `skill_file`。读不到则 `BLOCKED`，不要凭记忆补环节。

| 顺序 | skill | 环节 |
|---|---|---|
| 1 | `keel-issue` | 定位仓库、Issue、验收与已完成阶段 |
| 2 | `keel-how` | 讲清将改现有子系统怎么工作（带出处） |
| 3 | `keel-design` | 若设计门禁触发：提案并停在人工批准 |
| 4 | `keel-dev` | 实现已批准范围，填写 `S1…Sn` |
| 5 | `keel-verify` | 按应用仓库 `.grok/skills/verify-*` 驾驶手册与功能地图证明 S1 |
| 6 | `keel-review` | 独立审查；未 `PASS` 不得进入发布 |
| 7 | `keel-release` | CI、PR/MR、合入；有 runbook 则部署与健康检查 |

状态机：`intake → keel-how → design-required? → human-approved → implementation → tests → keel-verify → independent-review → CI → merge → deploy → health-verify`

凭证据续跑，不重放已完成阶段。跳过某环节须写明原因。更窄的「把剩下代码写完」清单不能替换这台机器。

## 选择模式

先读 `keel-issue`（本会话已定位过则可 `skip: 已定位`）。然后：

- **route** — 「处理 Issue N」：只执行下一合法环节一份，然后停。下一刀是设计或实现、且还没有对将改子系统的机制说明时，下一合法环节是 `keel-how`。实现已做、尚未按手册在真路径上证明时，下一合法环节是 `keel-verify`。
- **design** — 「设计 Issue N」：`keel-how`（可按该环节 skip）→ `keel-design`，停在人工批准。
- **dev** — 「开发 Issue N」：`keel-how`（可按该环节 skip）→ `keel-dev` → `keel-verify` → `keel-review`，停在可发布，不合入。
- **end-to-end** — 「端到端完成」/「端到端改」：从下一合法环节执行到 `keel-release`；`keel-how` 在设计/实现前，`keel-verify` 在 `keel-review` 之前。用户要端到端但计划漏了 how/验证/审查/CI/合入时，计划不完整：补上或 `BLOCKED`。禁止默默丢掉。

「端到端完成」授权的是这条有范围的生命周期，不是绕过仓库策略、保护分支、人工批准或缺失的部署事实。

## 完成

说出停在哪一阶段、读过哪些环节 skill。带上该阶段要求的证据（验收表、审查结果、PR/MR 或合入 SHA、若有的部署结果）。未合入则说 `BLOCKED` 和那一个下一步决策。门禁挡住时，把挡住说清楚才算有效。

沉淀不在本状态机内。用户说 `keel-reflect` / `reflection` / 复盘时，再完整读取 `keel-reflect`。不要在端到端结束时默认跑复盘。
