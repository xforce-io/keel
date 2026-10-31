# 复验范围与成本（#31）

标准：`docs/design/31-verification-cost-control.md` Draft v1，S1.A1–S4.A1。全部采用隔离目录合成文件、当前实际 CLI，既有 Scratch Launch/Doctor/Cleanup 不变。无平台业务调用，不读真实家目录。

入口：checkout 与 scratch 复制安装 `keel reverify --help`、文本/JSON、`--initial` 和 `--previous`。用 `skills/keel-verify/examples/reverify/make_example.py` 在临时目录生成输入及依赖；样例不是业务验收或真实批准。

- S1.A1：展示/算法/资源三类，核对 actions 和原始 SHA；依赖变化却 retain、无影响重复 agent、明确 --require-agent 却 retain、当前摘要不符和漏掉 changed-path 都 BLOCKED。损坏链接（含中间路径）不可当删除，有效内部普通文件链接正常核对。修正后 READY，文件不被改写。算法实际受影响的样例改为 rerun，不跳过真实必需项。
- S2.A1：运行 `tests.test_keel_reverify.ReverifyTests.test_minimal_semantic_failure_examples` 的三类契约注入，经实际 CLI 前置失败先 BLOCKED，修正后 READY；记录没有执行任何模型调用。这是通用样例，不是医院或实际 Agent 行为验收。
- S3.A1：预算内 READY；已有消耗+下一批超界 BLOCKED；模型 usage 全0/null输出未知，设 token 限额时未知不能放行；续跑历史累计不丢失、CLI/原子/上游三项独立。前置检查或依赖失败仍展示合法累计/限额/计划/预计；有限数相加溢出 BLOCKED 且标准 JSON 以 null 标明。提高限额缺授权 BLOCKED，有可读授权引用方可继续；未调整预算不额外索要许可。
- #40 S1：从实际 CLI 使用历史和计划中的未知原子读取、上游请求；未设对应限额时 READY，累计和预计值均为 null；分别设置对应限额时 BLOCKED，未知不补零。
- #40 S2：首次用 `--adopt-history` 接入一轮带原始证据的审查，再用 `--previous` 续跑；空历史、缺失或错误审查证据、改写历史均 BLOCKED；三轮无扩额 BLOCKED，有效追加授权后 READY，原始 `--initial` 仍拒绝非空历史。
- S4.A1：三轮失败无追加授权 BLOCKED；暂停/换候选后 previous 完整保留并核对 retry；追加一轮允许第四轮，第四轮用尽再阻断。删除/改写历史、改 task_id、新文件名不解除约束。继承授权按 previous 目录、新授权按当前目录核对；连续移动须保留上一目录证据，同名当前文件不能替代。

复制安装后重复帮助及一条 READY/BLOCKED，doctor 通过；读取安装的 dev/verify/review 合同，确认增量依据、先确定性检查、预算和累计轮次都有引用，旧 `keel check` 门禁不变。

原始输入/输出、候选、环境、耗时及完成表放 `.agents/verify-runs/31/`。全部必需行实际执行后才能汇总 pass；不要求另起独立业务 Agent 做一次相同样例，正式代码审查仍独立。
