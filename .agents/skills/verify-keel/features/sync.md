# `keel-sync`

配套 skill：Grok Bot 共享电脑上把账号级 keel skill 更新到 `/workspace/keel`。不是交付环节。

## 用户入口（必须都走）

1. **读仓库文件**：打开本仓库 `skills/keel-sync/SKILL.md`（不要读 Grok Bot 私有登记）
2. **install 后 doctor 列出名字**：scratch `--home` 先 `install`，再 `doctor`（见 [install.md](./install.md) / [doctor.md](./doctor.md) 的已安装入口）

Grok Bot `/` 菜单与共享电脑 `git pull` 后覆盖登记：本手册不 Drive（无该电脑）。合入后由人在 box 上按该 SKILL 跑一次。

## 路径 → 可判定结果

| # | 路径 | 可判定结果 |
|---|---|---|
| A | 入口 1 | 恰好一份 `skills/keel-sync/SKILL.md`；正文含共享电脑 `git pull --ff-only` 与按 `SKILL.md` 重写账号级 skill |
| B | 入口 2 | `doctor` 退出码 `0`；`skills:` 行含 `keel-sync`；`library/keel-sync` 为指向本仓库该目录的 symlink 或 copy |

判定：文件原文 + doctor 全文存证。
