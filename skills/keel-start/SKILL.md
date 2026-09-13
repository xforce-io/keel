---
name: keel-start
description: >
  Use when the user says keel-start, /keel-start, code start, 打开这个项目,
  待办, 分支什么情况, or wants a repo-level map of open issues, PRs, and leftover
  merged branches before picking a ticket. Not a delivery stage. Do not use to
  locate one Issue (keel-issue), file one (keel-ticket), or operate monastery.
---

# keel-start

进当前 git 仓库，给出**只读**待办地图。不是交付环节。默认不改 git。不调用 `keel-issue`、`keel-ticket`、monastery。

禁止别称：monastery、巡检、治理、intake、keel-issue。

## 何时用

刚打开一个 checkout，要看清：在哪条枝、有哪些 open Issue / PR、哪些枝已合入还没删、有没有非法前缀。看完停。人点一张票 → `keel` → `keel-issue`；没票要开 → `keel-ticket`。

## 只读（必须先做完再问清不清）

1. `git remote get-url origin`，口头确认平台（GitHub / GitLab）。无法判定 → `BLOCKED`，问一次。
2. 默认分支：`git rev-parse --abbrev-ref origin/HEAD`（没有则 `main` / `master`）。
3. 当前分支：`git branch --show-current`；相对默认分支：ahead/behind、是否脏。
4. Open Issue / PR：
   - GitHub：`gh issue list --state open`、`gh pr list --state open`
   - GitLab：从 origin 解析 host 与 project path；`GET {host}/api/v4/projects/:id/issues?state=opened` 与 `…/merge_requests?state=opened`，`:id` 可用 URL-encoded path。仅 `$GITLAB_API_TOKEN`。未设置则 `BLOCKED`，不回退 `gh`
5. 残留枝：本地 `git branch --format='%(refname:short)'` 与远程 `git branch -r`，对每一条（除默认分支）判定「已合入仍在」仅当下面**任一**成立：
   - `git merge-base --is-ancestor <branch> <default>`
   - GitHub：`gh pr list --head <branch> --state merged` 非空（squash 残留）
   - GitLab：对应 project 的 merged MR，`source_branch` 等于该短名
   当前分支若已合入，仍列入「残留」，清的时候先切默认分支再删，不要对着当前枝 `branch -d`。未合入的当前工作枝不列入残留。列出：已合入仍在、未合入、非法前缀（不是 `feat/*` / `bugfix/*` / 默认分支）。
6. 输出一张表，然后停（除非本轮明确说清）：

| 类 | 内容 |
|---|---|
| 当前 | 分支名、相对默认分支、工作区脏/净 |
| 待办 | open Issue 数与标题；open PR 数与标题 |
| 残留 | 已合入仍在的本地/远程分支 |
| 非法前缀 | `chore/*`、`cursor/*`、`fix/*`、无前缀非默认 |

至少输出当前分支名与 open Issue 数量（可为 0）。

禁止：关 Issue、合 PR、`assess`、调 `monastery`、自动 `route`。

## 清残留（仅当本轮明确说「清」）

只删表里「已合入仍在」的枝：

- 若其中含当前分支：先 `git checkout <default>`，再删
- 本地：`merge-base --is-ancestor` 成立用 `git branch -d`；仅因 merged PR/MR 列入的 squash 残留用 `-D`
- 远程：`git push origin --delete <name>`（仅上表已合入项）

不删：当前未合入工作枝、默认分支、尚未合入的 `feat/*` / `bugfix/*`。不关票、不合 PR。删完再打一次只读表。

## 完成

报告停在只读或已清。下一步只说一个：处理哪张 Issue，或 `keel-ticket` 开票。不要默认进入交付。
