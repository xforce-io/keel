# L2：审查依赖改造

版本：v1；状态：Draft；依据 [L1 v1](product.md) 与 [Issue #49](https://github.com/xforce-io/keel/issues/49)。

## 1. 设计依据与技术目标

落实 S1.A1–S3.A3。Doctor 的退出判定不再取决于外部审查定位命令；不新增接口或配置。

## 2. 现状与改动范围

bin/keel 的 reviewContractStatus 调用 local-skill，只检查返回码和非空输出；commandDoctor 将结果计入失败。原测试 find 返回虚构路径。keel-review 开头硬性要求该命令，角色和文档仍引用外部合同。以上是本次 how 的源码依据，原环境 Doctor 退出 1 已留存在 #48 验证目录。

## 3. 总体架构与关键路径

删除 reviewContractStatus、其常量和 Doctor 调用。沿用已有挂载核对和退出码；最小审查准则只在 keel-review 中维护，角色引用它，路由不复制环节规则。驾驶手册与所有功能页统一使用 KEEL_VERIFY_HOME/KEEL_VERIFY_BIN，避免调用方落回真实家目录。

## 4. 数据与状态契约

无新状态或格式。Doctor 仍只读；state.json、外来文件及其他 skill 的所有权规则保持。

## 5. 接口与协作契约

命令和参数不变。Doctor 不再输出 code-review 可用断言，不因 locator 缺失/失败退出 1；挂载缺失/占用仍退出 1。install/uninstall 保留可选 local-skill refresh 的原行为。

## 6. 运行与保障机制

外部规则由 agent 根据用户或有效项目指令的来源实际读取，记录来源、版本和范围；无法读取或冲突未解决时阻断。不新增任意文件搜索、执行规则中的命令或身份认证机制。

## 7. 迁移、发布与回滚

无状态迁移，既有可选 locator 不删除也不改配置。按现有 PR 和人审流程发布；回滚恢复本票文件。无服务部署，不能将本机安装当合入。

## 8. 测试与验证

S1.A1–S2.A2：review.md 的真实 agent 合成情境与正式独立审查；S3.A1–A3：doctor.md 的 scratch CLI 及 state/外来文件前后摘要。Integration 覆盖无 locator 与存在但不得调用两类；Unit 跑 README 规定套件，默认不注入定位替身，兼容保留 refresh 测试。字符串检查只用于辅助，不能证明实际审查发生。

## 9. 技术风险与开放问题

审查准则仍由模型执行，Doctor 不认证审查能力。保留人审及精确候选约束；没有新增技术取舍。
