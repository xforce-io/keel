# 功能地图

| 文件 | 用户能看见什么 | 对上的验收 |
|---|---|---|
| [install.md](./install.md) | `keel install` 把 skill 与 CLI 挂到 `--home`；不写 `.agents/skills/` | 安装后 library + bin 可用 |
| [ticket.md](./ticket.md) | install 后能 `find keel-ticket`；工作分支只许 `feat/*` / `bugfix/*` | #4 S1–S4 |
| [start.md](./start.md) | install 后能 `find keel-start`；进仓只读、说清才删残留 | #6 S1–S4 |
| [review.md](./review.md) | install 后能 `find keel-review`；审查结论带 `human`，`required` 不得发布 | #7 S1–S3 |
| [doctor.md](./doctor.md) | `keel doctor` 只读报告挂载、占用与 code-review | 缺失或占用时退出码 1 |
| [uninstall.md](./uninstall.md) | `keel uninstall` 只拆 keel 自己挂上的链接或副本 | 外人不删；`--keep-bin` 留 CLI |

未列入的 `/keel` 会话路由、各环节 skill 正文：本 Issue 不对则不要 Drive。新增用户可见 CLI 入口时在此加一行并补功能文件；验收 Story 对不上任何一行即 BLOCKED。
