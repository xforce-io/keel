# 送审预检合同 v1

`keel preflight RECORD --issue N --candidate SHA --required REQUIRED [--previous PREVIOUS] [--json]`

只读取两份 JSON 和其中引用的证据文件。不写文件，不执行声明里的命令，不访问网络或 Git。结构通过不是交付批准，不代替独立审查或 `keel check`。

## 调用方责任

从适用产品基线或沿用契约独立确认必需验收编号、分支或阶段收尾、入口，以及需要核对的对象、版本、导出摘要、正式决定请求和修订。这些期望放在 `--required`，不能从 `RECORD` 反推。证据是否真的来自该任务、决定是否有效、版本适用性是否正确，仍由调用方、驾驶验证和独立审查判断。

## 输入

两份文件都要 `schema_version: 1`、与参数一致的正整数 `issue`、与 `--candidate` 一致的 40 或 64 位小写十六进制 `candidate_sha`。重复 JSON 键、非法类型、超过 1 MiB 均阻断。

`--required` 另有非空 `task_id` 和非空 `items`。每项含唯一 `id`、`branches`、`entries`。名称在各自清单内不可重复，顺序不表示层级。可以额外声明 `object`、`version`、`export_sha256`、`decision_id`、`revision`；声明了就必须是非空字符串，导出摘要还必须是 64 位小写十六进制。没声明的字段不检查。

`RECORD` 的 `items` 可为空。每项含唯一 `id`、非空 `task_id`、`branches`、`entries`，以及 `evidence: {path, sha256}`。相对路径以该文件所在目录为准。文件必须存在、是普通文件，且 SHA-256 与声明一致。

分支和入口按集合比较。证据多写的编号、分支或入口不构成失败。

## 输出

退出码 0 为 `PASS`，1 为 `BLOCKED`，命令行语法错误为 2。`ready_for_review` 只在 0 时为 true。`product_acceptance` 恒为 false。

文本先写状态，再写「本次可以交接」或「本次不能交接」。通过时另有一行说明只核对了编号、分支、入口和声明关联。随后每条检查一行，包含 `acceptance_id`、`field`、`branch`、`class`、`status` 和原因。JSON 使用同一批检查。

`binding` 由当前候选、两份输入文件的字节，以及每条已核对证据的声明摘要和实际文件摘要决定。`--previous` 接收上一次输出的 JSON。那次不是 `PASS` 时，本次按当前输入重新判定。那次是 `PASS` 但候选或 `binding` 已变时，本次失败并点名变化的关联字段，旧通过不能交接。绑定相同则旧通过仍对应当前输入。

工具不保存结果。调用方自己留存需要交接的那一次输出。
