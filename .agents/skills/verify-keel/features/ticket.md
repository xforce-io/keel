# `keel-ticket` 挂载与分支合同

CLI / 文件入口。不建真实 Issue。

## 用户入口（必须都走）

1. **挂载**：Launch 之后确认 `$HOME/.local/share/agent-skills/library/keel-ticket/SKILL.md` 指向本仓库 `skills/keel-ticket/SKILL.md`。
2. **查找**：PATH 上的 `local-skill find keel-ticket`（scratch 里可用测试用 fake，或本机已装的 `local-skill`）退出码 `0`。
3. **合同原文**：读本仓库 `skills/keel-ticket/SKILL.md`、`skills/keel/SKILL.md`、`skills/keel-issue/SKILL.md`、`skills/keel-release/SKILL.md`。

## #4 S1–S4

1. 入口 1：`keel-ticket` 已挂，不是 `未安装`。
2. 入口 2：能找到该 skill。
3. 入口 3：
   - `keel-ticket` 含 `feat/{issue}-{short-desc}` 与 `bugfix/{issue}-{short-desc}`，从默认分支 `checkout -b`，GitLab 字段为 `title`/`description`，且写明建完停止、不自动 route。
   - 根 skill 1–7 表没有 `keel-ticket`；无号 + 开票走 `keel-ticket`；无号 + 处理/设计/开发/端到端只走 `keel-issue`、禁止改道建票。
   - `keel-issue` 与 `keel-release` 对非法前缀写 `BLOCKED`。

判定：`ls -l` / `local-skill find` / 原文摘录存证。

## 不做

不在 Drive 里对本机 origin 跑 `gh issue create`。不把本机 `~/.claude/skills/create-github-issue` 当手册。
