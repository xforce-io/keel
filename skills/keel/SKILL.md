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
| 2 | `keel-design` | 若设计门禁触发：提案并停在人工批准 |
| 3 | `keel-dev` | 实现已批准范围，填写 `S1…Sn` |
| 4 | `keel-review` | 独立审查；未 `PASS` 不得进入发布 |
| 5 | `keel-release` | CI、PR/MR、合入；有 runbook 则部署与核对 |

状态机：`intake → design-required? → human-approved → implementation → tests → independent-review → CI → merge → deploy → verify`

凭证据续跑，不重放已完成阶段。跳过某环节须写明原因。更窄的「把剩下代码写完」清单不能替换这台机器。

## 选择模式

先读 `keel-issue`（本会话已定位过则可 `skip: 已定位`）。然后：

- **route** — 「处理 Issue N」：只执行下一合法环节一份，然后停。
- **design** — 「设计 Issue N」：执行到 `keel-design`（含未完成的设计），停在人工批准。
- **dev** — 「开发 Issue N」：`keel-dev` → `keel-review`，停在可发布，不合入。
- **end-to-end** — 「端到端完成」/「端到端改」：从下一合法环节执行到 `keel-release`。用户要端到端但计划漏了审查/CI/合入时，计划不完整：补上或 `BLOCKED`。禁止默默丢掉。

「端到端完成」授权的是这条有范围的生命周期，不是绕过仓库策略、保护分支、人工批准或缺失的部署事实。

## 完成

说出停在哪一阶段、读过哪些环节 skill。带上该阶段要求的证据（验收表、审查结果、PR/MR 或合入 SHA、若有的部署结果）。未合入则说 `BLOCKED` 和那一个下一步决策。门禁挡住时，把挡住说清楚才算有效。
