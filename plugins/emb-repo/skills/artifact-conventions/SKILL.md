---
name: artifact-conventions
description: 在创建、修改或整理工程文件时，辨别项目声明的受管理工程资产类型，说明 YAML 登记索引、稳定身份、状态、范围与生命周期的轻量约定，并指出需同步登记的文件。Recognize managed engineering artifact types and maintain a lightweight project registry of their identity and lifecycle.
when_to_use: 创建工程文档、增加协议规范、更新设计方案、登记 ADR、收录验证报告、迁移受管理文件、建立工程文件索引、整理项目的受管理资产类型、把文件设为受控或纳入文控时使用；"create a design document", "register an engineering artifact", "manage technical documents", "put a document under document control". 普通源码、临时脚本、随手笔记等不需要单独触发此 Skill。
argument-hint: "[新建/修改的文件或工程文件管理问题]"
allowed-tools: Read Glob Grep Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/registry_check.py check *) Bash(python3 tools/registry_check.py check *) Bash(python ${CLAUDE_SKILL_DIR}/scripts/registry_check.py check *) Bash(python tools/registry_check.py check *) Bash(py -3 ${CLAUDE_SKILL_DIR}/scripts/registry_check.py check *) Bash(py -3 tools/registry_check.py check *) Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/registry_check.py history *) Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/registry_check.py baseline *) Bash(python3 tools/registry_check.py history *) Bash(python3 tools/registry_check.py baseline *) Bash(python ${CLAUDE_SKILL_DIR}/scripts/registry_check.py history *) Bash(python ${CLAUDE_SKILL_DIR}/scripts/registry_check.py baseline *) Bash(python tools/registry_check.py history *) Bash(python tools/registry_check.py baseline *) Bash(py -3 ${CLAUDE_SKILL_DIR}/scripts/registry_check.py history *) Bash(py -3 ${CLAUDE_SKILL_DIR}/scripts/registry_check.py baseline *) Bash(py -3 tools/registry_check.py history *) Bash(py -3 tools/registry_check.py baseline *)
---

# 工程文件管理约定（artifact-conventions）

这是 **Inform + Principles** Skill，不是所有文件的生成器或审批器。创建或变更工程文件时，先判断它**在当前项目中是否属于受管理类型**；如果是，保持文件与项目 YAML 工程资产登记表一致；如果不是，不添加额外登记、审批或元数据要求。

**纳管的前提是文件在本仓库中。** 登记表只登记仓库内的文件；飞书、网盘、在线表格、厂商网站等外部系统中的内容不在本仓库的管理范围内，被讨论或引用过也不算。需要纳管时，由负责人把文件或其导出快照提交进仓库，再登记。未经用户明确要求，不代为从外部系统抓取内容入库，也不把外部链接登记为受管理条目；外部链接可以作为来源说明，写在受管理文件的正文或条目的 `source` 字段中。

- [登记表格式、字段、权威归属与生命周期](references/registry-format.md)（管理格式权威说明）
- [内置类型与项目扩展、非纳管边界](references/type-guide.md)
- [创建、修订、迁移与专业 Skills 集成](references/adoption-and-integration.md)
- [可复制的最小 YAML 示例](assets/engineering-artifacts.example.yaml)
- 完整性校验工具：`python3 ${CLAUDE_SKILL_DIR}/scripts/registry_check.py {check|update|hash|history|baseline}`（Windows 上没有 `python3` 时用 `python` 或 `py -3`）；项目 CI 模板见 `assets/ci/`

## 输入与产出

| 项 | 内容 |
| --- | --- |
| 输入 | 当前项目的 `docs/embedded-profile.md`、文档约定与现有工程文件登记表（如有）；正在创建/修改的文件及其用途、适用版本、现有审批依据 |
| 产出 | 简短判定（纳管/不纳管/待确认及理由）；对受管理文件，给出身份和生命周期约定、登记表中应新增或同步的条目；用户已授权创建文件时与文件一同更新登记 |
| 完成条件 | 已判断是否属于项目声明的管理类型；纳管文件可由项目唯一入口定位、状态不误导、范围明确；普通文件无额外管理负担 |

## 应用原则

### 1. 读取项目画像

1. **读取项目画像**：读取项目根目录 `docs/embedded-profile.md`。
   - 存在：以其中事实为准；只读取本任务需要的章节（优先第 1 节项目概述、第 5 节目录约定、第 8 节文档约定，必要时第 2、7 节硬件与验证）。若发现画像与代码不一致，以代码为准，并在结尾提示用户运行 `/emb-repo:project-profile update`。
   - 不存在：按需最小化探索仓库获取本任务所需事实，并在结尾建议用户运行 `/emb-repo:project-profile` 建立画像。不要因为缺少画像而中止任务。
2. 查找项目声明的 YAML 登记表，默认建议 `docs/engineering-artifacts.yaml`；项目已声明其他路径时遵循该路径。不可根据目录猜测登记表真实存在。
3. 识别项目当前已声明的文件类型及其识别条件；没有登记表时，先说明尚无正式管理入口。创建受管理文件的任务已获授权时，按 [registry-format.md](references/registry-format.md) 提议并建立**一份**入口，不另造平行台账；只讨论概念时不写文件。

### 2. 由文件的工程职责判断类型，而不是扩展名

1. 对照登记表 `types` 与 [type-guide.md](references/type-guide.md) 的常见类型：需求、外部依据、设计、ADR、协议/规范、验证；项目可声明更多类型，如风险分析、生产规范或校准记录。
2. 项目声明的受管理类型优先；即使一份文件是 `.md`，仅用于临时记录也不能据此强制纳管。已经承担正式契约/验收/外部依据职责的文件，不得因缺少既有登记而默认为普通文件。
3. 文件目标或适用范围含混时，列明假设并请用户确认，不擅自将草案升级为批准文件。详见 [type-guide.md](references/type-guide.md)。

### 3. 按最小必要方式建立或维护登记

1. 对新建的受管理文件，用稳定且未占用的 `id`、`type`、项目相对 `path`、通用 `status` 和非空 `scope` 注册。需要修订号的类型补 `revision`，其余关联信息按需增加，参照 [registry-format.md](references/registry-format.md)。
2. **受管理不等于已批准**：新草案可登记为 `draft`；`active` 不得由文件创建或测试存在自行推定。ADR 的 Proposed / Accepted / Superseded 等类型专属状态继续由 ADR 自身和其批准流程承载。
3. 受管理文件创建、改名、移动、修订、取代、归档时，**同一逻辑变更**中维护登记表；移动保留 ID，旧文件需要追溯时保留适当关系。未经授权的读取/建议任务仅提出变更，不编辑项目文件。
4. **登记表声明了 `integrity: sha256` 时**：修改受控文件后，在同一变更中运行 `registry_check.py update <id>` 写入新的 `sha256`（项目内若已有 `tools/registry_check.py` 则用项目副本），再运行 `check` 确认通过。规则：
   - 只为**本次有意修改**的文件更新 hash；`check` 报出的、不是本次任务改动的不一致要报告给用户，不能为了让 CI 变绿而顺手更新。
   - `superseded` / `archived` 文件已冻结：不要修改，也不要加 `--allow-frozen` 绕过；需要变更时提议新建修订并用 `supersedes` 取代。
   - 更新 hash 不代表批准，汇报时不要把“hash 已更新”说成“已审核”。
   - 用户要追溯某份受控文件的变化，或要留存某个版本的受控基线时，用只读的 `history <id>`、`baseline --ref <引用>`，见 [registry-format.md 第 6.3 节](references/registry-format.md#63-追溯与基线导出)；输出来自 git 历史，不代表批准记录。细则见 [registry-format.md 第 6 节](references/registry-format.md#6-完整性校验可选由项目启用)。
5. 外部资料（PDF、数据手册、原理图等）纳管时，原件放入仓库，登记其路径及厂商版本/修订号，不改动原件内容；原始下载地址等来源信息可记在 `source` 字段，必要时用关联的原始证据记录补充哈希。只存在于仓库外的资料不登记（见开头的纳管边界）。
6. 项目现有大量历史文件时，可逐步评估、补录；遗漏的管理类型文件作为一致性问题明确列出，不将 `artifacts: []` 伪称完整盘点，也不阻断无关开发。

### 4. 处理双重信息与状态冲突

1. 登记表是**受管理身份与索引入口**的权威：`id`、`type`、`path`、`scope` 和通用生命周期集中维护；文件或专业系统管理具体规范、原始证据、类型专属状态及正式批准依据。
2. 重复出现的状态信息不一致时，检查适用版本、类型状态映射与批准记录；**列为待确认**，不得默默把登记表或正文互相覆盖，更不得以登记表 `active` 取代 ADR 的 Accepted 决策流程。
3. 旧路径不存在、ID 重复、同一文档多处各自维护正式索引等异常应明确报告，但本 Skill 不执行强制门禁或全仓库治理任务。

### 5. 与其他 Skills 配合，保持轻量

1. `/emb-repo:engineering-principles` 说明工程认知；本 Skill 说明受管理文件的身份、类型、登记和生命周期，互不代替。
2. 创建具体 ADR 用 `/emb-design:adr-write`；处理 Issue 用 `/emb-project:issue-tracking`；协议、测试、索引编写交给项目已安装的对应专业能力。其他 Skill 创建受管理文件时可引用本约定，同时登记。
3. 新建或修订设计文档时，内容归属按 `/emb-repo:engineering-principles` 的文档边界判断：模块文档只写本模块，跨模块的合计、优先级和取舍放进联合文档并单独登记。
4. 对普通源码、构建脚本、临时日志、草图、临时笔记或未声明纳管的文件，不要求登记，也不要求使用某种模板。
5. 答复顺序：**是否纳管（依据）→ 登记位置/需同步的字段 → 尚需确认的状态或范围 → 必要的下一步**；普通任务只给出最简判断，不输出冗长流程报告。

## 自检

- [ ] 本项目至少有一个**明确的**登记入口（若缺失，已指出，而非假称存在）。
- [ ] 登记的条目都是仓库中的文件；没有把外部系统的链接或内容登记为受管理条目。
- [ ] 类型由用途和项目声明确定，没有把所有 Markdown 或测试文件一律纳管。
- [ ] `id/type/path/status/scope` 具备明确值，`revision` 遵循类型要求；未凭空编造批准状态。
- [ ] 索引中的每个路径与真实文件或明确的“待创建”动作一致；未静默遗失或覆盖其他条目。
- [ ] 启用了 `integrity` 的项目：本次修改的受控文件已更新 `sha256` 且 `check` 通过；未替与本任务无关或已冻结的文件更新 hash。
- [ ] 类型专属批准状态与登记表映射不矛盾，无法确认的冲突已披露。
- [ ] 未受管理的普通文件未被增加登记义务；项目既有规范与用户授权仍然优先。

## 约束

- 原则指导与文件创建任务中的**附带登记**，不是独立审批、管理 Agent 或自动迁移仓库。通用约定不强制 CI；项目通过 `integrity: sha256` 自愿启用 hash 检查后，按第 3 节维护 hash。
- 不擅自接受 ADR、批准协议、声称完成实板验证或更改原始外部资料。
- 不将通用案例中的项目路径、硬件参数、批准人或 ID 规则当成真实项目事实；没有证据就明确待确认。
