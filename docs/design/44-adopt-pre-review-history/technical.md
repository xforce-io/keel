# #44 审查前运行记录的首次接入

状态：Draft v1。[Issue #44](https://github.com/xforce-io/keel/issues/44)。产品基线：[L1 Draft v1](product.md)。

## 1. 设计依据与技术目标

落实 L1 S1.A1–S3.A5。检查器继续只读，schema 仍为 1，不增加字段或入口。不改审查轮次、预算授权和发布门禁。

## 2. 现状与改动范围

基线 `3cf923c`。`skills/keel-verify/scripts/reverify.py` 的 `command` 在累计和预计算完之后才分流：`--previous` 核对前缀；`--adopt-history` 要求 `history` 与 `reviews` 都非空；否则 `--initial` 要求 `history` 为空。因此「非空且 review 数为 0」两条都失败。失败报告里累计已经是 10 秒、`model_calls=1`，预计 30 秒、`model_calls=2`。证据循环只处理 review 行。

改动限于该分流条件、`bin/keel` 的帮助、`skills/keel-verify/references/reverification.md`，以及回归和功能地图。#40 的设计文件保持原样，作为当时的契约记录。

## 3. 总体架构与关键路径

调用方声明计划 → 三个历史参数互斥 → 只读检查器算累计和预计 → 准入 → READY 或 BLOCKED。主路径是非空且无 review 的 `--adopt-history` 得到 READY。失败路径是空历史、`--initial` 见到历史、证据或预算或轮次不合法。检查器不执行计划、不写记录。

不把准入提前到累计之前：BLOCKED 仍要带回已能计算的累计和预计，这是现有行为。

## 4. 数据与状态契约

`schema_version` 保持 1。运行记录字段不变。无 review 的记录不新增 evidence。累计规则不变：任一记录的某指标为 null，该累计就是 null。

## 5. 接口与协作契约

三个参数仍必选且互斥。

- `--initial`：history 必须为空。非空时的原因仍指向 `--adopt-history` 或 `--previous`，并说明对象是已有运行记录，不只是审查。
- `--adopt-history`：history 非空即可。含 review 时，每条 review 的证据规则不变。
- `--previous`：前缀、扩展和预算授权规则不变。

READY 的 JSON 形状不变。

## 6. 运行与保障机制

预算限额、未知受限指标、三轮审查和追加授权沿用现有检查，不因 review 数为 0 而跳过。工具不监测运行中的实际消耗，也不认证历史有没有被少报。

## 7. 迁移、发布与回滚

旧的空 `--initial`、带 review 的 `--adopt-history` 和 `--previous` 保持可用。回滚是恢复「adopt 必须已有 review」这一条件；已保存的无 review 计划用旧版会再次 BLOCKED，应保留原记录，不改写成空历史。发布门禁代码不改。

## 8. 测试与验证

功能文件：`.agents/skills/verify-keel/features/reverification.md`。

| 验收 | 机制 |
|---|---|
| S1.A1 S1.A2 | Unit：`tests/test_keel_reverify.py`。E2E：`tests/drive_reverification.py` 走当前 `bin/keel reverify` |
| S2.A1 | 同上，第二次调用 `--previous` |
| S3.A1–S3.A4 | 同上，反例字段断言 |
| S3.A5 | 既有三轮与预算授权用例保持通过；本票 diff 不碰发布门禁 |

## 9. 技术风险与开放问题

无会缩小 L1 的技术假设。少报历史仍不可检测，与 L1 第 7 节一致。
