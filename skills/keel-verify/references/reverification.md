# 复验准备合同 v1

`keel reverify RECORD --task TASK --candidate SHA --baseline SHA --items IDS --prechecks IDS --root DIR (--initial | --previous FILE) [--changed-path PATH] [--require-agent ID] [--json]`

目的：在昂贵运行前核对声明、可读文件和累计预算。返回 READY/0 或 BLOCKED/1，语法错误 2；READY 不代表执行、产品验收、审查或发布 PASS。输入只读，不运行其中的命令、不调用模型、不连接平台。完整可运行样例在 `../examples/reverify/`，不得把合成样例作为真实交付证据。

## 调用方责任

task、候选、baseline、必需验收项、前置检查和 changed-path 从原任务/产品基线/Git 变更独立取得，不能从待检计划反推；依赖列表要包含真正影响本项的代码、配置、输入、Skill 和共享模块。`--require-agent` 逐条列出产品基线要求本候选真实 Agent 实跑的项目。语义完整性由调用方及完整独立审查核对，工具不能发现所有漏报依赖，也不认证作者和授权身份。

已有记录必须提供原始上一份 `--previous`，不能复制改写历史后再冒充 previous。首次使用 --initial 且 history 为空；工具不能识别用户刻意隐瞒的其他任务记录。任务标识、文件名和 SHA 不是认证来源；不允许靠换目录/新 SHA/改 task_id 清零。previous 路径相对于当前工作目录，其内部证据在后续记录中仍相对于各自 record 所在目录，移动记录时须保留原证据可核对位置。

## JSON 字段

- `schema_version: 1`；`task_id`、`candidate_sha`、`baseline_sha` 必须与参数一致，SHA 为完整40/64位小写十六进制；拒绝重复键、非法非有限数字、非对象或超过1 MiB记录。
- `items`：按 --items 顺序每项一条；`id`、`method: deterministic|user-path|agent`、`decision: rerun|retain`、非空 `reason`、非空 `dependencies`。
- 每个 dependency：`path` 为 --root 下的相对文件名，禁止 `..`/绝对路径/跳出 root；`before`/`after` 为原/当前 SHA-256 或 null（新增/删除），两者不能都空。当前实际文件摘要须等于 after；retain 的 before 应为该原始证据所依赖的版本摘要，不强迫历史依据改成最近一次候选。同一项目依赖名不重复。
- `old_evidence` 可选，含原始运行的完整 `candidate_sha`（可早于 baseline，不得改写成当前版本）及 `evidence: {path,sha256}`；引用文件须可读且摘要一致。retain 只在所有依赖一致、有原始证据且非 --require-agent 时允许；原始证据不变 SHA，输出 executed=false。agent 无影响且已有依据、无显式必需要求时不能无理由 rerun；有影响/无原依据/明确必需要求则安排 rerun。其他方法可重跑低成本检查及当前用户路径。
- 每个 --changed-path 须被某项依赖覆盖，或在 `out_of_scope: {path: reason}` 逐项说明无关理由，两者不重叠。该声明仍须审查，不是自动语义分析。
- `prechecks` 与 --prechecks 编号、顺序一致；每项 `{id,status:"pass",candidate_sha,evidence}`，且为当前候选。调用方实际执行已确认的生产者/消费者、状态与资源等确定性检查，失败先修，不能伪造 pass；工具仅核对声明及原始输出摘要，不重执行测试。
- `history` 为按发生顺序的运行记录；每条唯一 `id`、完整 `candidate_sha`、`kind: check|cli|agent|review`、`metrics`；review 另含 `verdict: PASS|CHANGES_REQUESTED|BLOCKED`，非 PASS 须有非空 `failure_classes` 列表。当前 history 须完整保留 previous.history 前缀。
- `next_kind` 为下一批运行类型；`budget: {limits,planned}`。planned 为预计 metrics，时间必须大于0；limits 至少含 elapsed_seconds、model_calls，可另外约束其他指标，使用累计实际值+本次预计值比较。未知受限指标不能放行，时间/调用预算可作为未设 token 限额时的替代。达到边界后不能静默启动下一批；工具不负责运行中自动计量或终止，调用方要监测实际值、取消或收口。
- previous 的 budget.limits 被提高或移除时，须提供 `budget_authorization: {actor,evidence}`。未提高仍沿用已有授权，不逐次问人；tool 只检查证据引用，不认证其内容真是用户批准。
- 默认允许同一任务三轮 review。`extensions` 为按顺序扩展：`{after_round,additional_reviews,actor,evidence}`，after_round 必须等于当时可用边界且该轮已实际发生。前三轮后追加一轮即 after_round=3/additional_reviews=1；第四轮后再次追加须新的 after_round=4 授权。不得重复利用同一扩额。
- 最近一轮非 PASS 后安排 agent/review，`retry` 须含非空 root_cause、strategy_change、exit_condition。追加授权不覆盖失败审查/发布门禁；根因及策略变化的真实性由调用方和 Reviewer 核对。

metrics 每次必须显式列出：elapsed_seconds（非负有限数，其余均为非负整数）、model_calls、cli_calls、atomic_reads、upstream_requests、input_tokens、cached_input_tokens、output_tokens。agent/review 一条记录代表一次模型运行，model_calls=1；check/cli 为0。三个 token 字段允许 null，不能用 CLI 次数冒充原子读取或上游请求；模型运行 usage 三字段全零按未知处理。cached≤input（都已知时），input 包含缓存部分，不把它们再次相加当费用。

累计值若任一记录对应字段未知则输出 null；可从 history 查阅已知分项。没有发生过的运行总数为0，不能把计量缺失解释为0。各运行 elapsed_seconds 是执行耗时累计，不能误称有并行时的端到端墙钟时间；不提供定价或账单推算。

## 复验与门禁

开发先补同类边界的确定性回归，再评估必要 Agent 验收；展示改变不自动重分析业务，算法/数据/Skill决策改变则重验相关必需项。最终候选的所有适用产品验收仍完整覆盖，保留依据的适用性与当前核对事实单独记录，不能直接将旧 verify 表换 SHA。正式 review 继续审完整合并差异，发布仍运行独立 `keel check`。
