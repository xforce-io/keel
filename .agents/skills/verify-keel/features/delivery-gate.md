# 交付证据校验（#20）

只在临时目录复制 `skills/keel-release/examples/check/` 的合成样例，使用当前 checkout 的 CLI 及 scratch 安装 CLI；不用生产证据。样例 candidate 为 40 个 a、Issue 20、Stories S1,S2,S3、必需 CI unit。

## S1 索引读取且只读

入口：`keel check <临时目录>/complete.json --issue 20 --candidate <样例SHA> --stories S1,S2,S3 --required-ci unit --json`。

应退出 0 且 PASS，逐项有 source；比较调用前后文件摘要一致。在非 Git 目录运行。修改临时证据文件后应退出 1，evidence 项 fail；恢复原文件后 PASS。CLI 不能运行记录内的命令。

## S2 阻断与恢复

逐个从原样例复制后执行实际 check，保存退出码和全文：

1. 删除/重复验收行，或把一行改 fail：BLOCKED。
2. 删除 verify，或将证据路径改为不存在文件：BLOCKED。
3. 删除 review、改 CHANGES_REQUESTED 或非法 source：BLOCKED。
4. human 改 required 或删除：BLOCKED，说明需人处理。
5. 删除设计 version 或 evidence：BLOCKED。
6. 必需 CI 删除、fail 或 pending：BLOCKED。
7. --candidate 换成 40 个 b：旧索引 BLOCKED。
8. 只保留 PASS 而移除 evidence：BLOCKED。
9. 完整样例：PASS。

恢复路径一：缺 review 的索引 BLOCKED → 补回原始引用 → PASS。恢复路径二：换候选后旧记录 BLOCKED → 按新候选更新所有适用字段并提供对应原始证据 → PASS。此处是合成样例合同验证，不宣称驱动过外部 Reviewer 或平台。

## S3 分类、帮助、复制安装

分别执行 `keel check --help`、文本和 JSON 入口，结论相同。user_path=cli/gui 必须 pass；改 skip 即 BLOCKED。user_path=none、status=skip、reason=无用户路径且证据说明适用性时 PASS，输出保留 skip 理由。

使用 scratch `install --copy` 后的 CLI 再跑完整样例并运行 doctor；应 PASS，证明新增命令不依赖漏装的模块。Cleanup 只卸本次 scratch。

同时读取 scratch 安装的 `keel/SKILL.md`：end-to-end 必经 release，阅读/计划/check PASS 不等于执行完成；受阻报告已完成与未完成环节、原因和下一步；route/design/dev 保持合法停点。这是已安装合同验证，不声称已驱动任意下游 agent。

## Evidence

`.agents/verify-runs/20/` 保存当前候选 SHA、doctor 输出、每个入口的命令/退出码/结果及 S1/S2/S3 完成表。原始日志不提交。不要把合成证据描述成真实任务的设计批准、审查或 CI。
