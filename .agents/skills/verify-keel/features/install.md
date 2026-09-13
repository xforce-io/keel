# `keel install`

把本仓库 `skills/*` 与 `bin/keel` 挂到 scratch `--home`。不改产品代码。

## 用户入口（必须都走）

1. **符号链接**：`./bin/keel --home "$HOME" --bin-dir "$BIN" install`
2. **复制**：另开一个 scratch home，`./bin/keel --home "$HOME2" --bin-dir "$BIN2" install --copy`

不要跑 `--plugin`（会碰现网 grok plugin）。

## 路径 → 可判定结果

| # | 路径 | 可判定结果 |
|---|---|---|
| A | 入口 1，scratch home 只有默认探测面 | 退出码 `0`；`$HOME/.local/share/agent-skills/library/{keel,keel-design,keel-dev,keel-how,keel-issue,keel-reflect,keel-release,keel-review,keel-start,keel-ticket,keel-verify}` 均为指向本仓库 `skills/<name>` 的 symlink；`$BIN/keel` 指向本仓库 `bin/keel`；`$HOME/.agents/skills/` 不出现任何 `keel*` |
| B | scratch home 先 `mkdir "$HOME/.cursor"` 再入口 1 | `cursor/keel` 也是 symlink；其它未探测宿主（无目录）不出现在输出里 |
| C | 入口 2 | 退出码 `0`；library 与 bin 是 copy 不是 symlink；再次 `install --copy` 仍退出码 `0` 且内容刷新 |

判定：命令全文 + `ls -l` / `readlink` 存证。

## 不做

不把 skill 写进 `~/.agents/skills/`。不覆盖 scratch 里已存在且不是 keel 的同名目录——那种情况见 [doctor.md](./doctor.md) 的占用路径。
