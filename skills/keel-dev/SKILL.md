---
name: keel-dev
description: >
  Use when the user says keel-dev or /keel-dev, or when keel routes to the
  implementation stage. Implement accepted scope and fill the S1…Sn
  acceptance table. Do not self-review, merge, or deploy.
---

# keel-dev

只实现已批准范围，用项目已有手段证明，停在可送审。

实现与验收标准可追踪。开发中跑聚焦检查，送审前跑项目要求的套件。优先用项目已有工具（具名 pytest、套件脚本、进程内 HTTP 客户端）。不要新增项目没有的证据文件、截图工厂或额外 E2E 层。

独立审查前，为这个 SHA 写验收表，覆盖本 Issue 每条 `S1…Sn`，以及本次可能碰到的、先前已 pass 的 Story：

`S1: pass|fail|skip  <command>  <one-line result or skip reason>`

实现者自己跑的测试是候选门，不是验收。表必须来自冻结候选上的新跑（干净树）。`skip` 不是 pass：需要设计已允许的环境限制。缺行、`fail`、或把 skip 当完成，都不得宣称本环节完成。续做时先读 Issue 或 PR/MR 上最新表，不要只从代码反推状态。

本环节不代替 `keel-verify` 或 `keel-review`。项目测试填表之后，真用户路径证明交给 `keel-verify`（应用仓库 `.grok/skills/verify-*`，不读 `.cursor`）。不要开或合 PR/MR，不要部署。
