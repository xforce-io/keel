---
name: keel-how
description: >
  Use when the user says keel-how or /keel-how, or when keel routes to
  explain an existing subsystem before design or implementation. Cite source.
  Do not write L1/L2, change product code, drive the app, or merge.
---

# keel-how

只讲**将改的现有子系统现在怎么工作**。只读源码。不写设计、不改产品代码、不开应用。

产出给 `keel-design` / `keel-dev` 用，不代替它们。不是 `keel-verify`（真路径证明），也不是合入后健康检查。

## 何时必须跑

将改现有代码，且属于任一：跨模块、所有权不清、用户可见主路径。本会话还没有针对**同一子系统**的 how 产出。

## skip（必须写明哪一条）

仅这三条：

1. `skip: 已定位机制` — 本会话已有针对将改子系统、带出处的说明。
2. `skip: 无现成机制可讲` — 全新、没有可讲的现成代码。
3. `skip: 单模块且入口已钉死` — 单模块、入口明确、范围已钉死。

禁止「我已经懂了」而无上述原因。票面描述不能顶替源码。

## BLOCKED

读了将改范围仍无法从源码说明机制 → `BLOCKED`，问人。禁止猜完进入 `keel-design` 或 `keel-dev`。

无文件或符号出处的「架构故事」不算完成。

## 产出

用这些节，没有的可省略：Overview · 怎么跑 · 东西在哪 · Gotchas。每一条机制断言带仓库内路径（文件，必要时符号）。然后把控制权交回路由。
