# emb-repo 变更记录

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.3.0] - 2026-10-09

### 新增

- `artifact-conventions`：基于用户确认的 Inform + Principles 管理形式，指导工程文件类型识别、项目 YAML 登记入口、稳定 ID、通用生命周期、适用范围和项目新增类型。
- 登记表规范、类型目录、增量纳管与专业 Skill 集成指南及可复制示例；新增正向创建/核查与普通脚本反向评测。
- **可选的受控文件 hash 校验**：登记表声明 `integrity: sha256` 后，每个条目记录 `sha256`。
  - `scripts/registry_check.py`：`check`（CI 用；`--base` 检查冻结条目是否被修改或删除，基线无法读取时报错而非跳过）、`update`（只改条目这一层的 `sha256` 行，不碰 `source.sha256` 等嵌套字段，保留注释和顺序；写盘前重新解析并核对每个请求的 hash，任何条目未能更新时不写盘并以非零退出）、`hash`；git 输出一律按 UTF-8 解码，不受本地编码影响；文本统一 LF、二进制按原始字节、Git LFS 指针直接取 oid。
  - `draft` / `active` 修改后只需更新 hash；`superseded` / `archived` 冻结，已有 hash 时 `update` 默认拒绝改写（首次写入基线不受限）。
  - `PostToolUse` 提醒 hook（`integrity_reminder.py`，仅标准库）：编辑受控文件后提示更新 hash，编辑冻结文件后提示撤销；插件选项 `integrity_reminders`（默认开启）。
  - CI 与 CODEOWNERS 模板（`assets/ci/`）；hash 不等于审批，CODEOWNERS 由项目自选。
  - 确定性自检覆盖上述行为；新增评测 `integrity-update`、`integrity-frozen`。

### 变更

- `engineering-principles` 轻量核心新增“受管理文件有入口”原则（覆盖创建和修改）；会话注入与子 Agent 摘要使用同一来源，其余工作仍不强制纳管。
- README 中补充受管理登记表与普通文档导航索引的区别。

### 状态

- 评测（每个用例 3 次）：`create-managed-spec`、`registry-inconsistency`、`no-trigger`、`integrity-update`、`integrity-frozen` 均为 1.00。
- 实际安装后验证：新建受管理文件会自动登记为 `draft`；新建普通脚本不改动登记表；在启用 hash 校验的项目中修改 active 协议后，hash 会被正确更新。
- 说明：未加提醒 hook 时，“修改受控文件后更新 hash”的评测为 0/3，“不改冻结文件”为 0/3。仅靠 skill 描述无法可靠触发，因此改用 hook 做确定性提醒。

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
