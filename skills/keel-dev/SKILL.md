---
name: keel-dev
description: >
  Use when the user says keel-dev or /keel-dev, or when keel routes to the
  implementation stage. Implement accepted scope and fill the S1…Sn
  acceptance table. Do not self-review, merge, or deploy.
---

# keel-dev

只实现已定位范围，用项目已有手段证明，停在可送审。不检查人工批准，不等人。缺 L1 提案时由调用方（通常是 `keel`）先跑 `keel-design`。

不得在默认分支上实现本 Issue。工作分支必须是 `feat/{issue}-*` 或 `bugfix/{issue}-*`，且 `{issue}` 等于本 Issue 号，否则 `BLOCKED`。

实现与验收标准可追踪。开发中跑聚焦检查，送审前跑项目要求的套件。优先用项目已有工具（具名 pytest、套件脚本、进程内 HTTP 客户端）。不要发明仓库外的截图工厂或临时 E2E 层。

**功能地图不是「额外证据文件」。** 用户能摸到的界面（Web / CLI / TUI / 桌面 / 主 API 路径）：在宣称本环节完成前，对照应用仓库 `.agents/skills/verify-*/features/README.md` 与功能文件。每条用户可见 `S1…Sn` 必须对上恰好一个功能文件（文件名或 README 条目）。对不上 → `BLOCKED`：在同一 `features/` 下新增或更新文件并改 README 一行，然后才能填验收表结束本环节。不要把 pytest 表当作地图已覆盖。明确无用户界面、且 `S1` 已是可跑命令 → 表上 `skip`，写明「无用户路径」。查找手册规则与 `keel-verify` 相同（`.agents` 下 `verify-*`，不读 `.cursor`，不认旧 `.grok/skills`）。

独立审查前，为这个 SHA 写验收表，覆盖本 Issue 每条 `S1…Sn`，以及本次可能碰到的、先前已 pass 的 Story：

`S1: pass|fail|skip  <command>  <one-line result or skip reason>`

实现者自己跑的测试是候选门，不是验收。表必须来自冻结候选上的新跑（干净树）。`skip` 不是 pass：需要设计已允许的环境限制。缺行、`fail`、或把 skip 当完成，都不得宣称本环节完成。续做时先读 Issue 或 PR/MR 上最新表，不要只从代码反推状态。

本环节不代替 `keel-verify` 或 `keel-review`。项目测试填表之后，真用户路径证明交给 `keel-verify`（应用仓库 `.agents/skills/verify-*`，不读 `.cursor`，不认旧 `.grok/skills`）。不要开或合 PR/MR，不要部署。
