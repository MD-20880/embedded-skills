# ADR 文件格式

ADR 采用 Michael Nygard 格式的兼容模式，[adrs](https://github.com/joshrotenberg/adrs) 和 [adr-tools](https://github.com/npryce/adr-tools) 都能读写。不使用 MADR 或 adrs 的 NextGen 模式：它们带 YAML 头，adr-tools 不认。

## 1. 骨架

```markdown
# 3. 标题（可以用中文）

Date: 2026-01-31

## Status

Proposed

Supersedes [2. 被取代的 ADR 标题](0002-old-decision.md)

## Context

（背景）

## Decision

（决定，含被否决的方案及理由）

## Consequences

（影响，含待决问题）

## 决策信息

- 决策人：
- 确认：（谁、何时把状态改为 Accepted；未确认写“尚未确认”）
- 关联 issue：
```

- 第一行 `# 编号. 标题`、`Date:` 行、`## Status` 一节由 adrs 生成，链接行（`Supersedes`、`Superseded by`、`Amends` 等）由 adrs 命令写入，不要手改。
- “决策信息”是本仓库约定的附加章节，放在最后，不影响工具读写。

## 2. 必须用英文的部分

| 部分 | 写法 | 原因 |
| --- | --- | --- |
| 四个章节标题 | `## Status`、`## Context`、`## Decision`、`## Consequences`，原样保留 | adrs 按这些标题定位章节。把 `## Status` 改成中文后，`adrs status` 仍提示修改成功，但文件里的状态不变（adrs 0.12.1 实测） |
| 状态词 | `Proposed`、`Accepted`、`Deprecated`、`Rejected`、`Superseded` | `adrs list --status` 按这些词筛选 |
| 链接行 | 由 adrs 写入的英文，如 `Superseded by [...]`、`Amends [...]` | 工具生成和解析 |

其余正文使用项目的语言。

## 3. 各章节写什么

### Context

- 要解决什么问题，为什么现在要决定；
- 约束：硬件、时间、供应方、合规、已有决定；
- 事实与推断分开标：“实测（L2）：”“推断：”“待查：”；
- 引用来源：issue、设计文档、手册章节。

### Decision

- 第一句写决定本身，用“我们……”的主动句；
- 适用范围：哪些板、硬件版本、固件、阶段；
- **被否决的方案**：逐个列出，每个写一句理由。讨论中没有其他方案时，写明“讨论中没有其他方案”；
- 只写已经拍板的内容。尚未定的部分放到 Consequences 的“待决问题”。

### Consequences

- 要跟着改的文档、issue、硬件、固件，逐条列出；
- 带来的好处和代价，包括风险；
- 待决问题：本决定引出、但还没有人拍板的问题。每个建议另开问题 issue。

### 决策信息

- 决策人：谁有权拍板；
- 确认：谁、在什么时间、在哪里（会议、issue 评论）表态。没有表态时写“尚未确认”，状态保持 `Proposed`；
- 关联 issue：问题 issue 的编号或链接。问题 issue 的“决策记录”中同时链接回本 ADR。

## 4. 建议（不是硬性规则）

以下几点来自 adrs 0.12.1 的实测，由项目自行决定是否采用：

- **文件名用 ASCII。** 用中文标题运行 `adrs new`，文件名里会带中文（例如 `0002-lora-链路按-318-...md`），在部分工具和网址中需要转义。可以先用英文短语创建（`adrs new --no-edit "plan-without-vendor-stack"`），再把标题行中 `N. ` 之后的文字改成中文。改完后 `adrs list`、`adrs generate toc`、`adrs link`、`adrs status` 都正常，显示中文标题。注意：如果创建时用了 `--supersedes`，旧 ADR 中 Superseded by 一行的链接文字是创建时的英文短语，改标题行不会同步。链接仍然有效；需要一致时，只改该行方括号里的文字，不动链接目标。
- **增加 `adrs.toml` 时写上 `adr_dir`。** 有 `adrs.toml` 时 adrs 不再读 `.adr-dir`，目录会回到默认的 `doc/adr`。
- **不用自定义模板。** 实测自定义模板在 `--supersedes` 时生成了错误的链接行：链接文字和链接目标都只有旧 ADR 的编号，指向不存在的文件。用内置模板，再替换正文。
