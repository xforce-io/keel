# 产品与技术两层设计

本功能验证已安装 skill 合同及引用，不冒充模型行为评测或下游产品 UI 验证。关联 #24 S1–S3 与 [L1.8](../../../../docs/design/24-product-technical-design/product.md)。

## 用户入口（全部走）

1. 按手册在 scratch home 执行 install 和 doctor。
2. 从 scratch library 的 keel-design/SKILL.md 进入 references/design-contract.md，核对 S1.A1；读取同级 keel/references 的触发与确认规则。
3. 读取安装后的 keel-dev、keel-verify、keel-review、keel-release，核对 S2.A1：逐项证据、未执行、缺环境、S 汇总、标准修订与候选版本。
4. 读取设计合同迁移节、release/references/check.md，核对 S3.A1。确认引用真实可读、v1 能力限制明确，随后 scratch uninstall。

## 证据与判定

在 `.agents/verify-runs/24/` 保存原始命令、退出码、安装与 doctor 输出、各项摘录、候选 SHA。逐项记录 S1.A1/S2.A1/S3.A1，未读或引用缺失不能记 pass。运行合同测试作为辅助证据；不能仅凭测试替代安装入口检查。
