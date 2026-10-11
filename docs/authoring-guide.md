# Skill 编写规范

本文规定本仓库中 skill 的写法。目标是：Claude 能在正确的时机触发 skill，触发后按稳定的流程产出可交付的结果，维护者也能看懂、能修改。
带 **【lint】** 标记的条款由 `tools/lint_skills.py` 自动检查。

## 1. 归属与命名

### 1.1 选插件

| 工作内容 | 插件 |
| --- | --- |
| 立项、需求拆解、选型、资源预算、架构决策 | `emb-design` |
| 读芯片手册、写 / 移植外设驱动、总线抽象 | `emb-drivers` |
| 新板上电、验证程序、软硬件问题定位、验证记录 | `emb-bringup` |
| 审查代码中的嵌入式特有风险 | `emb-review` |
| 协议规范、测试向量、规范与实现一致性、交付文档 | `emb-docs` |
| issue 管理、验证矩阵、项目总览、阶段门禁、风险与变更管理 | `emb-project` |
| 项目画像、默认工程原则、目录与构建约定、文档索引、版本发布 | `emb-repo` |

跨领域的工作，按**主要产出物**归属：产出是驱动代码 → `emb-drivers`；产出是审查报告 → `emb-review`。

### 1.2 命名

- skill 名：kebab-case，用动宾或名词短语，说明“做什么”，不要写成“关于什么”。好：`driver-port`、`protocol-spec`；差：`i2c`、`helper`。**【lint】**
- 目录名与 frontmatter `name` 一致。**【lint】**
- 调用形式为 `/<插件>:<skill>`，起名时连起来读一遍，例如 `/emb-review:isr-concurrency-audit`。

### 1.3 粒度

一个 skill 对应**一个可交付的产出物**（一份驱动、一份审查报告、一份协议规范）。判断标准：

- 能用一句话说清输入和产出；
- 流程在 SKILL.md 的 500 行内写得下；
- 如果两个场景的流程有一半以上不同，就拆成两个 skill。

## 2. 目录结构

```text
skills/<skill>/
├── SKILL.md            # 必需：frontmatter + 流程与规则
├── references/         # 可选：检查清单、规范、术语、示例；SKILL.md 中按需链接
│   └── <topic>.md
├── scripts/            # 可选：确定性的辅助脚本，只用 Python 标准库
│   ├── <tool>.py
│   └── selfcheck.py    # 可选：本 skill 特有的开发期自检，lint 会自动运行
└── assets/             # 可选：供用户复制到项目中使用的模板、表单（不是给模型读的参考资料）
    └── ...
```

- 插件根目录不要放 `bin/`（claude.ai 组织同步会拒绝）。**【lint】**
- `scripts/selfcheck.py`：检查本 skill 特有的一致性（如章节引用、模板字段），失败时以非 0 退出并打印 `FAIL ...` 行；可使用 PyYAML。通用检查（frontmatter、链接、占位符）交给 `tools/lint_skills.py`，不要重复实现。
- 脚本在 SKILL.md 中用 `python3 ${CLAUDE_SKILL_DIR}/scripts/<tool>.py` 调用，不要写死绝对路径。
- 脚本必须是只读的，或者只写入明确告知用户的文件；不得执行构建、烧录或任何会改变设备状态的操作，除非这就是该 skill 的目的，且 skill 设置了 `disable-model-invocation: true`。

## 3. Frontmatter

```yaml
---
name: driver-port
description: 将外设驱动移植到新的 MCU 或 HAL：梳理移植层接口、替换总线与时基调用、给出验证步骤。Port a peripheral driver to a new MCU or HAL with a clear porting layer.
when_to_use: 换 MCU、换 SDK/HAL、复用其他项目的驱动时使用。触发语如“把这个驱动移植到 CH32”“适配新的 HAL”；"port this driver", "adapt driver to new MCU".
argument-hint: "[驱动路径] [目标平台]"
allowed-tools: Read Glob Grep
---
```

| 字段 | 要求 |
| --- | --- |
| `name` | 必填，与目录名一致 **【lint】** |
| `description` | 必填。**先写中文一句，再写英文一句**；先说做什么、产出什么，再说范围 **【lint：须同时包含中英文】** |
| `when_to_use` | 推荐。中文触发语 3~5 个 + 英文触发语 2~3 个，写用户会说的原话 |
| 长度 | `description` + `when_to_use` ≤ 1536 字符 **【lint】** |
| YAML 语法 | 值中出现英文冒号加空格（`: `）时，整个值要加引号，否则 frontmatter 解析失败 **【lint】** |
| `argument-hint` | 有参数时填写 |
| `allowed-tools` | 只预授权只读工具和该 skill 必需的脚本命令；不要预授权写文件、`git push` 等有副作用的操作 |
| `disable-model-invocation: true` | 有外部副作用（烧录、发布、推送）的 skill 必须设置，只允许用户手动调用 |
| 其他字段 | 只用 Claude Code 支持的字段，拼错会被静默忽略 **【lint：未知字段报错】** |

### 写好 description

description 决定 Claude 何时自动选用这个 skill，是最重要的一行。

- 写**任务和产出**，不写背景：好“从芯片手册提取寄存器与时序并生成驱动”；差“驱动开发相关的一些经验”。
- 写**边界**，避免与相邻 skill 抢触发：例如 `isr-concurrency-audit` 写明“只审查中断与并发，综合审查用 embedded-review”。
- 用**用户的说法**：用户说“点板子”“上电”，就把这些词写进 `when_to_use`。

## 4. 正文结构

正文按以下骨架组织（模板见 [templates/skill/SKILL.md](../templates/skill/SKILL.md)）：

1. **标题与一段话定位**：解决什么问题、产出什么、不做什么。
2. **输入与产出**：用表格写清楚。
3. **流程**：编号步骤。
   - 第一步固定为**读取项目画像**，直接使用 [profile-spec 第 6 节](../plugins/emb-repo/skills/project-profile/references/profile-spec.md#6-skill-如何消费画像写给-skill-作者) 给出的标准段落，并写明本 skill 需要哪些章节。**【lint：未提及画像时警告】**
   - 每一步写“做什么、怎么判断做完了”，不写背景故事。
   - 需要用户决策的地方明确写“向用户确认”。
   - 结论涉及“是否通过 / 是否成立”时，沿用 `emb-project:issue-tracking` 的证据等级 L0–L4 和适用对象写法（[method.md 第 7 章](../plugins/emb-project/skills/issue-tracking/references/method.md#7-证据等级)）。
4. **自检清单**：交付前逐项核对的检查项。
5. **汇报格式**：结论 → 产出物位置 → 待确认问题 → 建议的下一步。
6. **约束**：不做的事，以及哪些高风险操作需要用户确认。

### 写作要求

- **祈使句、可执行**：“读取链接脚本中的 MEMORY 段”，而不是“可以考虑看一下内存配置”。
- **给判断标准**：写“当……时，……”，不要只写“注意……”。
- **嵌入式的数值必须有来源**：寄存器地址、时序参数、容量、主频必须来自手册、代码或用户确认，skill 中要明确禁止猜测。
- **SKILL.md ≤ 500 行**，超出时把细节移到 `references/`。**【lint】**
- **不留占位符**：模板中的 `__…__` 必须全部替换。**【lint】**
- **相对链接必须有效**。**【lint】**

## 5. 安全与副作用

| 操作类型 | 要求 |
| --- | --- |
| 只读分析（读代码、读手册、生成报告） | 可以自动触发 |
| 写项目文件（生成驱动、文档） | 可以自动触发；产出路径在汇报中说明 |
| 烧录、擦除、改熔丝 / 选项字节、推送、发布 | 设置 `disable-model-invocation: true`，执行前逐项向用户确认 |
| 涉及密钥、账号、证书 | 不写入任何产出物，只引用其所在位置 |

### 插件 hook

插件级 hook（`hooks/hooks.json`）会在每个会话中自动运行，影响面远大于 skill。新增或修改 hook 前先读 [架构说明 4.8](architecture.md#48-插件-hook克制使用必须可关闭)，并满足：

- 使用 exec 形式（`command` + `args`），脚本路径以 `${CLAUDE_PLUGIN_ROOT}` 开头，只用 Python 标准库；
- 只读：不审批、不拦截工具调用、不写仓库、不访问网络；
- 提供 `userConfig` 布尔开关（默认值写明），关闭时脚本不输出任何内容；插件 README 写明关闭方法和运行要求；
- 注入文本有体积上限，并与 skill 引用同一份文件；
- 附带 `scripts/selfcheck.py`，覆盖各事件的输出格式、开关和体积上限。

## 6. 评测

每个 skill 至少需要：

- 一个**正向用例**：真实口吻的请求，检查 skill 被触发并且产出达标；
- 一个**反向用例**：相近但不该触发的请求，检查 skill 没有被调用。

写法与运行方式见 [评测指南](evals.md)。**【lint：缺少评测目录报错，缺少反向用例警告】**

## 7. 发布前检查清单

- [ ] `python3 tools/lint_skills.py` 无错误
- [ ] `claude plugin validate . --strict` 通过
- [ ] 正向、反向用例都至少本地跑过 1 次并通过
- [ ] 插件 README 的 Skills 表中状态为 ✅ 已发布，链接有效
- [ ] 插件 CHANGELOG 新增了版本条目，`plugin.json` 的版本已升级
