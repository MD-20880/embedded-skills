---
name: adr-write
description: 起草和维护架构决策记录（ADR）：从讨论和 issue 中整理背景、决定（含被否决的方案）与影响，生成与 adrs、adr-tools 兼容的 Nygard 格式文件；取代、废弃、改状态和链接都用 adrs 命令完成，每一步落地前由人确认。Draft and maintain adrs-compatible Nygard ADRs; every file change waits for human confirmation.
when_to_use: 出现出厂或实现后很难改的决定（硬件选型、Bootloader 读的格式、分区、板间协议），或跨多块板、多个模块的决定，以及要推翻或修改已有决定时使用。触发语如“把这个决定记下来”“写个 ADR”“这个方案定了”“之前那个决定作废”“改成 Accepted”；"write an ADR", "record this decision", "supersede ADR 3".
argument-hint: "[要记录的决定，或 ADR 编号与操作]"
allowed-tools: Read Glob Grep Bash(adrs --version) Bash(adrs config) Bash(adrs list*) Bash(adrs doctor*)
---

# 架构决策记录（adr-write）

把一个已经做出或正在做出的决定，写成可追溯的 ADR，并维护已有 ADR 的状态和关系。产出是项目 ADR 目录中的 Nygard 格式文件，与 [adrs](https://github.com/joshrotenberg/adrs) 和 adr-tools 兼容。

**ADR 由人拍板。** 本 skill 可以自动触发，但只负责起草：新建文件、改状态、取代、废弃、链接、修改关联 issue，每一步都先把内容给人看，得到明确确认后才执行。状态只能先写 `Proposed`；决策人明确表态后才改为 `Accepted`。

不做的事：方案对比和打分（交给 `emb-design:solution-compare`）；判断问题 issue 能否关闭（交给 `emb-project:issue-tracking`）；在项目中初始化 ADR 目录；把历史 issue 批量回填成 ADR。

- 格式规则：[references/format.md](references/format.md)
- adrs 命令与实测行为：[references/adrs-commands.md](references/adrs-commands.md)
- 完整示例：[references/example.md](references/example.md)

## 输入与产出

| 项 | 说明 |
| --- | --- |
| 输入 | 用户描述的决定；相关讨论、问题 issue、设计文档；已有 ADR |
| 产出 | 回复中的 ADR 草稿和拟执行命令；确认后，ADR 目录中新建或修改的文件，以及问题 issue 中指向 ADR 的链接 |

## 流程

### 1. 读取项目画像

读取项目根目录 `docs/embedded-profile.md`。
- 存在：以其中事实为准；只读取本任务需要的章节（1 项目概述、8 文档约定）。若发现画像与代码不一致，以代码为准，并在结尾提示用户运行 `/emb-repo:project-profile update`。
- 不存在：按需最小化探索仓库获取本任务所需事实，并在结尾建议用户运行 `/emb-repo:project-profile` 建立画像。不要因为缺少画像而中止任务。

### 2. 找到 ADR 目录和已有 ADR

1. 按顺序查找配置：项目根目录的 `adrs.toml`（读 `adr_dir`）、`.adrs.toml`、`.adr-dir`。有 `adrs.toml` 时以它为准，`.adr-dir` 会被忽略。
2. 都没有时：告诉用户项目还没有 ADR 目录，询问是否先建立。本 skill 不负责初始化，不要自行创建。
3. 列出目录中的 `NNNN-*.md`，读每个文件的标题行和 `## Status` 一节。
4. 判断这次是新建、取代、修改还是只改状态：
   - 新决定推翻或替换了某个已有 ADR → 取代该 ADR，不要另起一份互相矛盾的记录；
   - 新决定只修改或补充已有 ADR → 新建并用链接关联（如 `Amends`）；
   - 只是状态变化（确认、废弃、拒绝）→ 只改状态，不新建。

### 3. 判断是否需要 ADR

需要写 ADR 的决定，至少满足一条：

- 出厂或实现后很难改：硬件选型、Bootloader 读取的格式、分区、板间或对外协议；
- 跨多块板或多个模块：一处改动会牵连其他板、协议或团队。

都不满足时，告诉用户原因，建议把决定记在对应的 issue 里。用户仍要求写，照常写。

### 4. 收集内容

逐项收集，缺的写“待定，由谁定”，不要编造：

| 内容 | 来源 |
| --- | --- |
| 背景：要解决什么、有哪些约束 | 讨论、问题 issue、设计文档；事实标“实测（Lx）”“推断”“待查” |
| 决定：选了什么 | 用户的原话；不清楚就问 |
| 被否决的方案及理由 | 讨论中出现过的其他方案；没有出现过就写“讨论中没有其他方案” |
| 影响：哪些文档、issue、硬件或固件要跟着改；带来哪些新的待决问题 | 搜索仓库和 issue 中引用该主题的地方 |
| 决策人、关联 issue | 用户提供；不知道就问 |

决定中尚未拍板的部分，不写进 Decision；列为“待决问题”放进 Consequences，并建议另开问题 issue。

### 5. 起草，给人确认

在回复中给出：

1. 完整的 ADR 草稿，按 [references/format.md](references/format.md) 的骨架；状态为 `Proposed`；
2. 文件名（建议用 ASCII，见 format.md 第 4 节）；
3. 拟执行的命令，逐条列出，例如 `adrs new --no-edit --supersedes 2 "plan-without-vendor-stack"`；
4. 拟修改的关联 issue 内容；
5. 明确的问题：“确认后我执行以上命令吗？”

没有得到明确确认，不执行任何写操作。用户修改草稿后，重新给出修改后的版本再确认。

### 6. 执行（确认之后）

1. 运行 `adrs --version`。没有安装时停下，告诉用户安装方法（`cargo install adrs` 或 `brew install adrs`），不要手写文件代替。
2. 运行 `adrs config`，确认 ADR 目录与第 2 步一致、`Mode: Compatible`。不一致时停下，向用户报告。
3. 按确认过的命令执行。新建一律加 `--no-edit`，否则会打开编辑器并卡住。
4. 用确认过的草稿替换新文件中的模板占位文字。只改正文，不改 `# N. 标题` 行格式、`Date:` 行和四个英文章节标题；如果要用中文标题，只改标题行中 `N. ` 之后的文字。
5. 状态变化用 `adrs status`，取代用 `adrs new --supersedes`，关联用 `adrs link`。不要手改状态行和链接行。
6. 运行 `adrs doctor`，并重新读取改动过的文件，确认状态行和链接行符合预期（见第 7 步）。
7. 按确认过的内容修改关联的问题 issue：在“决策记录”中链接 ADR 文件。

### 7. 自检

- [ ] 每个写操作之前都有人明确确认
- [ ] 状态：新建为 `Proposed`；`Accepted` 只在决策人明确表态后设置，并在“决策信息”中写明谁、何时确认
- [ ] 四个章节标题是英文原文：`## Status`、`## Context`、`## Decision`、`## Consequences`；状态词是英文
- [ ] Decision 中写了被否决的方案及理由
- [ ] “决策信息”写了决策人和关联 issue；问题 issue 中有指向 ADR 的链接
- [ ] 推翻已有决定时用了取代，旧 ADR 的状态已变为 `Superseded` 并带链接
- [ ] 改动后重新读取过文件：`adrs status` 改中文标题的文件会静默失败，必须读回确认
- [ ] 没有编造日期、决策人、数值或结论；未定的写成待决问题

### 8. 汇报

1. 结论：起草了什么，或执行了哪些操作；
2. 产出：文件路径、状态、与其他 ADR 的关系；
3. 待确认：仍需人拍板的事项（例如把 `Proposed` 改为 `Accepted`）；
4. 下一步：Consequences 中列出的、需要另开 issue 或修改文档的地方。

## 约束

- 任何写 ADR 文件、改状态、取代、链接、改 issue 的操作，都要先得到人的明确确认。用户在请求中预先说“直接写”，也要先展示草稿。
- 不替人做决定：用户没有明确表态的选择，不写成决定；`Accepted` 必须来自决策人。
- 没有安装 adrs 时不写文件。
- 不修改已经 `Accepted` 的 ADR 的 Context 和 Decision；要改决定，用取代。
- 不删除 ADR 文件；作废用 `deprecated`、`rejected` 或取代。
