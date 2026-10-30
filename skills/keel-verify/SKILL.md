---
name: keel-verify
description: >
  Use when the user says keel-verify or /keel-verify, or when keel routes to
  app-driving proof after implementation and before independent review. Locate
  the project-local handbook at .agents/skills/verify-* (SKILL.md + features/).
  Do not look under .cursor or the retired .grok/skills. Do not merge or run
  post-deploy health checks.
---

# keel-verify

在**真用户路径**上证明本 Issue 的 `S1…Sn` 及适用的 L1.8 验收。驾驶手册和功能地图在**当前应用仓库**，不在 keel 插件仓库。

本环节不是 `keel-release` 合入后的健康检查。

## 核对已有环境

先从验收要求出发，核对会话和项目已经提供的测试环境、连接方式、数据/服务及版本、所需凭据的取用方式和授权范围，给出本次路径的适用性判断。已有信息直接使用，不重复索要；无适用环境时说明原因，按原验收条件执行，不虚构地址或凭据。

环境适用且执行条件满足、操作已获授权时，主动从实际入口执行相关业务路径，即使 Unit 或模拟验证已经通过。判断依据是业务响应及必要的持久化/下游结果，不能只看主机可达、连接建立或命令退出码 0。记录实际运行版本与候选的关系；无法确认关系时，不把该环境结果当成当前候选的通过证据。

手册提供操作路径，验收合同决定证明对象，会话可以提供环境事实。手册只列模拟路径不能成为忽略已有环境的理由；路径或映射缺口按下文处理，不静默退回模拟，不降低标准。提供环境不自动授权部署、破坏性操作或访问无关数据，沿用既有授权规则；证据不得包含凭据明文。

## 定位手册

应用仓库根目录下，只认宿主中性的：

```text
.agents/skills/verify-<app>/SKILL.md
.agents/skills/verify-<app>/features/
```

用本目录的 `lookup.py`（`python3 skills/keel-verify/lookup.py <app-root>`，或已安装 skill 目录里的同名文件）。它**不搜索 `.cursor`**，**也不把旧的 `.grok/skills/verify-*` 当手册**。`.cursor/skills/verify-*` 即使存在也当作没有手册。三件缺一不可：`SKILL.md`、`features/`、`features/README.md`；缺件的目录在输出 `incomplete` 里列出，按缺手册处理，不要补猜。

- 找到一份：完整读取该 `SKILL.md`（Launch / Doctor / Drive / Evidence / Cleanup），再读 `features/README.md` 与本次要对的功能文件。
- 找到多份：问哪一个 `verify-*`，不要猜。
- 找不到：见下方缺手册。
- 输出带 `legacy`：应用仓库还留着 `.grok/skills/verify-*`。它不是手册。`missing` 时按缺手册处理，`found` 时手册照常可用；两种情况都只把 `hint` 原话转给用户，不要自己代读旧路径。迁移该搬、该先合再删、还是直接删，由 `lookup.py` 按目标路径是否已被占用判定并写进 `hint`；本文件不复述那些命令，你也不要自己拼——照抄 `hint`，别加删除动作。

## 缺手册

| 本次改动 | 结果 |
|---|---|
| 用户能摸到的界面（Web / CLI / TUI / 桌面 / 主 API 路径） | `BLOCKED`。问一次：生成手册，或本 Issue 无界面可 skip。不要即兴点 UI，不要去 `.cursor` 找替身。 |
| 明确无用户界面（纯库、内部重构），且 `S1` 已是可跑命令 | `skip`，表上写明「无用户路径」。 |

禁止把「没有 `.cursor`」当成缺手册的理由；缺的是 `.agents/skills/verify-*`。仓库里只有旧 `.grok/skills/verify-*` 时同样算缺手册，让人迁移，不要替它读。

## 把验收对到功能文件

`S1…Sn` 是本 Issue 验收；`features/` 是产品目录。用户可见的 Story 必须对上一个主要功能文件（文件名或 README 条目），并覆盖其全部适用必需子项及关联路径。

先读取适用 L1/L2 的确切版本、L1.8 与 L2.8 映射；L2 不适用时映射在 L1.8。规则见 [设计合同](../keel-design/references/design-contract.md)。L1 不适用时直接对照 Issue 及沿用契约，不补造验收编号。功能地图与产品标准冲突时先修正映射或解决设计冲突，不降低标准。

- 对不上 → `BLOCKED`：验收不在地图上。不要拿顺手入口顶替。
- 对上 → 只 Drive **这些功能**，外加本次可能碰到的、先前已 pass 的功能。
- 功能文件若列出多条用户入口（工具栏 / 快捷键 / CLI），只走一条方便入口算**未完成**。
- 不要每次开完整张地图；全图是维护循环，不在本环节。

## 修复后的增量复验

先按 [复验准备合同](references/reverification.md) 用 `keel reverify` 核对受影响项、当前依赖与历史依据、前置检查和下一批预算。新 SHA 本身不要求所有业务重新分析；依赖变化或无法确认则重验，产品明确要求最终候选 Agent 实跑时不得保留替代。保留原始记录及原 SHA，另留当前适用性核对，不把 READY 当产品 PASS。所有适用必需项仍须有充分依据，真实路径及完整独立审查不省略。已有授权和预算内直接执行，达边界停止新增昂贵运行并报告累计消耗/缺口；未知计量不补零。

## 维护回归（无 Issue / 全图）

用户明确说「全图」「回归」「维护循环」或 `keel-verify-maintain` 时：完整读取 `../keel-verify-maintain/SKILL.md` 再执行。仍用 `lookup.py` 找到的 `verify-*`。证据目录用应用仓库 `.grok/verify-runs/regression/`（或不进 git 的用户给定 run id）。完成表**不**交给 `keel-review`。本文件不展开维护步骤。

无上述口语、又没有 Issue `S1…Sn` → 仍 `BLOCKED`，不要即兴点 UI。

按手册 Launch → Doctor → Drive 对上的功能（或维护回归的全图）→ 留下 Evidence 节规定的证据 → Cleanup。Cleanup 不得吃掉证据。

修复任务读取 how 的原问题证据，以相关条件可比的原入口和输入对照候选结果，注明环境/版本差异；不能把换输入、换环境当成修复效果。符合预期才支持修复结论；问题仍在记 fail，返回 how 调查后继续原流程；原路径无法运行时保留未验证项、缺口及对完成判定的影响。此前未复现的任务如实引用替代依据和限制，不编造前后对照；仅 Unit 通过不能替代必要原路径验证。

## 送审预检

交给 `keel-review` 之前，对当前候选运行 `keel preflight`。输入合同在 [送审预检](references/preflight.md)。必需编号、分支或阶段收尾、入口由调用方从产品基线或沿用契约独立确认，不能从待检证据反推。失败则本次不能交接，回到对应验收补证后重跑。通过只对本次候选及其关联证据有效；候选或关联证据变化后必须重跑，不得沿用旧的通过结果。预检不生成运行事实，不批准交付，不代替独立审查或 `keel check`。

## 完成

逐项记录验收 ID、设计版本、候选 SHA、环境与时间、所用入口、可观察结果、证据路径及 `pass / fail / blocked / not_run`，再汇总到功能和 S 行。`skip` 仅限有依据的不适用项；缺环境、缺人工判断、未执行不得记为 skip。所有适用必需项均 pass，且当前候选的预检为通过，才交给 `keel-review`。不能用 API 测试替代要求的图形操作，也不能用 mock 结果冒充真实服务验证；后续效果观察单列，不冒充交付证据。本环节不合入、不部署。

业务行为违背预期记 fail；缺凭据、凭据被拒等条件导致预期业务无法验证记 blocked，保留尝试或条件缺口、未验证项和下一步。认证拒绝是否符合预期仍由该项合同决定。不得用模拟通过、改记观察或转挂 Issue 消除必需项的未验证事实；合法范围调整沿用产品基线确认规则。条件补齐后对同一验收 ID 重验，以新证据更新结果并保留原受阻记录。
