# `keel uninstall`

只拆 keel 自己挂上的链接或副本。外人不删。

## 用户入口（必须都走）

1. **全拆**：已 install 的 scratch 上 `./bin/keel --home "$HOME" --bin-dir "$BIN" uninstall`
2. **留 CLI**：另一份已 install 的 scratch 上 `./bin/keel --home "$HOME2" --bin-dir "$BIN2" uninstall --keep-bin`
3. **外人**：scratch library 里放一个不是 keel 的 `keel/` 目录，install（会 skip 该项），再 `uninstall`

## 路径 → 可判定结果

| # | 路径 | 可判定结果 |
|---|---|---|
| A | 入口 1 | library 下九个 `keel*` 与 `$BIN/keel` 消失；`$HOME/.config/keel/state.json` 消失 |
| B | 入口 2 | library 下 `keel*` 消失；`$BIN2/keel` 仍在 |
| C | 入口 3 | 输出含 `library/keel: skip-foreign`；外来目录还在 |

判定：uninstall 全文 + 拆后 `test ! -e` / `test -e` 存证。

## 不做

不对用户现网家目录跑 uninstall。
