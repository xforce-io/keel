# `keel-review` 人介入合同

CLI / 文件入口。不跑独立审查、不合入。

Launch 前先 `mkdir "$HOME/.grok"`，以便 scratch 挂上 `reviewer`。

## 用户入口（必须都走）

1. **挂载**：Launch 之后 `$HOME/.local/share/agent-skills/library/keel-review/SKILL.md` 与 `…/keel-release/SKILL.md` 指向本仓库对应 skill；`$HOME/.grok/agents/reviewer.md` 指向本仓库 `agents/reviewer.md`。
2. **查找**：`local-skill find keel-review` 退出码 `0`。
3. **合同原文**：读本仓库 `skills/keel-review/SKILL.md`、`skills/keel-release/SKILL.md`、`skills/keel-verify/SKILL.md`、`agents/reviewer.md`。

## #7 S1–S3

1. 入口 1：`keel-review`、`keel-release`、`reviewer` 已挂，不是 `未安装`。
2. 入口 2：能找到 `keel-review`。
3. 入口 3：
   - 审查结论必须有恰好一个 `human: required` 或 `human: optional`；缺字段视为审查未完成。
   - 硬条件（表面 / `P0` / 三轮 / 无法独立）不得标 `optional`。
   - `keel-release` 可发布 = `PASS` 且 `human: optional`；`required` 或缺字段 → `BLOCKED`。

## #10 S1–S3

1. 入口 3 / `keel-review`：宿主表有 Cursor；模型顺序是用户点名 → `~/.config/keel/reviewer` → 宿主配置 → 互补 → `BLOCKED`；禁止 `inherit` 与未声明自选。
2. 入口 3 / 结论：必须有 `reviewer_host`、`reviewer_model`、`source`（`user` / `bind-file` / `host-config` / `complementary`）；缺一则审查未完成。`keel-release` 缺三列 → `BLOCKED`。
3. 入口 3 / `keel-verify`：有「维护回归（无 Issue / 全图）」段；完成表不交 `keel-review`。

判定：`ls -l` / `local-skill find` / 原文摘录存证。

## 不做

不在 Drive 里调 Reviewer。不改外部 `code-review`。不对本机现网 `~/.grok/agents/reviewer.md` 做 install / uninstall。
