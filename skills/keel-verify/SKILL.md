---
name: keel-verify
description: >
  Use when the user says keel-verify or /keel-verify, or when keel routes to
  app-driving proof after implementation and before independent review. Locate
  the project-local handbook at .grok/skills/verify-* (SKILL.md + features/).
  Do not look under .cursor. Do not merge or run post-deploy health checks.
---

# keel-verify

在**真用户路径**上证明本 Issue 的 `S1…Sn`。驾驶手册和功能地图在**当前应用仓库**，不在 keel 插件仓库。

本环节不是 `keel-release` 合入后的健康检查。

## 定位手册

应用仓库根目录下，只认：

```text
.grok/skills/verify-<app>/SKILL.md
.grok/skills/verify-<app>/features/
```

用本目录的 `lookup.py`（`python3 skills/keel-verify/lookup.py <app-root>`，或已安装 skill 目录里的同名文件）。它**不搜索 `.cursor`**。`.cursor/skills/verify-*` 即使存在也当作没有手册。

- 找到一份：完整读取该 `SKILL.md`（Launch / Doctor / Drive / Evidence / Cleanup），再读 `features/README.md` 与本次要对的功能文件。
- 找到多份：问哪一个 `verify-*`，不要猜。
- 找不到：见下方缺手册。

## 缺手册

| 本次改动 | 结果 |
|---|---|
| 用户能摸到的界面（Web / CLI / TUI / 桌面 / 主 API 路径） | `BLOCKED`。问一次：生成手册，或本 Issue 无界面可 skip。不要即兴点 UI，不要去 `.cursor` 找替身。 |
| 明确无用户界面（纯库、内部重构），且 `S1` 已是可跑命令 | `skip`，表上写明「无用户路径」。 |

禁止把「没有 `.cursor`」当成缺手册的理由；缺的是 `.grok/skills/verify-*`。

## 把 S1 对到功能文件

`S1…Sn` 是本 Issue 验收；`features/` 是产品目录。用户可见的 Story 必须对上一个功能文件（文件名或 README 条目）。

- 对不上 → `BLOCKED`：验收不在地图上。不要拿顺手入口顶替。
- 对上 → 只 Drive **这些功能**，外加本次可能碰到的、先前已 pass 的功能。
- 功能文件若列出多条用户入口（工具栏 / 快捷键 / CLI），只走一条方便入口算**未完成**。
- 不要每次开完整张地图；全图是维护循环，不在本环节。

按手册 Launch → Doctor → Drive 对上的功能 → 留下 Evidence 节规定的证据 → Cleanup。Cleanup 不得吃掉证据。

## 完成

表上为每个对上的功能记 `pass|fail|skip`、所用入口、证据路径。全部 `pass`（或规则允许的 `skip`）才交给 `keel-review`。本环节不合入、不部署。
