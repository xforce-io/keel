# keel

有门禁的研发交付：**keel 只路由**，环节是独立 skill。把单个任务从 Issue 推到设计、实现、独立审查、CI 与合入。何时问人见 [`when-to-ask.md`](skills/keel/references/when-to-ask.md)，何时写设计见 [`when-to-write.md`](skills/keel/references/when-to-write.md)。L1 是产品设计，L2 是技术设计，不再各分概要与详细。

它不是第二套 pstack，也不是常驻 mode。名词以 [docs/glossary.md](docs/glossary.md) 为准。

| skill | 职责 |
|---|---|
| `keel` | 选模式、选下一合法环节、完整读取该环节 skill |
| `keel-issue` | 定位仓库、Issue、验收 |
| `keel-how` | 设计/实现前说明现有子系统怎么工作 |
| `keel-design` | 按需写 L1 产品设计与 L2 技术设计 |
| `keel-dev` | 实现与 `S1…Sn` 验收表 |
| `keel-verify` | 按应用仓库 `.agents/skills/verify-*` 驾驶手册与功能地图证明 S1…Sn 及适用 L1.8 验收 |
| `keel-verify-maintain` | 保养功能地图（不在交付链上；全图/回归/维护循环时才跑） |
| `keel-review` | 独立审查 |
| `keel-release` | CI、PR/MR、合入；有 runbook 则部署 |
| `keel-reflect` | 任务后复盘（不在交付链上；你说了才跑） |
| `keel-ticket` | 建 Issue 并切到 `feat/*` 或 `bugfix/*`（不在交付链上；你说了才跑） |
| `keel-start` | 进仓看待办与残留分支（不在交付链上；你说了才跑） |
| `cat-mode` | 风格（不在交付链上；你说了才跑；不启动 `/keel` 状态机） |
| `keel-sync` | 把 Grok Bot 共享电脑上的 keel 技能更新到 `/workspace/keel`（不在交付链上；你说了才跑） |

也可单独调用 `/keel-design` 等。问不问、写不写由 keel 的两份合同控制；设计章节与验收规则见 [设计合同](skills/keel-design/references/design-contract.md)；项目 `AGENTS.md` 管本地路径/章节映射、Issue 骨架、分支与托管平台，旧的 L1=概要/L2=详细定义须明确迁移。

## 两层设计

L1 回答用户要完成什么、从哪里进入、如何操作、成功与失败各是什么；包含产品交互总览、完整 Stories、规则及第 8 节可执行验收。L2 引用确定的产品基线，说明架构、数据/状态、接口、运行保障与验证机制，不能自行缩减 L1。默认分别放在 `docs/design/{issue}-{slug}/product.md` 与 `technical.md`，Issue 只放摘要和链接。

仍只有一个 `keel-design` 环节。产品行为有变化时先明确 L1 及适用确认，再做 L2 和实现；已有用户决定直接复用，不重复索取确认。简单交互改动可仅 L1；产品行为不变的内部技术改造可仅 L2；小修可复用已有契约。每份文档分别判断 write/reuse/skip，不为流程凑文档。

Issue S 是交付汇总，L1.8 用稳定验收 ID 细化前置、真实入口、可判定结果、禁止结果与证据要求。开发、驾驶验证、独立审查和发布都对照同一基线；标准与执行结果分开记录。`keel check` v1 校验格式和文件摘要，尚不自动核对 L1.8 完整性。

## 安装

前置条件：

- Python ≥ 3.11。
- `local-skill` 在 PATH，且 `local-skill find code-review` 能找到审查合同 skill。`keel-review` 靠它把 `code-review` 交给 Reviewer；找不到该环节直接 `BLOCKED`。`code-review` 不随 keel 分发。`keel doctor` 会检查这两项。

克隆后把全部 skill 挂到本机：

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
6. 在 `~/.config/keel/state.json` 记下仓库路径和 keel 自己复制出去的文件

不写入 `~/.agents/skills/`（应用仓库内的 `.agents/skills/verify-*` 是 `keel-verify` 读的驾驶手册位置，与安装无关）。只跳过、只移除非 keel 的东西：指向任意 keel checkout 的符号链接、悬空链接、以及 `state.json` 里记录的副本才算 keel 的。任一项被跳过或失败，`install` 退出码为 1。

可选：

```bash
./bin/keel install --copy      # 不能建符号链接时复制；再次 install --copy 会整体刷新副本
./bin/keel install --plugin    # 再执行 grok plugin install . --trust
./bin/keel doctor              # 只读检查；有缺失、占用或找不到 code-review 则退出码 1
./bin/keel uninstall           # 只拆 keel 自己挂上的链接或副本
```

已 clone、且 `~/.local/bin` 在 PATH 时，之后用 `keel install` / `keel doctor` 即可；`--copy` 装出的 CLI 通过 `state.json` 找回仓库，仓库搬走后会直接报错，重新在新位置跑 `./bin/keel install` 或设 `KEEL_ROOT`。

### 更新

两套安装不要混用：

| 目标 | 怎么更新 |
|---|---|
| Mac 上的 Grok / Claude / Cursor / Codex / Pi | 在 checkout `git pull`。已有 skill 改正文即生效（符号链接）。**新增** `skills/<name>/SKILL.md` 才再跑 `keel install`，然后 `keel doctor`。 |
| Grok Bot 云端 bot | 副本在 `/workspace/keel`，`/` 菜单是登记快照。`git pull` **不够**。对任意 bot 打 `/keel-sync` 或说「keel 更新了」。不要在云端跑 `keel install` 冒充这次同步。 |

## 用法

在会话里说：

```text
用 keel 处理 Issue 12
keel 设计这个 Issue
端到端完成
/keel-review
keel-reflect
```

或 `/keel`。交付时 Agent 应读 `skills/keel/SKILL.md`，再完整读取它选出的环节 skill。复盘说 `keel-reflect` / `reflection`，不在端到端里默认跑。

模式：`route` · `design` · `dev` · `end-to-end`。

## 交付证据校验

`keel check` 是平台中立的只读工具，不调用 GitHub/GitLab API，不运行 CI，也不执行合入。输入合同、完整示例及调用方责任见 [交付校验](skills/keel-release/references/check.md)。

```bash
keel check /path/to/delivery.json --issue 20 --candidate "$candidate_sha" \
  --stories S1,S2,S3 --required-ci unit --json
```

退出码 0 表示输入通过，1 表示阻断，命令行语法错误为 2。是否接入 CI 由项目决定；release 环节在实际合入前调用校验。证据来源真实性、当前候选和必需项清单由调用方确认。

## 开发

```bash
python3 -m unittest tests.test_keel tests.test_keel_reflect_inspect tests.test_keel_check
```
