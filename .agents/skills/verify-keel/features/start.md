# `keel-start` 挂载与进仓合同

CLI / 文件入口。不调 monastery。

## 用户入口（必须都走）

1. **挂载**：Launch 之后 `$HOME/.local/share/agent-skills/library/keel-start/SKILL.md` 指向本仓库 `skills/keel-start/SKILL.md`。
2. **查找**：`local-skill find keel-start` 退出码 `0`。
3. **合同原文**：读 `skills/keel-start/SKILL.md`、`skills/keel/SKILL.md`。

## #6 S1–S4

1. 入口 1：`keel-start` 已挂。
2. 入口 2：能找到该 skill。
3. 入口 3：
   - `keel-start` 写只读先做完、仅当本轮明确说「清」才删已合入残留、不调用 monastery。
   - 根 skill 1–7 表没有 `keel-start`；进仓走 start；处理 Issue N 不先跑 start。

判定：`ls -l` / `local-skill find` / 原文摘录存证。
