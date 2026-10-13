# 在工程文件创建中应用 Artifact Conventions

本 Skill 是通用约定，不是取代各种文件生成器。创建工程文件的 Agent/Skill 在有相关项目上下文时，只需按下面的判断执行最小动作。

## 工作中的一次轻量判断

1. **看目标**：用户要写的是正式需求/设计/ADR/协议/验证，还是普通源码/临时笔记？
2. **看项目声明**：项目登记表 `types` 定义了哪些受管理类型，入口在哪里？没有表就说明尚未建立；只有用户要求创建文件/登记时才动手建立。
3. **受管理则同步**：文档放到项目约定目录；分配/沿用稳定 ID；登记 `type/path/status/scope`，修订号视类型要求而定。用户只是咨询时给建议，不擅自写库。
4. **非管理则退出**：正常创建原文件，不额外要求新索引项、元数据模板或审批步骤。
5. **遇到权限/审批边界**：保留 Draft 和真实证据的状态，不自行批准。若表内与文件不一致，标明冲突来源并请有权者确认。

这五步是**默认工程素养提示**，不是每次文件写入都要打印的五步报告。

## 与专业 Skill 的关系

| 专业能力 | 本约定提供什么 | 本约定不替代什么 |
| --- | --- | --- |
| `emb-design:adr-write` | 为 ADR 记录稳定身份、文件位置、抽象生命周期 | ADR 的决策、批准及 supersede 流程 |
| `emb-docs:protocol-spec`（规划中） | 类型与登记方法、草案/正式范围区别 | 协议内容、状态机及字段语义 |
| 验证/Bringup 专业 Skills | 验证计划与证据记录类型、scope、引用入口 | 真实测量、判据及是否通过 |
| `emb-repo:project-profile` | 从画像第 5/8 节理解目录和文档约定 | 画像的生成/维护 |
| `emb-repo:docs-index-sync`（规划中） | 与受管理登记表互相链接 | 普通 README/目录导航 |
| `emb-repo:engineering-principles` | 与工程事实、承诺与证据分离的原则一致 | 一般性的架构和工程管理素养 |

## 常见增量场景

**新建协议初稿**：由协议撰写者建立草案，登记为 `specification / draft`，不伪称评审通过；需关联的实施与测试可以之后补充。

**原理图更新修订**：项目内保留原始文件及 revision，登记项更新或新增版本化对象（遵循项目的 ID 政策）；不把二进制变成 Markdown。

**移动设计文件**：检查引用，更新登记路径，保持稳定 ID；如果原有文档实际上已被新方案取代，明确 supersedes 或等效关系。

**引入新类型**：例如量产校准记录，在 `types` 里声明辨别规则，再登记实例；无需修改 Skills 仓库。

**从历史项目迁移**：逐步补录，描述尚未清点的覆盖范围；不要求一口气把每个 README、Demo、脚本纳管，更不能靠猜测把历史材料标成 Active。

## 启用完整性校验（项目可选）

项目希望 CI 形式化检查受控文件的修改时，按以下步骤启用（建议通过一个单独的 PR 完成，并由项目负责人评审）：

1. 把 `scripts/registry_check.py` 复制到项目的 `tools/registry_check.py`。它是单文件、只依赖 PyYAML；`--version` 显示工具版本，文件头部注明来源，升级时整体替换。
2. 在登记表顶层加入 `integrity: sha256`，运行 `python3 tools/registry_check.py update --all` 写入全部 hash。此前请先确认现有受控文件的内容就是要作为基线的版本。
3. 复制 `assets/ci/artifact-integrity.yml` 到 `.github/workflows/`，它在每个 PR 上运行 `check --base <目标分支>`。GitLab 等其他平台按同样的命令改写。
4. 需要指定把关人时，参照 `assets/ci/CODEOWNERS.example`，为登记表和受控文件目录设置 CODEOWNERS，并在仓库设置中要求代码所有者审核。这一步可选。
5. 在项目画像第 8 节（文档约定）中写明“受控文件启用了 hash 校验，修改后运行 `tools/registry_check.py update <id>`”，方便人和 Agent 发现。

命令中的 `python3` 在 Windows 上可换成 `python` 或 `py -3`。`registry_check.py` 按 UTF-8 读写登记表，`update` 保留登记表原有的换行符（CRLF 或 LF），因此 Windows 与 Linux 上的开发者可以混用。

日常使用（安装了 `emb-repo` 插件时，Claude 编辑受控文件后会收到 `PostToolUse` 提醒，自动按下面的方式处理；人工修改时照做即可）：

- 修改受控文件 → `python3 tools/registry_check.py update <id>` → 与文件改动一起提交；
- CI 失败提示“内容与登记的 sha256 不一致” → 确认改动是有意的，再更新 hash；不是有意的，撤销改动；
- CI 失败提示“已冻结” → 不要修改归档或已被取代的文件，新建修订并用 `supersedes` 取代。

## 原则传播

`engineering-principles` 的会话级提醒只需提示“创建工程文件时检查项目受管理类型并在需要时引用 artifact-conventions”。其他具体文件技能在生成受管理类型时可按需阅读本约定。仅靠 Skill 描述无法保证所有外部 Agent/平台每次都自动触发；需依赖已启用的插件上下文和专业 Skill 的显式集成来提高覆盖，不宣称零遗漏。
