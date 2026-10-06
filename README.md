# embedded-skills

面向**嵌入式软件工程**的 Claude Code skills 集合。每个 skill 把嵌入式开发中的一类工作（写驱动、板级 bring-up、代码审查、协议文档、方案设计、仓库维护）沉淀成可复用、可评测、带版本的工作方法，在任何项目中安装后即可调用。

本仓库本身是一个 [Claude Code 插件市场](https://code.claude.com/docs/en/plugin-marketplaces)：按工作领域分成多个插件，按需安装。

## 快速开始

### 1. 安装

在任意项目的 Claude Code 会话中执行：

```text
/plugin marketplace add MD-20880/embedded-skills
/plugin install emb-repo@embedded-skills        # 基础插件：项目画像
/plugin install emb-drivers@embedded-skills     # 再按需安装其他领域插件
```

除 `emb-repo` 外的插件都依赖 `emb-repo`，安装时会自动一并安装。
如果希望团队成员打开项目就自动获得本市场，在项目根目录执行一次下面的命令，并提交生成的 `.claude/settings.json`：

```bash
claude plugin marketplace add MD-20880/embedded-skills --scope project
```

### 2. 为项目建立画像（首次必做）

```text
/emb-repo:project-profile
```

它会扫描仓库，生成 `docs/embedded-profile.md`。画像汇总 MCU 与板卡、构建与烧录命令、目录与编码约定等项目事实，每条都附来源；无法确定的内容会列成问题请你确认。之后所有 skill 都先读这份画像再工作，结果更稳定，也不必每次重新探索仓库。

### 3. 使用 skill

- **自动触发**：直接描述任务（如“帮我给 BMI270 写个 I2C 驱动”），Claude 会按 skill 的描述自动选用。
- **手动调用**：输入 `/<插件名>:<skill名>`，如 `/emb-repo:project-profile check`。

### 4. 更新

```text
/plugin marketplace update embedded-skills
```

也可以在 `/plugin` → Marketplaces 中为本市场开启自动更新。插件只有在版本号变化时才会更新。

## 插件目录

| 插件 | 领域 | 已发布 skill | 说明 |
| --- | --- | --- | --- |
| [emb-repo](plugins/emb-repo/README.md) | 项目 Repo 管理 | `project-profile` | 项目画像、目录与构建约定、文档索引、版本发布 |
| [emb-design](plugins/emb-design/README.md) | 方案设计 | — | 需求拆解、方案对比与选型、资源预算、ADR |
| [emb-drivers](plugins/emb-drivers/README.md) | 外设驱动开发 | — | 从手册到驱动、寄存器映射、跨 MCU 移植 |
| [emb-bringup](plugins/emb-bringup/README.md) | 板级 bring-up 与验证 | — | 上电清单、验证程序、软硬件问题定位、验证记录 |
| [emb-review](plugins/emb-review/README.md) | 嵌入式代码审查 | — | 中断与并发、内存与栈、可移植性专项审查 |
| [emb-docs](plugins/emb-docs/README.md) | 协议与设计文档 | — | 协议规范、测试向量、规范与实现一致性、交付文档 |

每个插件 README 列出了已发布和规划中的 skill。

## 仓库结构

```text
embedded-skills/
├── .claude-plugin/marketplace.json   # 市场目录：登记全部插件
├── plugins/<插件>/                   # 一个领域一个插件，插件名统一以 emb- 开头
│   ├── .claude-plugin/plugin.json    #   插件清单（含语义化版本号）
│   ├── README.md / CHANGELOG.md      #   插件说明、skill 清单、变更记录
│   ├── skills/<skill>/               #   SKILL.md + references/ + scripts/
│   └── evals/<skill>/<用例>/         #   claude plugin eval 评测用例
├── templates/                        # 新建 skill 与评测用例的模板
├── tools/                            # lint_skills.py（规范检查）、new_skill.py（脚手架）
├── docs/                             # 架构、编写规范、评测、发布流程
├── .claude/skills/new-skill/         # 本仓库专用：引导 Claude 和你一起沉淀新 skill
└── .github/workflows/                # CI：规范检查 + 官方校验；评测（手动触发）
```

## 核心约定

| 约定 | 内容 | 详见 |
| --- | --- | --- |
| 分层 | skill 只写**通用方法**；项目事实写在各项目的 `docs/embedded-profile.md` | [架构说明](docs/architecture.md) |
| 命名 | 插件 `emb-<领域>`，skill 用 kebab-case 动宾或名词短语，调用形如 `/emb-drivers:driver-port` | [编写规范](docs/authoring-guide.md) |
| 语言 | 正文中文；`description` 中英并列，提升自动触发命中率 | [编写规范](docs/authoring-guide.md) |
| 质量 | 每个 skill 至少一个正向和一个反向评测用例；PR 必须通过 lint 与官方校验 | [评测指南](docs/evals.md) |
| 版本 | 每个插件独立语义化版本，改动即升版本并写 CHANGELOG | [发布流程](docs/release.md) |

## 参与贡献

新增或修改 skill 的完整流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。在本仓库中打开 Claude Code，输入 `/new-skill`，Claude 会通过对话收集你的经验，然后起草 skill 和评测用例。

## 文档

- [文档索引](docs/README.md)
