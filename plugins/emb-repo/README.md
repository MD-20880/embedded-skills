# emb-repo · 项目 Repo 管理

维护嵌入式仓库的“地基”：项目画像、通用工程默认原则、受管理文件约定、目录与构建、文档索引和版本发布。

## 适用场景

- 项目首次接入 embedded-skills（先建项目画像）
- 新增板子 / 硬件版本 / 程序时按约定落位
- 保持 README 与文档索引和实际目录一致
- 发版时整理变更记录

## Skills

| Skill | 调用方式 | 状态 | 作用 |
| --- | --- | --- | --- |
| [project-profile](skills/project-profile/SKILL.md) | `/emb-repo:project-profile` | ✅ 已发布 | 建立 / 更新 / 核查项目画像 `docs/embedded-profile.md`，供所有 skills 共用 |
| [engineering-principles](skills/engineering-principles/SKILL.md) | `/emb-repo:engineering-principles` | ✅ 已发布 | 提供工程知识、假设与承诺、契约一致性、证据与交接原则；SessionStart/SubagentStart 注入精简原则 |
| [artifact-conventions](skills/artifact-conventions/SKILL.md) | `/emb-repo:artifact-conventions` | ✅ 已发布 | 定义受管理工程文件类型、项目 YAML 索引、身份与生命周期；普通文件保持轻量 |
| repo-layout | `/emb-repo:repo-layout` | 📝 规划中 | 梳理或执行目录与构建约定：新增板、硬件版本、程序时的落位与改动清单 |
| docs-index-sync | `/emb-repo:docs-index-sync` | 📝 规划中 | 检查并同步 README、文档索引与实际目录 |
| release-notes | `/emb-repo:release-notes` | 📝 规划中 | 整理版本变更记录与发布说明 |

> 状态说明：✅ 已发布（含评测用例）；📝 规划中（名称与范围可能调整）。新增 skill 的流程见仓库根目录 [CONTRIBUTING.md](../../CONTRIBUTING.md)。

## 默认原则自动加载

插件启用时，`hooks/hooks.json` 注册三个只读 hook：

| 时机 | 注入内容 | 大约体积 | 开关 |
| --- | --- | --- | --- |
| 会话开始（`SessionStart`） | 完整的 [轻量工程原则](skills/engineering-principles/references/core-principles.md)（7 条） | 约 2K 字符 | `inject_principles` |
| 子 Agent 启动（`SubagentStart`） | 一行精简版：7 条原则的标题 | 约 200 字符 | `inject_principles` |
| 编辑文件后（`PostToolUse`，Edit / Write） | 仅当改的是**启用了 hash 校验的受控文件**时：提示更新 hash，或提示该文件已冻结、应撤销 | 约 200 字符，其余情况不输出 | `integrity_reminders` |

hook 只读取插件自身文件和项目登记表，不审批、不拦截、不写入仓库、不访问网络。编辑提醒在编辑完成后才送达，所以它不能阻止编辑，只能让 Claude 立即补上 hash 或撤销；最终由项目 CI 把关。需要完整说明时，调用 `/emb-repo:engineering-principles`；普通编码任务不会因此被要求写管理报告。

### 关闭自动注入

所有领域插件都依赖 `emb-repo`，所以安装任何一个插件都会带上这些 hook。不需要时可以关闭：

- 在 Claude Code 中打开 `/config`，找到 `emb-repo` 的“自动注入工程原则 / Inject engineering principles”或“受控文件 hash 提醒 / Registry hash reminders”，设为关闭；或
- 在终端执行：`echo '{"inject_principles":"false"}' | claude plugin configure emb-repo@embedded-skills --values-stdin`（hash 提醒对应 `integrity_reminders`）

关闭原则注入后不再注入原则内容，`project-profile` 等 skill 不受影响，`/emb-repo:engineering-principles` 仍可手动调用。

### 运行要求

- **Python 3.8 及以上**：hook 经 `hooks/run-python.sh` 启动，依次尝试 `python3`、`python`、`py -3`，用第一个真正能运行的；只装了 python.org 版 Python（没有 `python3`）的 Windows 也能用。都不可用时，Claude Code 会显示 hook 错误，提醒你安装 Python。
- **Windows 需要 Git for Windows**：Claude Code 在 Windows 上通过 Git Bash 运行 hook 命令（Bash 工具同样需要它）。没有 Git Bash 时 hook 无法启动，会显示 hook 错误；不影响 skill 的手动调用。
- hook 读写一律按 UTF-8 处理，不受 Windows 中文系统本地编码（cp936 / GBK）影响；项目路径含中文也可以。

修改原则或 hook 后，运行 `python3 skills/engineering-principles/scripts/selfcheck.py` 检查两种输出、开关和体积上限（仓库 lint 也会自动运行它）。

## 受管理工程文件（Artifact Conventions）

创建需求、设计、ADR、协议、验证计划等工程文件时，先识别当前项目已声明的管理类型。符合类型的文件，默认在同一次变更中维护该项目**唯一的 YAML 工程文件登记入口**（推荐 `docs/engineering-artifacts.yaml`）；普通源码、脚本和随手笔记不被额外要求登记。

登记表管理稳定 ID、类型、相对路径、通用生命周期和适用范围；专业文件管理内容、专属批准状态及证据。可用 [示例](skills/artifact-conventions/assets/engineering-artifacts.example.yaml) 从零建立，但不要把示例当成已部署的项目事实。登记表不同于普通文档导航索引；细节见 `/emb-repo:artifact-conventions`。

**只有仓库中的文件才能登记。** 飞书、网盘、在线表格等外部系统中的内容不在管理范围内；需要纳管时，由负责人把文件或其导出快照提交进仓库后再登记，原链接可记在条目的 `source` 字段。

### 可选：受控文件 hash 校验

项目在登记表顶层声明 `integrity: sha256` 后，每个条目记录文件内容的 sha256，CI 用 `registry_check.py check --base <目标分支>` 发现受控文件的修改：

| 条目状态 | 文件改动后的要求 |
| --- | --- |
| `draft`、`active` | 在同一变更中运行 `registry_check.py update <id>` 更新 hash |
| `superseded`、`archived` | 冻结，不允许修改；应新建修订并用 `supersedes` 取代 |

- hash 只说明“受控文件变了”，不代表改动已批准；需要指定把关人时，配合 CODEOWNERS（模板见 `skills/artifact-conventions/assets/ci/`）。
- 启用步骤（复制工具与 CI 模板、写入基线）：[adoption-and-integration.md](skills/artifact-conventions/references/adoption-and-integration.md#启用完整性校验项目可选)；规则细节：[registry-format.md 第 6 节](skills/artifact-conventions/references/registry-format.md#6-完整性校验可选由项目启用)。
- 追溯与基线：`registry_check.py history <id>` 列出一份受控文件历次的改动（含改了文件却没更新登记的提交），`baseline --ref <标签>` 导出某个版本的受控基线清单；见 [registry-format.md 第 6.3 节](skills/artifact-conventions/references/registry-format.md#63-追溯与基线导出)。
- 未声明 `integrity` 的项目不受影响。

## 依赖的项目画像章节

全部章节（本插件负责生成画像）。画像规范见 [profile-spec](../emb-repo/skills/project-profile/references/profile-spec.md)；项目中尚无画像时，先运行 `/emb-repo:project-profile`。

## 安装

```text
/plugin marketplace add MD-20880/embedded-skills
/plugin install emb-repo@embedded-skills
```

## 版本

当前版本见 [.claude-plugin/plugin.json](.claude-plugin/plugin.json)，变更记录见 [CHANGELOG.md](CHANGELOG.md)。
