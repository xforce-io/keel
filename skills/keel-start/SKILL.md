---
name: keel-start
description: >
  Use when the user says keel-start, /keel-start, code start, 打开这个项目,
  待办, 分支什么情况, or wants a repo-level map of open issues, PRs, and leftover
  merged branches before picking a ticket. Not a delivery stage. Do not use to
  locate one Issue (keel-issue), file one (keel-ticket), or operate monastery.
---

# keel-start

进当前 git 仓库，给出**只读**待办地图。不是交付环节。默认不改 ref 与工作区（squash 探测会写一个游离 commit 对象，gc 回收，不更新任何 ref）。不调用 `keel-issue`、`keel-ticket`、monastery。

禁止别称：monastery、巡检、治理、intake、keel-issue。

## 何时用

刚打开一个 checkout，要看清：在哪条枝、有哪些 open Issue / PR、哪些枝已合入还没删、有没有非法前缀。看完停。人点一张票 → `keel` → `keel-issue`；没票要开 → `keel-ticket`。

## 只读（必须先做完再问清不清）

1. `git remote get-url origin`，口头确认平台（GitHub / GitLab）。无法判定 → `BLOCKED`，问一次。
2. 默认分支短名：`git symbolic-ref --short refs/remotes/origin/HEAD` 去掉 `origin/`（没有则 `main` / `master`）。比较用 `origin/<短名>`；`git checkout` 只用本地短名，禁止 `checkout origin/<短名>`（会 detached HEAD）。
3. 当前分支：`git branch --show-current`；相对 `origin/<短名>`：ahead/behind、是否脏。
4. Open Issue / PR：
   - GitHub：`gh issue list --state open`、`gh pr list --state open`
   - GitLab：从 origin 解析 host 与 project path；`GET {host}/api/v4/projects/:id/issues?state=opened` 与 `…/merge_requests?state=opened`，`:id` 可用 URL-encoded path。仅 `$GITLAB_API_TOKEN`。未设置则 `BLOCKED`，不回退 `gh`
5. 残留枝。本地短名：`git branch --format='%(refname:short)'`。远程短名：`git for-each-ref --format='%(refname:short)' refs/remotes/origin`，去掉 `origin/`，丢掉 `HEAD`。比较对象 `tip`：本地有该短名用本地 ref，否则用 `origin/<短名>`。按顺序只走一条（默认短名除外）：
   1. **祖先**：`git merge-base --is-ancestor <tip> origin/<默认短名>` → 残留（祖先）
   2. 否则 **squash**：已合入 PR/MR（GitHub `gh pr list --head <短名> --state merged` 非空；GitLab `GET …/merge_requests?state=merged` 且 `source_branch` 等于短名）**且** 合成探测为已合入：
      `base=$(git merge-base origin/<默认短名> <tip>)`；`probe=$(git commit-tree "$(git rev-parse <tip>^{tree})" -p "$base" -m squash-probe)`；`git cherry origin/<默认短名> "$probe"` 的那一行以 `-` 开头。`merge-base` / `commit-tree` / `cherry` 任一失败（无共同祖先、无 committer identity、空 probe）→ 该短名算未合入，不准进残留表，不要猜
   3. 否则 → 未合入，不准进残留表
   当前分支若已合入仍列入残留。未合入的当前工作枝不列入。列出：已合入仍在（注明祖先或 squash）、未合入、非法前缀（不是 `feat/*` / `bugfix/*` / 默认短名）。
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

工作区脏 → `BLOCKED`，不 stash、不切走。只删表里「已合入仍在」的短名：

- 若其中含当前分支：先 `git checkout <默认短名>`，再删
- 本地：祖先 → `git branch -d`；squash → `-D`
- 远程：`tip` **固定**为 `origin/<短名>`（忽略本地同名 ref），再跑一遍第 5 步仍是残留，才 `git push origin --delete <短名>`

不删：当前未合入工作枝、默认短名、第 5 步判未合入的枝。不关票、不合 PR。删完再打一次只读表。

## 完成

报告停在只读或已清。下一步只说一个：处理哪张 Issue，或 `keel-ticket` 开票。不要默认进入交付。
