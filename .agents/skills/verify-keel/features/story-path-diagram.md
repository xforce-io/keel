# 有分支的用户交互路径要能在一张图里看完

关联 #38 S1–S3 与 [L1 v1](../../../../docs/design/38-branching-story-diagram/product.md) §8。这里核对合同原文和已安装设计入口，不把模型自称当通过。

## 用户入口（全部走）

1. 在当前候选上按手册用 scratch home install、doctor。从 scratch library 的 `keel-design/SKILL.md` 读窄规则，再经其中的相对引用打开 `references/design-contract.md` 的 Stories 节。记录候选 SHA。两处都必须能读到：有多个步骤或有分支的路径必须能在一张图里看完；可以是该 Story 自己的图，或它明确指出的已有图的一段；仅在总览出现名称不算覆盖；数据库、进程、IPC 图不能充当这张用户交互图；单步且无分支可说明原因后省略；纯技术可写 N/A；不要求每条 Story 各有一张图。不得出现「每条 Story 必须提供交互图」。
2. 在同一候选的 README「两层设计」读取同一条窄规则，核对 S2.A2。
3. 用 `git diff origin/main` 核对 S3.A2：已存在的 `docs/design/` 无改动；无新增 `bin/` 命令、schema 或检查脚本。本票 L1 记录 L2 skip。
4. scratch uninstall。运行 `python3 -m unittest tests.test_keel.ProductDesignContractTests.test_branching_user_story_path_fits_one_diagram` 作为 S1.A1–S2.A2 的辅助证据，不能代替安装入口摘录。

## 证据与判定

在 `.agents/verify-runs/38/` 保留候选 SHA、安装/doctor/卸载原文、两处安装摘录、README 摘录和 diff 统计。S1.A1–S3.A2 全部 pass 才汇总 S1–S3 pass。摘录缺失记 not_run，原文不符记 fail。
