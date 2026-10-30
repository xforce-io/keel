# Issue #38 验收表

设计：[L1 v1](product.md)。L1：write。L2：skip。确认来源：本会话对窄口径的确认。

候选 SHA 是包含本文件的提交。完整 SHA 写在 PR 正文。安装摘录在 `.agents/verify-runs/38/`，不提交。可重复的合同断言是 `tests/test_keel.py` 的 `test_branching_user_story_path_fits_one_diagram`。

| ID | 结果 | 入口 | 证据 |
|---|---|---|---|
| S1.A1 | pass | 设计合同 Stories 节 | 单元测试直接读取合同 |
| S1.A2 | pass | 同一节 | 单元测试直接读取合同 |
| S2.A1 | pass | 同一节 | 单元测试直接读取合同 |
| S2.A2 | pass | 合同、keel-design 执行说明、README「两层设计」 | 单元测试直接读取三处 |
| S3.A1 | pass | scratch install 后的 keel-design | `.agents/verify-runs/38/s3.txt` |
| S3.A2 | pass | `git diff origin/main` | `.agents/verify-runs/38/diff.txt` |
| S1 | pass | 上表 S1.A1–A2 | 子项均为 pass |
| S2 | pass | 上表 S2.A1–A2 | 子项均为 pass |
| S3 | pass | 上表 S3.A1–A2 | 子项均为 pass |

`python3 -m unittest tests.test_keel tests.test_keel_reflect_inspect` 在该候选上通过。S3.A1 的安装摘录不能用单元测试代替。
