---
name: keel-sync
description: >
  Use when the user says keel-sync, /keel-sync, keel 更新了, update keel,
  or 同步 keel skill. Refresh Grok Bot account-level keel skills from
  /workspace/keel. Not a delivery stage. Do not start keel route, design,
  dev, or end-to-end. Do not edit alfred or kairo product code or bot personas.
---

# keel-sync

配套 skill，不是交付环节，不是流程。

两套安装，更新方式不同。本 skill **只**更新 Grok Bot 共享电脑上的账号级 private skill。

| 目标 | 装在哪 | 更新 |
|---|---|---|
| Mac 上的 Grok / Claude / Cursor / Codex / Pi | `keel install` 符号链接到本机 checkout | `git pull` 该 checkout；**新增** `skills/*/SKILL.md` 才再跑 `keel install`；然后 `keel doctor` |
| Grok Bot 云端 bot | `/workspace/keel` + `/` 菜单里的账号级 skill | 必须走本 skill：`git pull` **不够**，还要按当前 `SKILL.md` **重写**已登记 skill |

用户说处理 Issue、端到端或 `/keel` → 交给 `keel`。本 skill 不启动 route / design / dev / end-to-end。

## 何时跑

人明确说更新 / 同步。不要做定时 routine。不要在 `/keel` 交付流程里顺手 pull。

## 步骤

1. 确认 `/workspace/keel` 是 git checkout。记下旧 HEAD：`git -C /workspace/keel rev-parse HEAD`。
2. `git -C /workspace/keel fetch origin` 然后 `git -C /workspace/keel pull --ff-only origin main`。
   - 非 fast-forward → 停，把 `git status` 给人，禁止 `reset --hard` / force push。
3. pull 之后若存在 `docs/grok-bot-box.md`，**完整读取新文件**再继续（优先于本 skill 里过期的步骤）。
4. 枚举 `/workspace/keel/skills/*/SKILL.md`（目录名 = skill 名）。
5. 对每个 skill 用正式 skill write / `update_state` **更新同名** private skill（覆盖，不要再复制一份）：
   - `keel`：正文附上 `references/when-to-ask.md` 与 `references/when-to-write.md`
   - `keel-verify`：带上目录内脚本（如 `lookup.py`）
   - `keel-reflect`：带上 `scripts/` 与 `references/`
   - `keel-sync`：从本文件更新自己
   - 其它：`SKILL.md` 全文
6. 账号级 skill 没有 per-bot 开关：写一次即该账户全部 bot 都能用。不要改人设。
7. 仓库里已删除的同名 private skill：只删本清单里的 keel skill，不要动无关 skill。清单以本次枚举为准。
8. 回报：旧 HEAD → 新 HEAD、变更的 skill 名、`/` 菜单抽样是否还能搜到、失败项。

## 不要做

- 不要在云端跑 `keel install` 冒充 Grok Bot 安装（那是 Mac coding agent 的挂载）。
- 不要改 alfred / kairo 产品代码。
- 不要改任何 bot 人设或领地。
- 不要非 ff merge、不要 `reset --hard`。
