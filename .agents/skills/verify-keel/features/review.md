# `keel-review` 人介入合同

CLI / 文件入口。不跑独立审查、不合入。

Launch 前先 `mkdir "$HOME/.grok"`，以便 scratch 挂上 `reviewer`。

## 用户入口（必须都走）

1. **挂载**：Launch 之后 `$HOME/.local/share/agent-skills/library/keel-review/SKILL.md` 与 `…/keel-release/SKILL.md` 指向本仓库对应 skill；`$HOME/.grok/agents/reviewer.md` 指向本仓库 `agents/reviewer.md`。
2. **查找**：`local-skill find keel-review` 退出码 `0`。
3. **合同原文**：读本仓库 `skills/keel-review/SKILL.md`、`skills/keel-release/SKILL.md`、`agents/reviewer.md`。

## #7 S1–S3

1. 入口 1：`keel-review`、`keel-release`、`reviewer` 已挂，不是 `未安装`。
2. 入口 2：能找到 `keel-review`。
3. 入口 3：
   - 审查结论必须有恰好一个 `human: required` 或 `human: optional`；缺字段视为审查未完成。
   - 硬条件（表面 / `P0` / 三轮 / 无法独立）不得标 `optional`。
   - `keel-release` 可发布 = `PASS` 且 `human: optional`；`required` 或缺字段 → `BLOCKED`。

判定：`ls -l` / `local-skill find` / 原文摘录存证。

## 不做

不在 Drive 里调 Reviewer。不改外部 `code-review`。不对本机现网 `~/.grok/agents/reviewer.md` 做 install / uninstall。
