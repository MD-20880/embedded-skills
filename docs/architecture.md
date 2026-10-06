# 架构说明

本文说明 embedded-skills 的整体结构、各组成部分的职责，以及关键设计决策和理由。读完后应能回答：一个 skill 放在哪里、如何拿到项目信息、如何被安装和更新、如何保证质量。

## 1. 目标与边界

**目标**：把嵌入式软件开发中可重复的工作方法沉淀为 skill，让 Claude 在任何嵌入式项目中按一致、可验证的方式完成这些工作，并且这个集合能持续增长而不失控。

**边界**：

- skill 写的是**方法**：流程、检查清单、判断标准、模板、辅助脚本。
- skill 不写某个具体项目的事实（板子、引脚、命令）。这些事实属于各项目自己，记录在项目画像中。
- 本仓库不包含固件代码，也不负责构建或烧录任何设备。

## 2. 总体结构

```text
embedded-skills（本仓库 = 插件市场）
└── marketplace.json
    ├── emb-repo ─────── project-profile …   基础插件：生成与维护项目画像
    ├── emb-design   ┐
    ├── emb-drivers  │
    ├── emb-bringup  ├── 均依赖 emb-repo；需要项目事实时先读项目画像
    ├── emb-review   │
    ├── emb-docs     │
    └── emb-project  ┘
            │
            │ /plugin install
            ▼
某个嵌入式项目仓库
├── docs/embedded-profile.md   ← /emb-repo:project-profile 生成和维护；其他 skill 只读
└── 源码、构建配置、文档 …     ← 画像中每条事实都指向这里的来源
```

## 3. 组成部分

| 组成 | 位置 | 职责 |
| --- | --- | --- |
| 市场目录 | `.claude-plugin/marketplace.json` | 登记所有插件及其路径，用户通过它添加市场、安装插件 |
| 插件 | `plugins/emb-<领域>/` | 一个工作领域一个插件，可独立安装、独立版本 |
| skill | `plugins/<插件>/skills/<skill>/` | `SKILL.md`（流程与规则）+ `references/`（按需加载的细节）+ `scripts/`（确定性的辅助脚本）+ `assets/`（复制到项目中使用的模板、表单） |
| 评测用例 | `plugins/<插件>/evals/<skill>/<用例>/` | `claude plugin eval` 用例，验证 skill 能否被正确触发、产出是否达标 |
| 项目画像 | 使用方项目的 `docs/embedded-profile.md` | 项目事实的唯一汇总，所有 skill 共享 |
| 模板与工具 | `templates/`、`tools/` | 新建 skill 的骨架、仓库规范检查 |
| 仓库专用 skill | `.claude/skills/new-skill/` | 只在本仓库生效，引导通过对话沉淀新 skill |
| CI | `.github/workflows/` | PR 自动检查；评测手动触发 |

## 4. 关键设计决策

### 4.1 以插件市场分发，而不是复制文件

- **决策**：本仓库即插件市场，项目通过 `/plugin install` 使用。
- **理由**：一处维护、多项目共享；有版本号，可以控制何时更新、出问题时可以回溯；不同项目可以只装需要的领域。
- **代价**：使用方需要能访问本仓库（私有仓库要求本机 git 凭据可用）。

### 4.2 按工作领域拆分为多个插件

- **决策**：7 个插件 `emb-design / emb-drivers / emb-bringup / emb-review / emb-docs / emb-project / emb-repo`。
- **理由**：skill 数量增长后仍然好找；每个插件独立版本，改动影响面小；插件名就是调用前缀，`/emb-drivers:driver-port` 一眼可知领域。
- **命名前缀 `emb-`**：插件名是全局命名空间，加前缀可以避免与用户安装的其他插件（如通用的 `docs`、`review`）冲突。
- **新增领域的门槛**：现有插件都放不下，且预计会有 3 个以上 skill 时，才新建插件。

### 4.3 项目画像：方法与事实分离

- **决策**：项目事实统一写进使用方项目的 `docs/embedded-profile.md`，由 `emb-repo:project-profile` 生成和维护；其他 skill 只读。
- **理由**：
  - skill 保持通用，可以跨项目复用；
  - 不必每个 skill 每次重新探索仓库，结果更稳定，也更省上下文；
  - 每条事实都带来源，可以复核；无法确定的内容显式列为“待确认”，避免模型猜测型号、容量这类关键数值。
- **为什么放在 `docs/` 而不是 `.claude/`**：`.claude/` 是 Claude Code 的受保护目录，写入总需人工确认，自动化和评测场景中会被直接拒绝；而且画像本身也是一份适合新成员阅读的项目速览。
- **降级策略**：画像不存在时，skill 仍然完成任务（按需最小化探索仓库），并在结尾建议建立画像。
- **规范位置**：[profile-spec.md](../plugins/emb-repo/skills/project-profile/references/profile-spec.md) 是唯一权威定义。
- **依赖声明**：其他 6 个插件在 `marketplace.json` 的插件条目中声明依赖 `emb-repo`，安装任一领域插件时自动装上画像能力。依赖**不写在 `plugin.json`**：`claude plugin eval` 按路径评测时只加载被测插件，`plugin.json` 中声明的依赖无法满足，会导致被测插件整个不被加载（已实测）；写在市场条目中则只在通过市场安装时生效。**【lint】**

### 4.4 渐进式披露

- **决策**：`SKILL.md` ≤ 500 行，只写流程与规则；细节放 `references/`，确定性的工作放 `scripts/`。
- **理由**：skill 的描述常驻上下文，正文在调用时加载，references 只在需要时读取，上下文开销按需增长。脚本只输出结果、不占上下文，结果也可复现。

### 4.5 中文正文 + 中英描述

- **决策**：正文用中文；`description` 与 `when_to_use` 同时写中文和英文触发语。
- **理由**：正文与维护者的工作语言一致；用户的提问可能是中文、英文或中英混杂，双语描述可以提高自动触发命中率。

### 4.6 质量保障分三层

| 层 | 工具 | 时机 | 检查什么 |
| --- | --- | --- | --- |
| 结构 | `claude plugin validate --strict` | 每个 PR（CI） | 清单与 frontmatter 是否符合 Claude Code schema |
| 规范 | `tools/lint_skills.py` | 每个 PR（CI） | 本仓库约定：命名、中英描述、行数、评测完整性、链接、版本升级 |
| 行为 | `claude plugin eval` | 本地或手动触发 CI | 是否正确触发、是否误触发、产出是否达标 |

行为评测会调用模型、产生费用，因此不在每个 PR 上自动运行。

### 4.7 每插件独立语义化版本

- **决策**：版本号只写在各插件的 `plugin.json`，配合插件 CHANGELOG；CI 强制要求改动过的插件必须升版本。
- **理由**：使用方只有在版本变化时才会收到更新，所以写到一半的修改不会推到使用方；版本与 CHANGELOG 对应，可以回溯每次变更。

## 5. 一次典型使用的数据流

1. 用户在项目中说“帮我给 BMI270 写 I2C 驱动”。
2. Claude 根据描述选用 `emb-drivers:driver-from-datasheet`。
3. skill 第一步读取 `docs/embedded-profile.md` 的第 2、3、5、6 节，得到 MCU、HAL、驱动目录约定和编码约定。
4. skill 按自己的流程读取芯片手册，产出驱动；遇到画像中“待确认”的内容，先向用户确认。
5. 如果发现画像与代码不一致，以代码为准完成任务，并提示用户运行 `/emb-repo:project-profile update`。

## 6. 演进方向

- **共享概念**：`emb-project:issue-tracking` 定义的证据等级（L0–L4）和“结论绑定适用对象（板、硬件版本、固件版本）”适用于整个集合。后续 `emb-bringup`、`emb-review` 的 skill 在给出结论时沿用同一套等级与写法，引用 [method.md 第 7 章](../plugins/emb-project/skills/issue-tracking/references/method.md#7-证据等级)，不另起定义。
- 积累到一定数量的 skill 后，评估是否增加跨插件的 agent（如串起“方案→驱动→验证→文档”的端到端流程）。
- 当多个 skill 共享同一份参考资料（如通用的嵌入式审查清单）时，放在被依赖插件中，通过符号链接共享（市场内的符号链接在安装时会被解引用复制）。
