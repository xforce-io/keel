# 交付校验合同 v1

`keel check RECORD --issue N --candidate SHA --stories S1,S2 --required-ci NAME --json`

`--required-ci` 可重复；确认无必需项时不传。`--json` 可省略以输出文本。只读取 JSON 索引及本地证据文件；不调用网络、Git 或平台命令，不执行索引中的命令，不写文件。工具仍可在没有 Git 仓库的目录运行。

## 调用方责任

先从任务确认 Issue 和验收清单、从当前仓库确认完整候选 SHA、从项目/CI 环境取得完整必需检查清单；不能从待检索引复制这些期望值。证据采集、审查独立性、真实人工批准、设计适用性、skip 合法性和当前 CI 状态由调用方核对。不得把示例产物当生产证据。

索引是一份当前状态文件，位置由调用方提供；建议放在项目已有、被 Git 忽略的验证产物目录中，不提交进候选分支。更新时保留原始证据，不需要数据库或附加事件日志。不同候选的产物不要覆盖。更新索引用临时文件替换，避免读取半写文件。

## 输入

完整可运行的合成样例：[complete.json](../examples/check/complete.json)。样例只演示格式，不证明任何真实交付。

- 顶层：`schema_version: 1`、正整数 `issue`、完整小写十六进制 `candidate_sha`（40 或 64 位）。未知版本、重复 JSON 字段或非法类型均阻断。
- `design`：`status: pass|skip`、`evidence`。pass 时需非空 `version` 标识已获批设计版本；skip 时需非空 `reason`。
- `stories`：按调用方 `--stories` 顺序排列的数组，每行含 `id`、`status: pass|skip`、`candidate_sha`、`evidence`。skip 需非空 `reason`，证据指向允许该 skip 的依据。
- `verify`：`user_path: cli|gui|none`、`status`、`candidate_sha`、`evidence`。cli/gui 只能 pass；none 可 pass 或有理由的 skip，skip 证据是“无用户路径”的依据，不要求驾驶产物。
- `review`：`status: PASS`、`human: optional`、非空 `reviewer_host`/`reviewer_model`、`source: user|bind-file|host-config|complementary`、`candidate_sha`、`evidence`。其它状态、缺字段、human required 都阻断。不得因校验器只检查字段就代填 Reviewer 的字段。
- `ci`：`status`、`candidate_sha`、`evidence`、`checks`。每个 check 含非空唯一 `name`、`status: pass`、`candidate_sha`、`evidence`；必须包含所有 `--required-ci` 项，已提供的额外项同样必须 pass。无 CI 时仅允许 `status: skip`、空 checks、非空 reason 和说明无 CI 的证据；有必需项不能 skip。
- 所有 `evidence`：`{"path": "原始文件路径", "sha256": "64 位小写 SHA-256"}`。相对路径以索引目录为准；绝对路径也可。文件须存在、可读且摘要匹配。目录、缺失文件、摘要不匹配不通过。

所有适用候选字段均须与调用方传入 SHA 相同。设计版本独立于候选 SHA。文件摘要只能核对内容未变，不能认证作者、证明结论正确或识别一份被同步伪造的文件。工具不解析原始证据的自然语言；来源语义与索引是否一致须由调用方核对。仅自填 PASS 而没有有效文件引用不能通过，但补一份无意义文件并不能成为真实交付。

## 输出与恢复

退出码：0 PASS；1 BLOCKED（含输入内容错误与不可读文件）；2 argparse 命令行语法错误。JSON 为 `schema_version`、`status`、`issue`、`candidate_sha`、`checks`。checks 每项包含 `id`、`status: pass|fail|skip`、`reason`、`source`（索引路径与字段标识）、`next_stage`、`resume_when`。成功项后两者为 null。文本和 JSON 使用相同判定。

失败可同时列出多个原因。依赖环节按 design → dev → verify → review → release 的现有顺序补齐，人工/权限不足时等待真实责任方；不自动重试。代码变化后重新取得 SHA、验收、验证与审查证据再查；设计版本与 CI 情况由调用方重新核对。通过结果不缓存、不作为长期合入凭证。

PASS 不能阻止调用方绕过工具，也不能锁住校验后的平台 HEAD。项目需要硬性门禁时，自行接入 CI 或平台保护；本功能不负责集成。
