# keel

有门禁的研发交付：**keel 只路由**，环节是独立 skill。把单个任务从 Issue 推到设计批准、实现、独立审查、CI 与合入。

它不是第二套 pstack，也不是常驻 mode。名词以 [docs/glossary.md](docs/glossary.md) 为准。

| skill | 职责 |
|---|---|
| `keel` | 选模式、选下一合法环节、完整读取该环节 skill |
| `keel-issue` | 定位仓库、Issue、验收 |
| `keel-how` | 设计/实现前说明现有子系统怎么工作 |
| `keel-design` | 设计并停在人工批准 |
| `keel-dev` | 实现与 `S1…Sn` 验收表 |
| `keel-verify` | 按应用仓库 `.grok/skills/verify-*` 驾驶手册与功能地图证明 S1 |
| `keel-review` | 独立审查 |
| `keel-release` | CI、PR/MR、合入；有 runbook 则部署 |

也可单独调用 `/keel-design` 等。项目 `AGENTS.md` 仍是宪法。

## 安装

需要 Python ≥ 3.11。克隆后把全部 skill 挂到本机：

```bash
git clone https://github.com/xforce-io/keel.git
cd keel
./bin/keel install
```

`install` 会：

1. 把 `skills/*` 链到 `~/.local/share/agent-skills/library/<name>`（`local-skill find` 用这些）
2. 对已存在的 Grok / Claude / Cursor / Codex / Pi 家目录挂同名 skill
3. 若存在 `~/.grok`，把 `agents/reviewer.md` 挂到 `~/.grok/agents/reviewer.md`（plan 权限；不覆盖已有本机角色，不写死模型 slug）
4. 把 CLI 链到 `~/.local/bin/keel`
5. 若 PATH 里有 `local-skill`，执行 `refresh`

不写入 `~/.agents/skills/`。

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
/keel-review
```

或 `/keel`。Agent 应读 `skills/keel/SKILL.md`，再完整读取它选出的环节 skill。

模式：`route` · `design` · `dev` · `end-to-end`。

## 开发

```bash
python3 -m unittest tests.test_keel
```
