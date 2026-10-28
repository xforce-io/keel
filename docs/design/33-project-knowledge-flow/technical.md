# 项目知识与无号任务：技术设计

版本：v1；Issue [33](https://github.com/xforce-io/keel/issues/33)；依据 [L1 v1](product.md)，覆盖 S1.A1–S3.A4；状态：待交付审查。

## 1. 目标与约束

以现有 Markdown skill 合同实现，不增加服务或平台依赖；保留现有验证、review 和发布门禁。

## 2. 现状与范围

`skills/keel-how/SKILL.md` 当前只读源码、按出处解释；`skills/keel-issue/SKILL.md` 缺号即问；`skills/keel-ticket/SKILL.md` 建票后停止；`skills/keel/SKILL.md` 路由并禁止无号交付建票。`tests/test_keel.py` 及功能地图 ticket.md 固化旧约定。修改各职责所属 skill、参考文件、相关测试及验证地图。

## 3. 总体架构与关键路径

how 发现知识并核对源码；参考文件提供默认路径与格式；dev 更新受影响知识，review 检查其一致性。issue 负责识别无号和查重；唯一匹配继续定位，无匹配交 ticket 创建；ticket 在调用方为交付任务时返回结果，路由恢复原模式，显式建票仍停。歧义、查询失败或创建失败停止并报告。

## 4. 数据与状态

项目已有知识是事实源的入口，不覆盖源码；设计为意图，源码为当前实现；默认 docs/knowledge/ 可选，需保留范围、机制、出处、注意事项与核对基线。不会由安装程序生成项目文件。

## 5. 接口与协作

skill 通过 Markdown 相互引用；issue 必须先完成可判定查重再转 ticket，不能将 API 错误当零结果；明确目标编号直走原定位。ticket 输出 Issue 编号及合法分支，调用方按模式继续，不改变单独调用的停止行为。

## 6. 运行保障

凭据按既有平台规则；不写秘密。歧义询问，任何未核实的匹配或写入状态 BLOCKED。知识无据不保存。how 保持只读。

## 7. 迁移、发布与回滚

不迁移已有项目或修改用户配置；安装已有链接时 skill 变更自然生效。回滚相关 skill 和参考文件即可；已创建 Issue 由项目管理，不自动删除。

## 8. 测试与验证

S1.A1–A2、S2.A1–A2、S3.A1–A4 映射 `.agents/skills/verify-keel/features/project-knowledge.md`。源码级测试检查合同与旧限制消除；隔离环境驱动安装并按功能文件从 skill 入口实跑场景，留证据；平台失败和歧义不得伪称真实成功。

## 9. 风险

自然语言 skill 的结果依赖宿主与可用 tracker；真实 agent 验收不能仅靠字符串测试。查重语义不确定时必须询问。
