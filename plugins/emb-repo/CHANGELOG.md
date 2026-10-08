# emb-repo 变更记录

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.2.0] - 2026-10-09

### 新增

- `engineering-principles`：经过访谈确认的 Inform + Principles 工程默认原则，区分 Issue/ADR/协议/方案、探索与承诺、共同主线契约、证据和有界可诊断交接。
- `SessionStart` / `SubagentStart` 插件 Hook：共用一份精简原则，默认注入轻量上下文；详细参考由 Skill 按需加载，不替代专业 Skills。
- 提供标准库 Hook 脚本和确定性自检，新增复杂工程契约与普通 C 语法的正反向 Skill 评测。

### 状态

- 尚未运行 Claude 官方 Skill 评测，README 暂标“开发中”；正式发布前按 docs/evals.md 评测。

## [0.1.0] - 2026-10-06

### 新增

- `project-profile`：项目画像的建立（init）、更新（update）与核查（check）；画像规范 v1；证据扫描脚本 `scan_repo.py`；3 个评测用例。
