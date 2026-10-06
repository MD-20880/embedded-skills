# emb-project 变更记录

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

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
