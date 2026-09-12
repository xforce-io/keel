# 名词表

| 规范名 | 一句话定义 | 禁止别称 |
|---|---|---|
| keel | 路由 skill。按模式选择下一合法环节，完整读取对应环节 skill 再执行。 | 我的 pstack、rd-mode、xupeng-mode、delivery 2、统一入口 skill |
| keel-issue | 环节 skill。定位仓库、Issue、验收与已完成阶段。 | issue.md、intake |
| keel-design | 环节 skill。写出所需设计并停在人工批准。 | 自批设计、design.md |
| keel-dev | 环节 skill。实现已批准范围并填写 `S1…Sn` 验收表。 | 写完就算、development.md |
| keel-verify | 环节 skill。按当前应用仓库 `.grok/skills/verify-*` 的驾驶手册与功能地图，在真路径上证明本 Issue 的 S1。 | .cursor 验证、pstack verify、合入后健康检查 |
| keel-review | 环节 skill。对最新精确目标做独立审查。 | 自己审自己、reviewers.md |
| keel-release | 环节 skill。CI、PR/MR、合入；有 runbook 则部署与核对。 | 本地跑起来、release.md |
| route | keel 模式：查看当前状态并只推进一步合法阶段。 | 随便处理一下 |
| design | keel 模式：执行到 `keel-design` 并停在人工批准。 | — |
| dev | keel 模式：`keel-dev` → `keel-verify` → `keel-review`，停在可发布、不合入。 | — |
| end-to-end | keel 模式：从下一合法环节执行到 `keel-release`。 | 本地跑起来、重启服务 |
