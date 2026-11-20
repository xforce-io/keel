# 产品概念建模

覆盖 [Issue #62](https://github.com/xforce-io/keel/issues/62) S1–S2 和 [L1 v1](../../../../docs/design/62-product-ontology-method/product.md) §8。

1. 在干净候选上按手册执行 scratch install、doctor。从安装后的 keel-design 入口读取设计合同，核对 L1 第 3 节的按需引用可读。
2. 通过该入口提供训练产物还可用作评估基线的案例，要求完成产品设计相关部分。核对走查两条路径后，一个模型版本通过不同关系承载两个角色；结果可校验权限或输入不符的后果。对应 S1.A1。
3. 同一安装另开独立案例，给出仅替换文案且现有契约明确的需求。核对仍沿用既有产品设计适用条件，未要求额外建模、阶段或独立文档。对应 S2.A1。
4. 保存候选 SHA、设计版本、安装/doctor 输出和两条案例的原始 Agent 输入与输出，再执行 scratch uninstall。独立评审员对照 §8 判断输出；文件存在和命令成功只证明入口可用。
