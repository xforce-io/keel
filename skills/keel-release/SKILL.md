---
name: keel-release
description: >
  Use when the user says keel-release or /keel-release, or when keel routes
  to CI, PR/MR, merge, or deploy. Land only after independent review PASS and the human gate is satisfied.
  Do not invent deploy or rollback commands.
---

# keel-release

只在审查 `PASS`、且（`human: optional` 或 `human: required` 已有同候选的有效 `human_approval`）、且结论含 `reviewer_host` / `reviewer_model` / `source`、且验收表没有阻塞 `fail` 或缺失 `S*` 行之后继续。`human: required` 但缺有效人工批准、缺 `human`、或缺三列任一 → `BLOCKED`，不合入。允许的 `skip` 留在 PR/MR 上可见，不变成 pass。

用户可见票还须有 `keel-verify` 完成表（每个对上的功能 `pass|skip`、入口、证据路径）。只有 `keel-dev` 的 pytest / HTTP 验收表 → `BLOCKED`，不准开或合 PR/MR。无用户界面且 dev 表已写「无用户路径」的 `skip` 可以没有 Drive 证据。

当前分支必须是 `feat/{issue}-*` 或 `bugfix/{issue}-*`，且 `{issue}` 等于本 Issue 号。默认分支或其它前缀（`chore/*`、`cursor/*`、`fix/*`、号对不上）→ `BLOCKED`。不改名、不改道 `keel-ticket`、不合入。

合入前运行平台中立的 `keel check`（合同与示例见 [交付校验](references/check.md)）。调用方先从任务、当前候选和项目环境独立确认 Issue、完整 SHA、S1…Sn、必需 CI 清单，并核对原始证据真实性与合法 skip，不能从待检索引反向推导期望值。非零或执行不可用 → `BLOCKED`，按输出回对应环节；通过后候选或证据改变须重查。`PASS` 只说明本次输入符合校验合同，不代替独立审查或平台保护。keel 不负责采集平台 CI、配置 CI 或执行合入；实际操作继续使用项目已有方式。此工具不为缺失的人工批准补签。

按有效仓库惯例创建或更新 PR/MR，等待必需 CI 与平台检查。检查失败或仍在进行时不合入。表写入 PR/MR 正文。

合入 = 默认分支（或项目写明的集成分支）已包含该变更。本地重启、对未提交文件提供服务、脏树上测试通过，都不是合入。缺 Issue 号不是跳过 PR/MR 的理由。

环境、部署、健康检查、回滚只认项目 runbook。不编造目标环境、合入策略、部署命令或回滚。合入前确认项目是否有部署阶段；有则从 runbook 确认目标环境、如何识别该环境实际运行的版本、健康检查的可判定标准、有限的观察时限及适用的失败处理。缺任一必要依据 → `BLOCKED`，对外变更前只问一个问题；不以「部署命令成功」代替健康结果。

生产顺序：`merge → deploy/update service → health verification`。按 runbook 在观察时限内核对实际运行版本及健康结果；达到其通过标准后，本次发布结束。报告写明目标环境、实际运行版本及其证据、健康检查依据、观察时限、观察结果和结束状态。后续持续监控或故障调查另行处理，不让本次 release 无限期等待。

部署或健康检查失败、超出观察时限、或无法确认实际运行版本时 → `BLOCKED`。仅执行 runbook 记载且已获授权的适用回滚；报告已执行的处理、观察到的状态与一个下一步决策。不能回滚时也报告当前状态，不猜命令、不宣称端到端完成。项目没有部署阶段则合入后结束，并明说没有线上健康检查。

生产部署在合入之后。预合入部署仅当项目明确记录了 staging / preview。
