# adrs 命令与实测行为

以下行为在 adrs 0.12.1 上实测。版本变化后，先用 `adrs <命令> --help` 核对。

## 1. 安装与检查

| 用途 | 命令 |
| --- | --- |
| 安装 | `cargo install adrs` 或 `brew install adrs` |
| 版本 | `adrs --version` |
| 当前配置：目录、模式、配置来源 | `adrs config` |
| 健康检查 | `adrs doctor` |

`adrs config` 中应看到 `Mode: Compatible`，`ADR directory` 与项目约定一致。

## 2. 常用操作

| 操作 | 命令 | 结果 |
| --- | --- | --- |
| 新建 | `adrs new --no-edit "<标题>"` | 新文件状态为 `Proposed`。不加 `--no-edit` 会打开编辑器，在非交互环境中卡住 |
| 取代 | `adrs new --no-edit --supersedes <旧编号> "<标题>"` | 旧 ADR 状态改为 `Superseded`，并加一行 Superseded by，链接到新 ADR；新 ADR 加一行 Supersedes，链接到旧 ADR |
| 改状态 | `adrs status <编号> <状态>` | 状态可为 proposed、accepted、deprecated、superseded、rejected。`superseded` 用 `--by <编号>` 指明取代者 |
| 链接 | `adrs link <源> "<关系>" <目标> ["<反向关系>"]` | 两边各加一行，例如 `Amends` 与 `Amended by`；反向关系可以省略，由工具推导 |
| 列表 | `adrs list`、`adrs list --status accepted` | 输出文件路径 |
| 生成目录 | `adrs generate toc` | 每个 ADR 一行列表项，链接文字为“编号. 标题”，标题取自文件第一行 |

## 3. 已知坑

| 现象 | 原因 | 做法 |
| --- | --- | --- |
| `adrs status` 提示成功，文件里的状态没变 | 章节标题 `## Status` 被改成了中文 | 章节标题保持英文；任何状态变化后重新读取文件确认 |
| 新建命令一直不返回 | 打开了编辑器 | 加 `--no-edit` |
| ADR 建到了 `doc/adr` | 有 `adrs.toml` 但没写 `adr_dir`，`.adr-dir` 被忽略 | 在 `adrs.toml` 中写 `adr_dir = "<目录>"`，或删除 `adrs.toml` |
| 取代时新 ADR 的 Supersedes 链接只有编号，指向不存在的文件 | 使用了自定义模板 | 使用内置模板 |
