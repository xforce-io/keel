---
name: keel-release
description: >
  Use when the user says keel-release or /keel-release, or when keel routes
  to CI, PR/MR, merge, or deploy. Land only after independent review PASS
  and human: optional.
  Do not invent deploy or rollback commands.
---

# keel-release

只在审查 `PASS`、且 `human: optional`、且结论含 `reviewer_host` / `reviewer_model` / `source`、且验收表没有阻塞 `fail` 或缺失 `S*` 行之后继续。`human: required`、缺 `human`、或缺三列任一 → `BLOCKED`，不合入。允许的 `skip` 留在 PR/MR 上可见，不变成 pass。

用户可见票还须有 `keel-verify` 完成表（每个对上的功能 `pass|skip`、入口、证据路径）。只有 `keel-dev` 的 pytest / HTTP 验收表 → `BLOCKED`，不准开或合 PR/MR。无用户界面且 dev 表已写「无用户路径」的 `skip` 可以没有 Drive 证据。

当前分支必须是 `feat/{issue}-*` 或 `bugfix/{issue}-*`，且 `{issue}` 等于本 Issue 号。默认分支或其它前缀（`chore/*`、`cursor/*`、`fix/*`、号对不上）→ `BLOCKED`。不改名、不改道 `keel-ticket`、不合入。

按有效仓库惯例创建或更新 PR/MR，等待必需 CI 与平台检查。检查失败或仍在进行时不合入。表写入 PR/MR 正文。

合入 = 默认分支（或项目写明的集成分支）已包含该变更。本地重启、对未提交文件提供服务、脏树上测试通过，都不是合入。缺 Issue 号不是跳过 PR/MR 的理由。

环境、部署、健康检查、回滚只认项目 runbook。不编造目标环境、合入策略、部署命令或回滚。缺事实时，对外变更前只问一个问题。

生产顺序：`merge → deploy/update service → health verification`。部署或健康检查失败时，只执行文档里的回滚，并报告观察到的状态。项目没有部署阶段则合入后结束，并明说。

生产部署在合入之后。预合入部署仅当项目明确记录了 staging / preview。
