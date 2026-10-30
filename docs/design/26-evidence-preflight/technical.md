# 送审前证据预检：技术设计

版本：v1。状态：Draft。L1：write，[product.md](product.md) v1。L2：write。确认来源与 L1 相同：Issue #26 正文。

## 1. 设计依据与技术目标

落实 L1 的 S1.A1–S1.A9 与 S2.A1–S2.A5。新增一条只读 CLI。不扩展 `keel check` schema v1，不新增交付阶段，不保存续跑状态。

## 2. 现状与改动范围

how 依据：

- `bin/keel` 的 `buildParser` 在本变更前提供 `install`、`uninstall`、`doctor`、`check`、`reverify`。`commandCheck` 只核对索引字段和证据文件摘要。
- `skills/keel-release/references/check.md` 写明校验器不解析 L1.8，不自动检查覆盖率、设计版本关系或确认语义。
- `skills/keel-verify/scripts/reverify.py` 的 precheck 是调用方声明的确定性检查项，不是验收分支。
- `skills/keel-verify/SKILL.md` 的完成条件要求必需项 pass 才交给审查，但没有可执行的结构预检。
- `skills/keel-review/SKILL.md` 送审前要求映射材料，不要求一份绑定当前候选的预检结果。

改动：`skills/keel-verify/scripts/preflight.py` 做比较；`bin/keel` 增加 `preflight` 子命令并 `runpy` 调用该脚本，沿用 `commandReverify` 的装载方式。交接句子写在 `keel-verify` 与 `keel-review`。`commandCheck` 的字段规则不改。

## 3. 总体架构与关键路径

调用方持有两份 JSON 和候选 SHA。CLI 读取它们和证据文件，在内存里比较，打印同一份结果的文本或 JSON。失败路径把每一条缺口放进 `checks`。没有进程间队列，没有写入。

选择：逻辑放在 verify 脚本而不是 `commandCheck`，避免发布门 schema 承担送审前的编号语义。代价是两个命令都要会核对文件摘要；预检不调用 check。

## 4. 数据与状态契约

两份输入的 `schema_version` 都是整数 1，`issue` 与 `--issue` 相同，`candidate_sha` 与 `--candidate` 相同。候选是 40 或 64 位小写十六进制。

必需清单还有非空 `task_id` 和非空 `items`。每项有唯一 `id`、`branches`、`entries`。调用方若声明 `object`、`version`、`export_sha256`、`decision_id`、`revision`，证据行必须逐字相同；未声明的字段不查。`export_sha256` 为 64 位小写十六进制。

证据行有唯一 `id`、`task_id`、`branches`、`entries` 和 `evidence.path` / `evidence.sha256`。文件必须存在且 SHA-256 等于声明。分支和入口按集合比较，多出来的名称不失败。证据里多出来的编号不失败。

输出绑定 `binding` 覆盖候选、两份 JSON 的字节、以及每条已见证据的声明摘要和实际文件摘要。工具不把结果写入磁盘。`--previous` 只读取调用方保存的上一次 JSON 输出。

## 5. 接口与协作契约

```text
keel preflight RECORD --issue N --candidate SHA --required REQUIRED [--previous PREVIOUS] [--json]
```

退出码：0 结构通过；1 阻断或输入不可核对；2 命令行语法错误。

JSON 与文本来自同一次 `checks`。文本每行带 `acceptance_id`、`field`、`branch`、`class`、`status`。`status` 为 `PASS` 或 `BLOCKED`。`ready_for_review` 仅在没有任何失败项时为 true。`product_acceptance` 恒为 false。通过时文本写「本次可以交接」和「结构通过，只核对编号、分支、入口和声明关联」。失败时写「本次不能交接」。

`class`：`missing-id`、`missing-branch`、`missing-entry`、`cross-task`、`stale-association`、`decision-mismatch`、`evidence-file`、`consistent`、`stale-pass`、`previous`、`input`。

`--previous` 指向的输出若 `status` 不是 `PASS`，不把那次失败当成可沿用的通过，本次仍按当前输入判定。若那次是 `PASS` 但候选或 `binding` 不同，本次追加 `stale-pass` 并阻断，即使当前声明本身已经一致。相同绑定则记一次 `previous` 通过。

重复 JSON 键、未知 schema、空必需清单、非法 SHA 归入 `input`，退出码 1。声明中的命令字符串不执行。

## 6. 运行与保障机制

只读打开文件。单文件 JSON 上限 1 MiB。不访问网络，不调用 Git，不认证人的身份，不解析证据正文。摘要相同只说明字节没变。

## 7. 迁移、发布与回滚

旧的 `keel check` 索引继续按 schema v1 使用。没有数据迁移。回滚是去掉 `preflight` 子命令和交接句子；已有 check 行为保持。无部署阶段。

## 8. 测试与验证

功能文件：`.agents/skills/verify-keel/features/evidence-preflight.md`。

| 验收 | 机制 |
|---|---|
| S1.A1–S1.A9、S2.A1–S2.A5 | `python3 -m unittest tests.test_keel_preflight` 子进程调用 `bin/keel preflight` |
| 安装后的同一入口 | 该测试里的 `--copy` 安装再跑完整样例和 `--help` |
| 既有门禁未变 | `tests.test_keel_check` 与 `tests.test_keel` |

驾驶证据放在 `.agents/verify-runs/26/`，不提交。

## 9. 技术风险与开放问题

调用方可以把错误清单和配套证据一起造出来，工具发现不了。这是 Issue 已经写明的边界，不在本契约里补自然语言判断。

无需要退回 L1 的技术假设。
