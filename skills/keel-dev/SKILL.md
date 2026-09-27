---
name: keel-dev
description: >
  Use when the user says keel-dev or /keel-dev, or when keel routes to the
  implementation stage. Implement accepted scope and fill the S1…Sn
  acceptance table. Do not self-review, merge, or deploy.
---

# keel-dev

只实现已定位范围，用项目已有手段证明，停在可送审。进入前引用适用 L1/L2 的版本、L1.8 验收与产品确认依据；确认规则只认 `../keel/references/when-to-ask.md`，已有依据不重复问。设计缺失或产品问题未明确时交回 `keel-design`，不能在实现中自行决定用户路径或降低标准。

不得在默认分支上实现本 Issue。工作分支必须是 `feat/{issue}-*` 或 `bugfix/{issue}-*`，且 `{issue}` 等于本 Issue 号，否则 `BLOCKED`。

先读 [设计与验收合同](../keel-design/references/design-contract.md)。Issue S 是汇总，适用的 L1.8 验收项是具体实现与验证目标；L1 不适用时使用已有契约与 Issue 验收，不制造 A 编号。实现与验收标准可追踪。开发中跑聚焦检查，送审前跑项目要求的套件。优先用项目已有工具（具名 pytest、套件脚本、进程内 HTTP 客户端）。不要发明仓库外的截图工厂或临时 E2E 层。

**功能地图不是「额外证据文件」。** 用户能摸到的界面（Web / CLI / TUI / 桌面 / 主 API 路径）：在宣称本环节完成前，对照应用仓库 `.agents/skills/verify-*/features/README.md` 与功能文件。每条用户可见 `S1…Sn` 指定一个主要功能文件（文件名或 README 条目），其中列全 L1.8 子项及必要的跨功能路径。对不上 → `BLOCKED`：在同一 `features/` 下新增或更新文件并改 README 一行，然后才能填验收表结束本环节。不要把 pytest 表当作地图已覆盖。明确无用户界面、且 `S1` 已是可跑命令 → 功能地图/Drive 记 `skip`，写明「无用户路径」；S 本身仍须执行适用验收。查找手册规则与 `keel-verify` 相同（`.agents` 下 `verify-*`，不读 `.cursor`，不认旧 `.grok/skills`）。

独立审查前，为这个 SHA 写验收表，覆盖本 Issue 每条 `S1…Sn`，以及本次可能碰到的、先前已 pass 的 Story：

`S1: pass|fail|blocked|not_run|skip  <command>  <one-line result or reason>`

S 行附 L1.8 子项结果索引：验收 ID、设计版本、候选 SHA、环境、命令/入口、结果与证据；所有适用必需子项均 pass 才可汇总 pass。缺环境或未运行记 blocked/not_run，不得写成 skip；skip 只接受事先明确不适用的依据。产品规则改变先回 L1，纯技术差异更新 L2。

待 keel-verify 执行的用户路径先记 not_run 并明确交接；这允许进入验证环节，但不允许宣称 S 已验收或直接送独立审查。

实现者自己跑的测试是候选门，不是最终产品验收。表必须来自冻结候选上的新跑（干净树）。`skip` 不是 pass：需要设计已明确的不适用依据，环境缺失不属于不适用。缺行、`fail`、或把 skip 当完成，都不得宣称本环节完成。续做时先读 Issue 或 PR/MR 上最新表，不要只从代码反推状态。

本环节不代替 `keel-verify` 或 `keel-review`。项目测试填表之后，真用户路径证明交给 `keel-verify`（应用仓库 `.agents/skills/verify-*`，不读 `.cursor`，不认旧 `.grok/skills`）。不要开或合 PR/MR，不要部署。
