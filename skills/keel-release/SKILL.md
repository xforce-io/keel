---
name: keel-release
description: >
  Use when the user says keel-release or /keel-release, or when keel routes
  to CI, PR/MR, merge, or deploy. Land only after independent review PASS.
  Do not invent deploy or rollback commands.
---

# keel-release

只在审查 `PASS`、且验收表没有阻塞 `fail` 或缺失 `S*` 行之后继续。允许的 `skip` 留在 PR/MR 上可见，不变成 pass。

按有效仓库惯例创建或更新 PR/MR，等待必需 CI 与平台检查。检查失败或仍在进行时不合入。表写入 PR/MR 正文。

合入 = 默认分支（或项目写明的集成分支）已包含该变更。本地重启、对未提交文件提供服务、脏树上测试通过，都不是合入。缺 Issue 号不是跳过 PR/MR 的理由。

环境、部署、健康检查、回滚只认项目 runbook。不编造目标环境、合入策略、部署命令或回滚。缺事实时，对外变更前只问一个问题。

生产顺序：`merge → deploy/update service → health verification`。部署或健康检查失败时，只执行文档里的回滚，并报告观察到的状态。项目没有部署阶段则合入后结束，并明说。

生产部署在合入之后。预合入部署仅当项目明确记录了 staging / preview。
