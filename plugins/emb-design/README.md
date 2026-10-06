# emb-design · 方案设计

把模糊的产品需求变成可验证的技术方案：拆指标、比方案、算预算、记决策。

## 适用场景

- 新功能或新产品立项，需要从需求推导出技术指标
- 在几种 MCU / 通信方式 / 架构之间做选型
- 评估 Flash、RAM、CPU、功耗、带宽是否够用
- 需要留下可追溯的架构决策记录（ADR）

## Skills

| Skill | 调用方式 | 状态 | 作用 |
| --- | --- | --- | --- |
| requirements-breakdown | `/emb-design:requirements-breakdown` | 📝 规划中 | 把产品需求拆成可测量的技术指标与验收条件 |
| solution-compare | `/emb-design:solution-compare` | 📝 规划中 | 多方案对比与选型：评价维度、打分、风险与推荐 |
| resource-budget | `/emb-design:resource-budget` | 📝 规划中 | Flash / RAM / CPU / 功耗 / 带宽预算表与余量评估 |
| [adr-write](skills/adr-write/SKILL.md) | `/emb-design:adr-write` | ✅ 已发布 | 起草和维护架构决策记录：背景、决定（含被否决的方案）、影响；与 adrs 兼容的 Nygard 格式，取代、改状态、链接用 adrs 命令，每一步落地前由人确认 |

> 状态说明：✅ 已发布（含评测用例）；📝 规划中（名称与范围可能调整）。新增 skill 的流程见仓库根目录 [CONTRIBUTING.md](../../CONTRIBUTING.md)。

## 依赖的工具

`adr-write` 需要 [adrs](https://github.com/joshrotenberg/adrs) 命令行工具（`cargo install adrs` 或 `brew install adrs`）。没有安装时只能起草，不会写文件。

## 依赖的项目画像章节

1 项目概述、2 硬件清单、3 软件栈、8 文档约定、9 已知约束与坑。画像规范见 [profile-spec](../emb-repo/skills/project-profile/references/profile-spec.md)；项目中尚无画像时，先运行 `/emb-repo:project-profile`。

## 安装

```text
/plugin marketplace add MD-20880/embedded-skills
/plugin install emb-design@embedded-skills
```

## 版本

当前版本见 [.claude-plugin/plugin.json](.claude-plugin/plugin.json)，变更记录见 [CHANGELOG.md](CHANGELOG.md)。
