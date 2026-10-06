# emb-bringup · 板级 bring-up 与验证

新板到手后的系统化点亮与验证：先保证硬件可信，再让软件跑起来，并留下记录。

## 适用场景

- 新板或硬件改版首次上电
- 编写外设逐项验证程序
- 区分问题出在硬件还是软件
- 把验证 / 排查过程归档成可追溯的记录

## Skills

| Skill | 调用方式 | 状态 | 作用 |
| --- | --- | --- | --- |
| bringup-checklist | `/emb-bringup:bringup-checklist` | 📝 规划中 | 按电源→时钟→调试口→外设的顺序生成上电检查清单 |
| validation-program | `/emb-bringup:validation-program` | 📝 规划中 | 为某块板编写外设验证程序与通过判据 |
| hw-sw-triage | `/emb-bringup:hw-sw-triage` | 📝 规划中 | 软硬件问题定位：现象→假设→测量（示波器 / 逻辑分析仪）→结论 |
| validation-record | `/emb-bringup:validation-record` | 📝 规划中 | 按项目约定写验证 / 排查记录，并把结论回写到板的 README |

> 状态说明：✅ 已发布（含评测用例）；📝 规划中（名称与范围可能调整）。新增 skill 的流程见仓库根目录 [CONTRIBUTING.md](../../CONTRIBUTING.md)。

## 依赖的项目画像章节

2 硬件清单、4 构建与烧录、7 测试与验证、9 已知约束与坑。画像规范见 [profile-spec](../emb-repo/skills/project-profile/references/profile-spec.md)；项目中尚无画像时，先运行 `/emb-repo:project-profile`。

## 安装

```text
/plugin marketplace add MD-20880/embedded-skills
/plugin install emb-bringup@embedded-skills
```

## 版本

当前版本见 [.claude-plugin/plugin.json](.claude-plugin/plugin.json)，变更记录见 [CHANGELOG.md](CHANGELOG.md)。
