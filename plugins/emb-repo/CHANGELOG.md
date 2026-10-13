# emb-repo 变更记录

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.4.0] - 2026-10-13

### 新增

- `artifact-conventions`：明确**纳管以仓库为边界**——只有已提交到本仓库的文件才能登记为受管理文件。飞书、网盘、在线表格、厂商网站等外部系统中的内容不在管理范围内；需要纳管时由负责人把文件或其导出快照提交进仓库后再登记，外部链接只作为 `source` 来源说明，不单独成为条目。未经用户明确要求，不代为从外部系统抓取内容入库。
- 自检清单新增一项：登记的条目都是仓库中的文件。
- 新增评测 `external-not-managed`：用户要求把飞书文档登记为受控文件时，应说明需先放入仓库，不得把链接写进登记表。

### 修复（Windows）

此前插件只在 Linux 上验证过；以下问题会影响 Windows 使用者，现已修复，并在 CI 中增加 Windows 环境运行全部确定性自检。

- **hook 在 Windows 上大多无法启动**：原来以 exec 形式直接调用 `python3`，而 python.org 版 Python 在 Windows 上只提供 `python` 和 `py`，每次会话和每次编辑都会出现 hook 错误，原则注入和 hash 提醒都不生效。现在三个 hook 统一经 `hooks/run-python.sh` 启动，依次尝试 `python3`、`python`、`py -3`，实际运行通过才使用（可跳过应用商店的 `python3` 占位程序）；都不可用时以非零退出，让 Claude Code 显示 hook 错误。
- **中文系统下 hook 输入输出乱码**：hook 原来按本地编码（cp936 / GBK）读 stdin、写 stdout，而 Claude Code 按 UTF-8 收发。现在一律按 UTF-8 读入；hash 提醒以 ASCII 转义的 JSON 输出，原则注入按 UTF-8 字节输出。项目路径含中文时提醒也能正确识别文件。
- **hash 提醒给出的命令在 Windows 上不可用**：提示中的命令改为使用当前运行 hook 的 Python 解释器，路径用正斜杠并按需加引号，可直接在 Git Bash 中执行。
- **`registry_check.py update` 改变登记表换行符**：原来在 Windows 上会把 LF 登记表整体改成 CRLF（Linux 上则相反），产生整文件 diff。现在保留文件原有的换行符。管道输出（CI 日志、Claude 的 Bash 工具）固定为 UTF-8。
- `tools/lint_skills.py` 以 UTF-8 运行并读取各 skill 自检的输出。

### 变更

- `artifact-conventions` 的 `allowed-tools` 增加 `python` / `py -3` 形式的只读 `check` 命令；文档注明 Windows 上可用 `python` 或 `py -3` 代替 `python3`。
- `registry-format.md`：第 1 节写明登记范围；`path` 字段注明不得填外部链接；`source` 字段说明可记录外部原件地址；外部资料条目改为“原件放入仓库后登记”。
- `type-guide.md`：`reference` 类型的纳管条件补充“原件已放入仓库”；“不纳管的典型对象”新增仓库外内容。
- `SKILL.md` 第 3 节第 5 条（外部资料）与新边界统一表述；`when_to_use` 增加“把文件设为受控 / 纳入文控”触发词。

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
