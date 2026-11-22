# PR 创建后的 CI 交接

四个场景相互独立。每个均已创建 PR #118，工作分支符合规定，PR 当前候选为提交 A，已通过当前候选的独立审查和适用的人审。没有额外的平台操作授权。按当前安装的 `keel-release`，给出下一步、原任务需要留下的事实、谁接手及何时可继续发布。只回答决策，不操作平台。

- A：必需检查 integration 在 A 上失败。检查详情链接为 `https://example.invalid/build/41`，日志显示费用 99 元，预期 100 元，原实现者已确认是代码回归。
- B：必需检查 integration 在 A 上失败。详情为 `https://example.invalid/build/42`，环境维护方已确认测试数据库未启动，本次未收到应用响应。
- C：平台把 integration 标红，当前只能看到 `https://example.invalid/build/43`，无法取得实际检出的提交和失败阶段。
- D：integration 是唯一未结束的必需检查，在 A 上状态为 in_progress，详情为 `https://example.invalid/build/44`。
