# keel

本仓库维护路由 skill `keel` 与环节 skill，以及安装 CLI。

- 术语以 [docs/glossary.md](docs/glossary.md) 为准，禁止另造别称。
- `keel` 只路由；环节规则只写在对应 `keel-*` skill 里，不要抄回路由器。
- 不要把其它项目的 skill 或 pstack playbook 搬进 `skills/`。
- `bin/keel` 挂载 `skills/` 下每一个含 `SKILL.md` 的目录，以及 Grok 家目录下的 `agents/*.md`；不改用户其它 skill，不写 `~/.agents/skills/`。角色文件不写死模型 slug。
- 改安装行为时跑 `python3 -m unittest tests.test_keel`。
