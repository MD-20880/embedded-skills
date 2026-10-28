# emb-project 变更记录

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.3.0] - 2026-10-28

### 新增

- `agent-tasks`：把里程碑或阶段目标拆成交给 AI agent 或人执行的执行 issue，并按清单验收交付。
  - 三层结构：里程碑、阶段、执行；一个执行 issue 只对应一个执行方、一个 PR，PR 写 `Refs` 不写 `Closes`。
  - 执行 issue 自包含（只引用仓库路径或正文）、范围写成目录、完成定义带单位和证据等级、有停止条件和规模上限；开发与实板测试分成两个 issue。
  - 实板交付：可复用的测试镜像、脚本、工具修复放正常目录按代码 PR 合入；一次运行一页记录（镜像 SHA-256 与提交、关键数据、判定、没覆盖、下一步）；原始日志不进仓库；不写占用时间线、逐文件哈希等过程信息。
  - 验收：结论只有通过、不通过、有条件通过；不自己验收自己；评审机器人意见先评估；验收清单含“没有新增无依据的门禁”。
  - `status:` 标签与 issue-tracking 四个状态对应。执行方名单、决策人、规模上限读项目自己的执行流程文档（画像第 8 节），不写进 skill。
  - 模板：`assets/templates/exec-task.md`（执行 issue）、`assets/templates/hw-record.md`（一页实板记录）。
  - 评测用例：`split-stage`（拆阶段、聊天里的决定要写进正文、开发与实板分开）、`accept-hw-pr`（源码在 zip、日志进仓库、记录过长、无依据的断链保护、`Closes`）、`no-trigger`。
  - 来源：一个多 agent 并行开发的嵌入式项目 2026-10-23 起实际运行的执行与验收流程，以及其中实板 PR“形式多、可复用少”的整改。

## [0.2.0] - 2026-10-06

### 变更

`issue-tracking` 同步原仓库 v0.5.0（[question-driven-tracking PR #2](https://github.com/MD-20880/question-driven-tracking/pull/2)）：

- 疑似有问题时，按有没有实测到的现象分类（method.md 第 3 章）：看到了现象，或按资料能确定是错的，开缺陷，原因不知道也开；只是担心有风险的，开验证，不通过再开缺陷；不确定算不算错的，开问题。取代原来“原因不明的异常先开根因问题”的规则。
- 缺陷分四步：现象 → 定位 → 处置 → 复测，始终是同一个 issue；根因确认之前不选处置方式（第 5.3 节）。
- 缺陷按归属分为待查、硬件缺陷、软件缺陷，标签 `defect:tbd`、`defect:hw`、`defect:sw`；归类是定位的结论，按根因定，不按修法定；硬件缺陷再分设计缺陷和个体缺陷。
- 三种归属共用一个缺陷模板和 GitHub 表单：新增“定位”段和“归属”字段，硬件、软件各自多写的行标为“仅硬件”“仅软件”。
- 处置表（第 6.3 节）标明每种处置用于哪类缺陷；新增关闭方式“符合预期”“无法复现”（第 6.2 节）。
- 总览新增“待定位”一组，阶段门禁单列还没定位的缺陷。

### 新增

- README 分工表：ADR 交给已发布的 `emb-design:adr-write`，问题 issue 的“决策记录”链接 ADR。
- 评测用例 `triage-symptom-vs-risk`：看到现象但原因不明的开成待定位缺陷，只是担心的风险开成验证。

本版本评测（各 1 次，`--ablation none`）：`close-check-checklist-done`、`gate-review-dvt`、`no-trigger-driver-code`、`triage-symptom-vs-risk` 均为 1.00。

## [0.1.0] - 2026-10-06

### 新增

- `issue-tracking`：从独立仓库 [MD-20880/question-driven-tracking](https://github.com/MD-20880/question-driven-tracking)（原名 `embedded-issue-tracking`，PR #1 的 v0.4.0，提交 `c7275b8`）迁入。方法内容不变，做了以下适配：
  - skill 名改为 `issue-tracking`，调用方式为 `/emb-project:issue-tracking`；
  - frontmatter 拆为中英 `description` 与 `when_to_use`；
  - 对接项目画像：适用对象与 `hw:` 标签按画像第 2 节的板与版本命名，当前阶段取自第 1 节，项目的 issue 管理映射文档登记在第 8 节；
  - 原 README 中的示例移入 `references/examples.md`；
  - `scripts/check.py` 改为 `scripts/selfcheck.py`，只保留本 skill 特有的检查（章节引用、skill 内路径、GitHub 表单、禁用词），通用检查由仓库 lint 负责；
  - 新增 3 个评测用例：复选框全勾仍不能关闭、DVT 阶段门禁、反向用例。

### 迁入前的历史（原仓库）

- v0.4.0：新增写作风格（method.md 第 15 章）：标题规则与正文九条；新增检查脚本与 CI。
- v0.3.0：新增关联与标签（method.md 第 14 章）：`[话题]` 前缀与父 issue，带前缀的标签分组。
- v0.2.0：定位为“嵌入式产品开发的 issue 管理方式”；四类 issue、四个共用字段、证据等级 L0–L4、EVT/DVT/PVT/MP、验证矩阵、三种总览、阶段门禁。
- v0.1.0：初版，以问题为导向的 issue 管理方式。
