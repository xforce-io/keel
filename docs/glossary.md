# 名词表

| 规范名 | 一句话定义 | 禁止别称 |
|---|---|---|
| keel | 路由 skill。进入流程前读何时问人、何时写设计合同，按流程选择下一合法环节，完整读取对应环节 skill 再执行。 | 我的 pstack、rd-mode、xupeng-mode、delivery 2、统一入口 skill |
| keel-issue | 环节 skill。定位仓库、Issue、验收与已完成阶段。 | issue.md、intake |
| keel-how | 环节 skill。在设计或实现前，带出处说明将改现有子系统怎么工作。 | pstack how、架构故事、keel-verify |
| keel-design | 环节 skill。写出所需设计并交回路由。 | 自批设计、design.md |
| keel-dev | 环节 skill。实现已定位范围并填写 `S1…Sn` 验收表。 | 写完就算、development.md |
| keel-verify | 环节 skill。按当前应用仓库 `.agents/skills/verify-*` 的驾驶手册与功能地图，在真路径上证明本 Issue 的 S1。 | .cursor 验证、旧 .grok/skills/verify-* 手册、pstack verify、合入后健康检查 |
| keel-review | 环节 skill。对最新精确目标做独立审查。 | 自己审自己、reviewers.md |
| reviewer | Grok 审查 agent 类型。由 `keel install` 挂到 `~/.grok/agents/reviewer.md`，`permission_mode: plan`；模型 slug 留在本机（`~/.config/keel/reviewer` 或宿主配置），不写进 keel skill。 | setup-pstack 模型表、general-purpose 自审 |
| keel-release | 环节 skill。CI、PR/MR、合入；有 runbook 则部署与核对。 | 本地跑起来、release.md |
| keel-reflect | 任务后复盘 skill。三透镜后给出 Accepted / Rejected / Backlog，人批再改 skill、AGENTS 或建 Issue。不是交付环节。 | reflection 2、自学习、pstack reflect 自动 apply |
| keel-ticket | 建票配套 skill。从对话创建 GitHub / GitLab Issue，并切到 `feat/{issue}-*` 或 `bugfix/{issue}-*`。不是交付环节。 | create-github-issue、create-gitlab-issue、intake、keel-issue |
| keel-start | 进仓配套 skill。只读待办、分支与已合入残留枝；人点头后才清残留。不是交付环节。 | monastery、巡检、治理、keel-issue |
| route | keel 流程：查看当前状态并只推进一步合法阶段。 | 随便处理一下 |
| design | keel 流程：`keel-how` 后写设计并停在人工批准。 | — |
| dev | keel 流程：写设计（若需）后实现到 review，停在可发布、不合入。 | — |
| end-to-end | keel 流程：从下一合法环节执行到 `keel-release`。 | 本地跑起来、重启服务 |
