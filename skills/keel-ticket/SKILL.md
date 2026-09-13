---
name: keel-ticket
description: >
  Use when the user says keel-ticket, /keel-ticket, 开票, 建 Issue, 跟踪这个需求,
  or wants to file a GitHub/GitLab issue from the conversation and switch to
  a feat/* or bugfix/* branch. Not a delivery stage. Do not use to locate an
  existing Issue (that is keel-issue) or to start route/design/dev/end-to-end.
---

# keel-ticket

从当前对话**建一张 Issue**，并切到合法工作分支。不是交付环节。建完停止，不自动 `route` / `design` / `dev` / `end-to-end`。不调用 `keel-issue`。

禁止别称：create-github-issue、create-gitlab-issue、intake。

## 何时用

用户要开新票、跟踪一个还没有 Issue 号的需求。已有 Issue N → 交给 `keel` → `keel-issue`，不要在这里重建。

## 步骤

0. **识别托管平台（先于一切写操作）**
   - `git remote get-url origin`（必要时 `git remote -v`）
   - `github.com` 或明确 GHE → **GitHub**
   - host 含 `gitlab` 或典型 GitLab URL → **GitLab**
   - 无法判定 → 问用户，停止
   - 向用户确认一句：host + 平台
   - **GitLab** 才用 `$GITLAB_API_TOKEN`；**GitHub 禁止使用**该变量
   - 禁止对 GitLab 仓默认执行 `gh issue create`

1. 整理标题与 body。标题：`【{module}】{一句话结果导向标题}`（模块边界清晰才加 `【module】`）。body 必须用下方模板。**禁止**把设计方案写进创建 body。

2. **校验 Stories ↔ 验收 1:1**
   - 至少 1 条，优先 2–5 条，超过 7 条先问是否拆票
   - 编号、顺序、数量与「验收标准」一致
   - 每条操作闭环；能定量则写定量，验收句用同一数字

3. **按平台创建**
   - **GitHub**：`gh issue create`。feature → `enhancement`（若有）；bugfix → `bug`（若有）。`gh` 未登录则停。
   - **GitLab**：REST `POST {host}/api/v4/projects/:id/issues`，仅 `$GITLAB_API_TOKEN`。未设置则失败，不回退 `gh`，不创建半成品。
   - 取出 GitHub number / GitLab **iid**

4. **建分支并切换**（Issue 创建成功之后）
   - feature → `feat/{issue}-{short-desc}`
   - bugfix → `bugfix/{issue}-{short-desc}`
   - `{short-desc}`：小写 kebab-case，3–5 词，仅 `a-z` `0-9` `-`
   - 同名分支已存在 → `BLOCKED`，不覆盖、不改到默认分支上开发
   - `git checkout -b ...`

5. 报告平台、Issue URL、编号、分支名。**停止。** 不要读 `keel` 去推进交付。

## Body 模板（必须使用）

```markdown
## 背景

{1–5 句}

## 目标

{1–3 句，结果导向}

## Stories

### S1. {短标题}

- **角色**：
- **前置**：
- **操作**：
  1.
  2.
- **闭环结果**：
- **定量**：{指标或 N/A}

### S2. {短标题}

- **角色**：
- **前置**：
- **操作**：
  1.
  2.
- **闭环结果**：
- **定量**：

## 范围

- In：
- Out：

## 复现 / 依据

{Bug 步骤 / 依据 / N/A}

## 验收标准

- [ ] **S1**：
- [ ] **S2**：

## 关联

- {可选；无则整节省略}
```

## 规则

- Issue = 问题与验收；设计发 **comment**，人批后再 promote。名词表不进 issue body。
- 术语以仓库 `docs/glossary.md` 为准。缺失则先补规范名，禁止另造别称。
- 不要粘贴大段对话；不要写入密钥或 token。
- **永不默认 GitHub**；平台以当前 origin 为准，换仓库须重判。
