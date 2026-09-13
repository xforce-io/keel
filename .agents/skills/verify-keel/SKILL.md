---
name: verify-keel
description: Use when keel-verify must drive the keel CLI on a real user path (install, doctor, uninstall). Never point Drive at the live home.
---

# verify-keel

驾驶 **keel CLI**（`bin/keel`：install / doctor / uninstall）。Issue 验收对 `features/`；只 Drive 对上的功能文件。

本仓库是插件仓，也是这份手册所在的应用仓。`install` 挂的是 `skills/keel*`，**不**写入应用仓库的 `.agents/skills/verify-*`。

## Launch

在**本仓库当前分支**跑 CLI，不要用 PATH 上过期的 `keel`。Drive 一律走 scratch `--home`，禁止对现网家目录做 install / uninstall。

```bash
HOME=$(mktemp -d /tmp/keel-verify-home.XXXX)
BIN="$HOME/.local/bin"
# 本机 PATH 里要有能 `local-skill find code-review` 的 local-skill（keel-review 依赖它）。
# 不要为了验证去卸用户的 code-review。
./bin/keel --home "$HOME" --bin-dir "$BIN" install
```

`library` 是必挂宿主。其它宿主（grok / claude / cursor / …）只有 scratch home 下对应探测目录存在才会挂。需要测某宿主时，Launch 里先 `mkdir` 再 install。

## Doctor

全部成立才 Drive：

1. `./bin/keel --home "$HOME" --bin-dir "$BIN" doctor` 退出码 `0`
2. 输出含 `root:` 指向本仓库，且 `skills:` 列出 `keel keel-design keel-dev keel-how keel-issue keel-reflect keel-release keel-review keel-start keel-ticket keel-verify`
3. `library/keel` 与 `bin` 均为本 CLI 的 symlink 或 copy，不是 `未安装` / `占用且不是 keel`
4. `code-review: ok`（来自 PATH 上的 `local-skill find`）

失败则 `BLOCKED`，不要对现网家目录补救。

## Drive

只打开 `features/` 里对上本 Issue `S1…Sn` 的文件（外加本次会碰到的、先前已 pass 的功能）。文件列出的**每一条用户入口都要走**；只跑 unittest 或只跑一条 CLI 算未完成。

需要隔离宿主时另开 scratch home，不要复用已污染的 `$HOME`。

## Evidence

每次 Drive 写入仓库 `.agents/verify-runs/<issue-no>/`（该目录不进 git）：

| 文件 | 内容 |
|---|---|
| `doctor.txt` | Doctor 命令、退出码、全文 |
| `sN.txt` | 所用入口、关键输出行、判定 |

命令输出原文存证。不得把 scratch home 路径写进仓库文件。

## Cleanup

```bash
./bin/keel --home "$HOME" --bin-dir "$BIN" uninstall
rm -rf "$HOME"
```

只拆本次 scratch。**不得**对用户现网 `~/.config/keel` / `~/.local/bin/keel` 跑 uninstall。**不得删除** `.agents/verify-runs/`。
