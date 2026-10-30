# Issue #26 验收表

设计：`docs/design/26-evidence-preflight/product.md` v1，`technical.md` v1。L1：write。L2：write。确认来源：Issue #26 正文。

候选 SHA 是包含本文件的提交。完整 SHA 写在 PR 正文。证据目录 `.agents/verify-runs/26/` 不提交；可重复的命令证据是 `tests/test_keel_preflight.py`。

| ID | 结果 | 入口 | 证据 |
|---|---|---|---|
| S1.A1–S1.A9 | pass | `keel preflight` JSON 与文本 | `tests/test_keel_preflight.py`；`.agents/verify-runs/26/s1.txt` |
| S2.A1–S2.A5 | pass | 同一命令，含 `--previous` 与两个跨阶段样例 | `tests/test_keel_preflight.py`；`.agents/verify-runs/26/s2.txt` |
| S1 | pass | 上表全部必需子项 | 子项均为 pass |
| S2 | pass | 上表全部必需子项 | 子项均为 pass |

`python3 -m unittest tests.test_keel tests.test_keel_reflect_inspect tests.test_keel_check tests.test_keel_reverify tests.test_keel_preflight` 在该候选上通过。预检结构通过不是交付批准。
