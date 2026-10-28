---
name: agent-tasks
description: 把 milestone 或阶段目标拆成可交给 AI agent 或人执行的执行 issue，并按清单验收执行方交付的 PR 和实板记录：一个执行 issue 一个 PR、范围写成目录、开发与实板测试分开、不自己验收自己。Break milestones into self-contained execution issues for AI agents or people, and accept their PRs and hardware-run records against a checklist.
when_to_use: 要把阶段目标拆给 Codex、Claude 等 agent 或同事执行，或要验收执行方交上来的 PR、实板测试记录时使用。触发语如“把这个阶段拆成 agent 能做的 issue”“写一个给 Codex 的执行 issue”“验收这个 PR”“这个实板 PR 能合吗”“执行 issue 怎么写”；"split this milestone into agent tasks", "write an execution issue for an agent", "review this agent PR for acceptance". issue 类型判定与关闭用 issue-tracking，ADR 用 adr-write。
argument-hint: "[阶段 issue、执行 issue 或 PR]"
allowed-tools: Read Glob Grep
---

# 交给 agent 执行与验收（agent-tasks）

多个 AI agent 和人并行开发时，最常见的失败是：执行方看不到聊天记录就猜、PR 越做越大、开发和实板测试混在一起说不清证据、谁写的谁就说通过、实板产出的镜像源码只在压缩包里。本 skill 解决两件事：**把目标拆成执行方拿到就能做的执行 issue**，以及**按固定清单验收交付物**。

它不做：issue 类型判定和关闭规则（`/emb-project:issue-tracking`）；架构取舍记录（`/emb-design:adr-write`）；派发和合并（由决策人做）。

- 完整做法：[references/method.md](references/method.md)
- 执行 issue 模板：[assets/templates/exec-task.md](assets/templates/exec-task.md)
- 实板记录模板：[assets/templates/hw-record.md](assets/templates/hw-record.md)

## 输入与产出

| 项 | 说明 |
| --- | --- |
| 输入 | 阶段 issue 或 milestone 目标；相关规范、接口头文件的仓库路径与提交号；项目的执行流程文档（如有）；待验收的 PR 或记录 |
| 产出 | 起草：执行 issue 正文（模板）、建议的执行方和标签；验收：结论（通过 / 不通过 / 有条件通过）、PR 上的缺失项评论、issue 上“做了 / 结果 / 下一步”三行 |
| 完成条件 | 执行 issue 自包含且可直接检验；验收结论逐项对照清单，有证据，有等级 |

## 流程

### 1. 读取项目画像和项目约定

1. 读取项目根目录 `docs/embedded-profile.md`。
   - 存在：以其中事实为准；只读本任务需要的章节：第 2 节（板与硬件版本命名，写“适用对象”）、第 4 节（构建命令）、第 5 节（目录约定，写“范围”）、第 7 节（测试与验证、记录放哪里）、第 8 节（文档约定，查找项目的执行流程文档）。若发现画像与代码不一致，以代码为准，并在结尾提示用户运行 `/emb-repo:project-profile update`。
   - 不存在：按需最小化探索仓库获取本任务所需事实，并在结尾建议用户运行 `/emb-repo:project-profile` 建立画像。不要因为缺少画像而中止任务。
2. 查找项目自己的执行流程文档（画像第 8 节登记的，或 `docs/` 下的 agent 工作流文档）和执行 issue 模板。项目已有约定时按项目的：执行方名单与分工、规模上限、标签名、决策人。没有时用 [method.md](references/method.md) 的默认值，并告诉用户这些是默认值。
3. 执行方名单、决策人、规模上限这类项目事实不写回本 skill。

### 2. 起草执行 issue

1. 确认上级：执行 issue 挂在一个阶段 issue 下（[method.md 第 1 节](references/method.md#1-三层结构)）。阶段 issue 本身不直接派给执行方。
2. 切分：一个执行 issue 只对应一个执行方、一个 PR。按下面的标准拆：
   - 需要实板证据（L2 及以上）的，开发和实板测试拆成两个 issue，即使同一执行方完成；
   - 预计超过项目规模上限（默认不含 vendor 约 1500 行）的，拆；
   - 范围跨了两个互不依赖的目录组的，拆。
3. 用 [exec-task.md](assets/templates/exec-task.md) 写正文，逐项满足：
   - **自包含**：执行方只能看到仓库和 issue。输入只列仓库内路径（必要时带提交号），需要的数值连同来源抄进正文；不写“见聊天记录”或仓库外的文件。
   - **范围写成目录**：“允许改动”“允许新增”列出目录，其余一律范围外。
   - **完成定义可直接检验**：数值带单位和条件，写明要求的证据等级（沿用 issue-tracking 的 L0–L4，[method.md 第 7 章](../issue-tracking/references/method.md#7-证据等级)）。
   - **停止条件**：契约或字段不清、硬件行为未知、要改范围外文件或接口、规模超限时，评论提问后等待。
   - **起点**：基于哪个分支和提交，分支名，PR 目标分支。
4. 标题写成 `[话题] 动宾短语`，话题沿用阶段 issue 的前缀。
5. 建议执行方：按项目的分工表；没有时按任务性质给建议（[method.md 第 2 节](references/method.md#2-角色)），由决策人派发时决定。
6. 不加没有依据的限制。执行 issue 里的“不许做”只写范围外目录、接口契约和项目已有规则；不为“以防万一”加额外门禁。
7. 把标题、正文、标签、建议执行方给用户看，确认后再创建。

### 3. 验收交付

1. 读执行 issue 的完成定义和范围，再读 PR 的改动、正文和关联记录。
2. 能在主机上重跑的测试自己重跑，对照 PR 正文所述结果。
3. 逐项核对 [method.md 第 6.2 节](references/method.md#62-验收清单) 的验收清单。重点：
   - 改动只在允许的目录内；规模在上限内；
   - 每条完成定义都有证据，等级不低于要求；编译通过和主机测试不充当实板结果；
   - 没有改协议或接口，需要改的事先经决策人同意；
   - 实板交付按 [method.md 第 5 节](references/method.md#5-实板交付可复用的进仓库过程不进)：可复用的镜像源码、脚本、工具修复在正常目录、可合入；记录一页；原始日志不进仓库；
   - 没有新增无依据的门禁、锁止、上限。
4. 给出结论，只有三种：**通过**、**不通过**、**有条件通过**（写明限制和确认人）。
   - PR 上评论缺什么、在哪里；
   - issue 上评论三行：“做了：”“结果：”“下一步：”。
5. 验收者不能是执行者本人。自己起草并执行的 PR，按清单自查写进 PR，交另一个执行方交叉审核，由决策人合并。
6. 评审机器人的意见不自动视为缺陷：先评估，在 PR 上回复，涉及协议或方向的交决策人。
7. 合并后（由决策人合并）：填写执行 issue 的“交付记录”，以“已完成”关闭，勾选阶段 issue 对应的完成定义；改了 issue 正文时，在下方评论说明改了什么。

### 4. 自检

- [ ] 执行 issue 只引用仓库内路径或正文内容，没有“见聊天”或外部文件依赖。
- [ ] 范围列成目录；完成定义带单位、条件和证据等级。
- [ ] 需要实板的工作拆成了开发和实板测试两个 issue。
- [ ] 项目事实（执行方、决策人、上限）来自项目文档或用户，用了默认值的已说明。
- [ ] 验收结论是三种之一，每条依据都指向 PR 或记录中的具体位置。
- [ ] 没有把编译通过、主机测试当作实板结果；没有自己验收自己。
- [ ] 外部写操作（建 issue、评论、改标签）都经用户确认。

### 5. 汇报

结论（起草了几个执行 issue / 验收结论）→ 产出位置（issue 草稿或评论链接）→ 待确认的问题（执行方、门槛、偏离）→ 建议的下一步。

## 约束

- 不派发、不合并、不放行阶段门禁：这些由决策人做。
- 新建、编辑、关闭 issue，打标签，在 PR 或 issue 上评论，先给用户看内容，确认后执行。别人创建的 issue 和 PR，没有授权不改正文。
- 不改协议、接口定义和已批准的设计；需要时停下提问。
- 门槛、数值、硬件参数不知道时写“待定，由谁定”，不猜。
