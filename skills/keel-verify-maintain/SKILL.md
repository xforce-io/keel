---
name: keel-verify-maintain
description: >
  Use when the user says keel-verify-maintain, 维护循环, 全图, or 回归
  without an Issue, or when keel-verify routes map upkeep. Audit
  .agents/skills/verify-* features against source user surfaces. Do not
  edit product code, do not merge, do not run keel-review.
---

# keel-verify-maintain

保养应用仓库的**功能地图**。不是交付环节，不代替 `keel-verify`（有 Issue 的 `S1…Sn` 真路径证明）。

## 定位手册

与 `keel-verify` 相同：只认 `.agents/skills/verify-<app>/`（`SKILL.md` + `features/` + `features/README.md`）。用 `keel-verify/lookup.py`。多份则问哪一个。缺手册 → 指向生成手册，停；不要即兴点 UI，不要读 `.cursor` 或旧 `.grok/skills`。

## 只改哪里

只编辑该 `verify-*` 目录（`SKILL.md`、`features/`、手册自带的 helper）。**不改产品代码。** 地图描述了应用已经不做的行为：改地图。应用坏了：记给用户，不要用文档遮。

## 步骤

1. **索引。** 读 `features/README.md`，glob 同级功能文件。缺行、多余、重复、死链 → 改 README 或删/补文件。
2. **源码对照。** 每个功能文件对照源码入口（路由、命令、模板）。标漂移（有出处）。扫最近用户可见 churn：源码里能指出路径的新面不在地图上 → 新增文件并改 README。
3. **Live（用户说全图/回归时）。** 按该手册 Launch → Doctor → Drive **全部**功能文件及各文件列出的每一条用户入口。证据目录：应用仓库 `.grok/verify-runs/regression/`（或不进 git 的用户给定 run id）。Cleanup 不得吃掉证据。
4. **结束。** 完成表**不**交给 `keel-review`。三种结果之一：`clean`（覆盖完、无改动）、`changed`（只交了地图/手册修正）、`blocked`（覆盖不完或不能安全改手册）。不合入、不部署。

无「全图 / 回归 / 维护循环」口语、又没有 Issue `S1…Sn` → `BLOCKED`，不要即兴点 UI。有 Issue 的证明走 `keel-verify`。
