# 送审前证据预检（#26）

只在临时目录构造合成清单和证据文件，使用当前 checkout 的 `bin/keel`，以及 scratch `--copy` 安装出来的 CLI。不使用生产证据，不把结构通过写成交付批准。

## S1 八类结果

入口：`keel preflight <record> --issue 26 --candidate <SHA> --required <required> [--json]`。

同一份输入分别走 JSON 和文本。结论的状态、验收编号、字段、分支和 class 一致。调用前后文件字节不变。

1. 清单有的编号在证据里没有：失败并点名该编号。
2. 编号在，但缺一个分支或阶段收尾：失败并点名该分支。
3. 缺要求的入口：失败并点名入口字段。
4. 证据任务标识与清单不一致：失败并点名 `task_id`。
5. 对象、版本或导出摘要与清单不一致：失败并点名该关联字段。
6. 正式决定请求或修订不一致：失败并点名该关联字段。
7. 证据文件缺失或摘要不符：失败并点名 `evidence.sha256`。
8. 完整一致：退出码 0，连续两次输出相同，声明中的命令不被执行，输出不含「产品验收 PASS」。

另用一组 `S1.A1` / `S4.A6` 和一组 `contract.login` / `contract.export`。两组都按所给编号判定。

## S2 交接

1. 有缺口：`ready_for_review` 为 false，文本是「本次不能交接」。
2. 同一候选补齐后重跑：`ready_for_review` 为 true，文本是「本次可以交接」。
3. 保存通过输出后改变候选或证据文件，再带 `--previous`：失败并点名变化的关联字段。去掉 `--previous` 的新运行可以通过，且 `binding` 与旧输出不同。

跨阶段样例一：清单要求 `independent-failure`、`rework`、`new-inspection`、`human-accept-close`，证据只有新版检验。失败点名 `human-accept-close`；四段齐了才通过。

跨阶段样例二：操作记录的 `version` 仍是旧导出。失败点名 `version`；改为清单上的当前版本后通过。

## 帮助与复制安装

`keel preflight --help` 退出码 0，并写出 `--required` 与 `--previous`。

scratch `install --copy` 后的 CLI 能跑通完整样例。Cleanup 只卸本次 scratch。

## Evidence

`.agents/verify-runs/26/` 保存命令、退出码和原文。原始日志不提交。合成样例不代表某次真实审查已经通过。
