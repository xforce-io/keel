# #40 未知计量与已有审查接续

状态：Draft v1；[Issue #40](https://github.com/xforce-io/keel/issues/40)；[L1 v1 与用户确认](https://github.com/xforce-io/keel/issues/40#issuecomment-6540074022)。沿用 [#31 复验合同](31-verification-cost-control.md)。本文件为本票唯一详细设计。

## 1 背景

原 CLI 在历史记录中拒绝未知的原子读取、上游请求；首次接入时已有审查却没有先前复验计划。原入口在基线 588aacd 实测分别阻断于 `history.metrics.atomic_reads` 和 `initial plan must have empty history`。原因分别是 metrics 仅对 token 接受 null，以及无 previous 时强制空 history。

## 2 名词解释

沿用[名词表](../glossary.md)，无新增领域词。

## 3 目标与非目标

实现 #40 S1/S2：如实保留不可得计量、接续已有审查，并继续约束受限预算、审查轮次及追加授权。不认证记录真实性，不降低验证、审查或发布门禁。

## 4 能力

CLI 提供显式首次接入已有审查的入口；未知受限指标仍阻断。READY 仅表示只读准备核对完成。

### 4.1 UI/UX

CLI 主路径：准备历史及审查原始文件 → 选择新入口 → 输出 READY 或 BLOCKED 及定位；无图形界面。后续只能以 previous 接续。

## 5 思路与折衷

独立入口区分空起点和已有历史；审查证据沿用文件路径与 SHA-256 核对，不解析日志。放弃放宽 initial、伪造 previous、自动识别或认证来源；工具无法识别使用者有意隐瞒历史，必须由调用方和独立审查核实。

## 6 架构

调用方声明任务、候选、证据和预算 → CLI 参数互斥校验 → 只读检查器校验历史、证据、预算和轮次 → READY/BLOCKED；缺失文件、摘要错误或未知受限值走 BLOCKED。检查器不执行计划、不写数据。

## 7 模块

`bin/keel` 声明入口；`skills/keel-verify/scripts/reverify.py` 实施检查；复验合同说明格式和限制。安装复制复用既有机制。

## 8 API/CLI

`--adopt-history` 与 `--initial`、`--previous` 必选且互斥。initial 历史为空；adopt-history 历史非空且至少有一条 review，每条 review 具有 `evidence: {path, sha256}`，文件可读且摘要匹配。历史 metrics 的 `atomic_reads`、`upstream_requests` 可为 null，planned 同样适用；预算限制项的预计值未知则 BLOCKED。其他指标及 model_calls 规则不变。既有 previous 记录无需补证据字段；带证据的记录持续校验。接入后的 history 和 extensions 沿 previous 保持前缀一致。相对证据按声明所在记录目录解析；续跑须保留上一记录目录的证据。后续新审查仍沿用原有 history 合同。

## 9 边界

审查达到三轮时下一次 agent/review 仍须有效扩额，失败审查后的 retry 仍须完整。工具不认证证据内容、作者或授权，不检测隐瞒历史，不提供强防篡改存储。

## 10 迁移/兼容/回滚

schema_version 保持 1；原 empty initial 和 existing previous 保持兼容。新字段仅要求首次接入的审查；回退旧版无法读取新入口，应保留原始记录，不伪造空历史。

## 11 测试计划

E2E：#40 S1 实际 CLI 未设限时 null/READY、分别设限时 BLOCKED；S2 一轮接入及 previous 续跑、缺失证据阻断、三轮阻断和授权追加。对应 `.agents/skills/verify-keel/features/reverification.md`。Integration：隔离复制安装、CLI 参数互斥、历史及证据续跑。Unit：空历史、无 review、摘要错误、历史篡改、现有契约回归。原问题输入与入口用于前后对照。

## 12 开放问题

无阻塞问题。来源真伪及历史完整性依赖调用方和独立审查，不由工具自动判断。

## 13 关联

[#31](https://github.com/xforce-io/keel/issues/31)、[#40](https://github.com/xforce-io/keel/issues/40)、[L1](https://github.com/xforce-io/keel/issues/40#issuecomment-6540074022)、功能地图 `reverification.md`；PR 待创建后关联。
