# keel

一条有门禁的研发交付 skill。把单个任务从 Issue 推到设计批准、实现、独立审查、CI 与合入。

它不是第二套 pstack，也不是常驻 mode。`kairo` 管调研，`reflection` 管事后收口，`keel` 只管这条交付状态机。名词以 [docs/glossary.md](docs/glossary.md) 为准。

## 安装

需要 Python ≥ 3.11。克隆后把 skill 挂到本机：

```bash
git clone https://github.com/xforce-io/keel.git
cd keel
./bin/keel install
```

`install` 会：

1. 把 `skills/keel` 链到 `~/.local/share/agent-skills/library/keel`（`local-skill find` 用这份）
2. 对已存在的 Grok / Claude / Cursor / Codex / Pi 家目录挂同名 skill
3. 把 CLI 链到 `~/.local/bin/keel`
4. 若 PATH 里有 `local-skill`，执行 `refresh`

不写入 `~/.agents/skills/`。常驻 skill 仍只应是 `reflection` 与 `kairo`。

可选：

```bash
./bin/keel install --copy      # 不能建符号链接时复制
./bin/keel install --plugin    # 再执行 grok plugin install . --trust
./bin/keel doctor              # 只读检查
./bin/keel uninstall           # 只拆 keel 自己挂上的链接或副本
```

已 clone、且 `~/.local/bin` 在 PATH 时，之后用 `keel install` / `keel doctor` 即可。

## 用法

在会话里说：

```text
用 keel 处理 Issue 12
keel 设计这个 Issue
端到端完成
```

或 `/keel`。Agent 应读 `skills/keel/SKILL.md`，再只读当前阶段的 `references/`。

模式：`route` · `design` · `dev` · `end-to-end`。硬门禁包括：禁止自批设计、合入前独立审查、`S1…Sn` 验收表。项目 `AGENTS.md` 仍是宪法。

## 开发

```bash
python3 -m unittest tests.test_keel
```
