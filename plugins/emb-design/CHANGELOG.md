# emb-design 变更记录

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.2.0] - 2026-10-06

### 新增

- `adr-write`：起草和维护架构决策记录（ADR）。
  - 格式：Nygard 兼容模式，与 adrs、adr-tools 兼容；四个章节标题和状态词保留英文，正文用项目语言；末尾附“决策信息”（决策人、确认、关联 issue）。
  - 每一步落地前由人确认：新建、改状态、取代、链接、修改关联 issue。新建为 `Proposed`，决策人明确表态后才改为 `Accepted`。
  - Decision 中必须写被否决的方案及理由；尚未拍板的部分列为待决问题。
  - 必须安装 adrs；取代、改状态、链接都用 adrs 命令。`references/adrs-commands.md` 记录了 adrs 0.12.1 的实测行为和坑。
  - 评测用例：`supersede-needs-confirm`（推翻已有 ADR，且用户要求直接写）1.00、`no-trigger`（选型对比）1.00，各 1 次。

## [0.1.0] - 2026-10-06

### 新增

- 插件骨架与 skill 规划清单（尚无已发布 skill）。
