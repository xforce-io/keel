# `keel doctor`

只读检查。不改挂载、不写 `state.json`。

## 用户入口（必须都走）

1. **已安装**：Launch 之后 `./bin/keel --home "$KEEL_VERIFY_HOME" --bin-dir "$KEEL_VERIFY_BIN" doctor`
2. **未安装**：另开空 scratch home（从未 install）跑同一条 doctor
3. **占用**：空 scratch 里先放一个不是 keel 的 `library/keel/SKILL.md`，再 doctor（不要先 install）

## 路径 → 可判定结果

| # | 路径 | 可判定结果 |
|---|---|---|
| A | 入口 1 | 退出码 `0`；含 `root:` 本仓库、`skills:` 含 `keel` 与 `keel-sync`、`library/keel:` 为 symlink 或 copy、`bin:` 已挂；无 local-skill/code-review 仍通过 |
| B | 入口 2 | 退出码 `1`；`library/keel` 或 `bin` 报 `未安装 → keel install`；stderr 含 `doctor:` |
| C | 入口 3 | 退出码 `1`；`library/keel: ⚠ 占用且不是 keel`；那个外来 `SKILL.md` 内容未被改写 |

判定：输出原文存证，前后核对 state.json 和外来文件未变。#49 S3.A1–A3 使用这里的 A/B/C 入口，正常路径同时执行 install → doctor → uninstall；可选 locator 存在时 Doctor 也不得调用它或把任意 find 输出当合同可用。
