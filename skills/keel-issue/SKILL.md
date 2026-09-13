---
name: keel-issue
description: >
  Use when the user says keel-issue or /keel-issue, or when keel routes to
  the intake stage. Locate the repository, Issue, acceptance criteria, and
  already-finished stages. Do not implement, design, review, or merge.
---

# keel-issue

定位当前任务，不往下做设计或实现。

1. 先解析仓库与托管平台。进入仓库以及任何 Issue / PR·MR / 平台 API 写操作之前，按有效 `AGENTS.md` 判定 GitHub 或 GitLab，口头确认 origin。
2. 只读读取 Issue、验收标准、已链设计、分支、PR/MR、CI。遵循有效 `AGENTS.md` 的 Issue 骨架与术语。
3. 根据证据判断下一合法阶段。不要重建已经存在的 Issue、设计、分支或审查。
4. 目标 Issue 含糊、或必需验收缺失时，只问一个问题。
5. 缺 Issue 号就问，不是跳过发布。
6. 后续增量接同一 Issue 时，先读 Issue 或 PR/MR 上最新的 `S1…Sn` 表。`pass` 行若本次可能碰到，当作保全检查，不要丢掉 Story id。
7. **分支前缀。** 默认分支（`main` / `master` / `origin/HEAD`）只许定位。工作分支必须是 `feat/{issue}-*` 或 `bugfix/{issue}-*`，且 `{issue}` 等于目标 Issue 号。其它名字（`chore/*`、`cursor/*`、`fix/*`、无前缀非默认、号对不上）→ `BLOCKED`。不改名、不改道 `keel-ticket`、不重建分支。下一步：人从默认分支手工 `git checkout -b feat/{issue}-…`（或 `bugfix/`）后重入 `keel-issue`。

本环节产出：仓库、平台、Issue、验收、已完成阶段、下一合法环节。然后停，除非调用方是 `keel` 并继续路由。
