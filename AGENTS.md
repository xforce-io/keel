# keel

本仓库只维护一条 skill 和它的安装 CLI。

- 术语以 [docs/glossary.md](docs/glossary.md) 为准，禁止另造别称。
- 不要把其它项目的 skill 或 pstack playbook 搬进 `skills/`。本仓库只含 keel。
- `bin/keel` 只负责挂载与拆除；不改用户其它 skill，不写 `~/.agents/skills/`。
- 改安装行为时跑 `python3 -m unittest tests.test_keel`。
