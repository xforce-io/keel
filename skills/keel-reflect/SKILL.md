---
name: keel-reflect
description: >
  Use when the user says keel-reflect, /keel-reflect, reflection, 复盘,
  or asks to mine the current task for durable agent lessons. Do not use
  for delivery, code review, or Kairo research. Not a keel delivery stage.
---

# keel-reflect

任务后再收口。组织跟 pstack `reflect`：轨迹 → 三透镜 → Accepted / Rejected / Backlog → 人批 → Routing。

**不是**交付状态机的一站。不要在 `端到端完成` 里默认跑。不改产品代码、不合入、不部署。批准的 Issue 另用 `keel` 处理。

一次性、已有 skill 覆盖且父代理已遵守、会话太闲的，skip。

## 硬边界

- 一次调用一个范围：project 或 global，禁止同时改两边的指令文件。
- 在 git 仓库内默认 project。全局指令要两次独立任务的证据。
- 提案先出。未经用户对**精确** diff / Issue 草案的明确批准，不写指令文件、不创建 Issue、不改 skill。
- 批准前只读。不要持久化原始 transcript、秘密、个人数据或纯推测。
- 能做成 lint/脚本/CI 的，不准只写进更多 Markdown（踢到 Backlog）。

## 1. 检查器 + 轨迹

```bash
python3 <skill-directory>/scripts/inspect_context.py --cwd "$PWD"
```

`<skill-directory>` 是本 `SKILL.md` 所在目录。用 JSON 定范围、全局指令源、项目指令链、托管平台。正文只读检查器列出的每份唯一 `AGENTS.md` 一次。全局源冲突则停，把冲突给用户，不要代选。

轨迹：当前会话。能定位本工作区 transcript 则用它（不要扫其它项目的聊天）。用 diff、测试、失败、人类纠正作证据。缺证据就写缺口，不编历史。

## 2. 三透镜（并行）

一次发起三个只读子代理（Grok 优先 `explore`；没有只读类型再用通用类型并写明禁止改文件）。**不写死模型 slug。** 宿主不能并行时，父代理按序跑三个透镜，合成前不要提前合并结论。

每个透镜返回 3–5 条：Principle、Evidence（回合或短引）、建议 Routing。跳过笔误、工具重试、会随 SHA/路径漂移的细节。

| 透镜 | 找什么 |
|---|---|
| **判断** | 该记住的行为原则；下次 agent 会不会因此换动作 |
| **工具** | 用过的 skill/工具有没有洞；该触发却没触发 → `tune description` |
| **唱反调** | 一次失败当教条、把执行问题当成缺文档、不该新开 skill |

发现必须指向**本会话实际用过或本该触发**的 skill/工具。没打开过、也不是漏触发的，丢掉。

## 3. 合成 Accepted / Rejected / Backlog

父代理合成。同一根因合并。标准：持久、具体、先改现有 skill、两条以上透镜呼应则更稳、能改变下次行为。

## Accepted

改**行为工具**的行，等人逐行批：

| Problem | Proposal | Routing |
|---|---|---|
| 用过的 skill 有洞 | 改该 skill 正文 | `skills/…/SKILL.md` 或章节 |
| skill 在册却没触发 | 调 description | `tune description: <path>` |
| 新模式且没有合适家 | 新 skill | `new skill: <kebab-name>` |
| 可执行的项目/全局指令 | 一条 `AGENTS.md` diff | 检查器给出的目标文件 |

Accepted 里 **AGENTS 至多一条**（`no-change` / `merge` / `rewrite` / `delete` / `add`，评估见 [evaluation.md](references/evaluation.md)）。skill 行可多条，但每条要能独立批准。

## Rejected

每条：Principle + Reason（不持久 / 太泛 / 已覆盖 / 没使用该 skill / 一次失败 / 结构项应进 Backlog 等）。

## Backlog

产品缺口，或「该做成检查器而不是再写说明书」。**出 Issue 草案，你批了才建**，不自动建单。准入、优先级、去重见 [issues.md](references/issues.md)。

## 4. 结构落实检查

Accepted 里若用 lint、脚本、metadata、运行时检查能更稳地执行，移到 Backlog，不要只改 skill 散文。

## 5. 呈交

压缩输出：

1. 范围、证据、缺口  
2. 三份名单（Accepted 表、Rejected、Backlog 草案或 `no-backlog`）  
3. 一句批准问：要落地哪些 Accepted 行、要创建哪些 Backlog Issue  

## 6. 批准后 Routing

只做勾过的项。

- 现有 skill / AGENTS 改一行：直接打已展示的补丁；改指令后重跑检查器，确认链一致  
- 大段新节、新 skill、`tune description`：按 skill 作者流程，不在本 skill 里即兴长文  
- 应用仓库 `verify-*` 地图过时：改那对文件，不改 keel 插件  
- 动 `keel-*`：仅当 cwd 是 keel 或证据就是交付机不好用  
- Backlog Issue：写入前重查 origin/平台/重复；创建后停止。修复走单独的 `keel`  

提案若在批准后有变，重新展示再问一次。
