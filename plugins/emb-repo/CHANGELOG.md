# emb-repo 变更记录

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.2.0] - 2026-10-09

### 新增

- `engineering-principles`：经过访谈确认的 Inform + Principles 工程默认原则，区分 Issue / ADR / 协议 / 方案、假设与承诺、主线契约冲突、证据，以及交付可接手、问题可诊断。
- `SessionStart` / `SubagentStart` 插件 hook：会话开始注入轻量原则，子 Agent 启动只注入一行精简版（由同一份 `core-principles.md` 生成）；详细参考由 skill 按需加载，不替代专业 skill。
- 插件选项 `inject_principles`（默认开启）：可在 `/config` 或 `claude plugin configure` 中关闭自动注入。
- 标准库 hook 脚本与确定性自检（输出格式、开关、体积上限）；正向（契约冲突、轻量变更）与反向评测用例。

### 变更

- 插件定位扩展为“嵌入式项目基础”：除项目画像外，承载默认工程原则。

## [0.1.0] - 2026-10-06

### 新增

- `project-profile`：项目画像的建立（init）、更新（update）与核查（check）；画像规范 v1；证据扫描脚本 `scan_repo.py`；3 个评测用例。
