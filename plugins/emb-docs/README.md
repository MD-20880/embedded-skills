# emb-docs · 协议与设计文档

写出可交付、可验证的协议与设计文档，并保证文档与实现一致。

## 适用场景

- 定义板间 / 设备间通信协议
- 为协议生成测试向量与校验脚本
- 检查规范与代码实现是否一致
- 编写交付、验收类文档

## Skills

| Skill | 调用方式 | 状态 | 作用 |
| --- | --- | --- | --- |
| protocol-spec | `/emb-docs:protocol-spec` | 📝 规划中 | 编写协议规范：帧格式、字段、状态机、时序、错误处理、版本演进 |
| test-vectors | `/emb-docs:test-vectors` | 📝 规划中 | 从协议规范生成测试向量与自动校验脚本 |
| spec-impl-consistency | `/emb-docs:spec-impl-consistency` | 📝 规划中 | 逐条比对规范与实现，输出差异清单 |
| delivery-doc | `/emb-docs:delivery-doc` | 📝 规划中 | 编写交付与验收文档：范围、验收项、判据、记录模板 |

> 状态说明：✅ 已发布（含评测用例）；📝 规划中（名称与范围可能调整）。新增 skill 的流程见仓库根目录 [CONTRIBUTING.md](../../CONTRIBUTING.md)。

## 依赖的项目画像章节

1 项目概述、5 目录约定、8 文档约定。画像规范见 [profile-spec](../emb-repo/skills/project-profile/references/profile-spec.md)；项目中尚无画像时，先运行 `/emb-repo:project-profile`。

## 安装

```text
/plugin marketplace add MD-20880/embedded-skills
/plugin install emb-docs@embedded-skills
```

## 版本

当前版本见 [.claude-plugin/plugin.json](.claude-plugin/plugin.json)，变更记录见 [CHANGELOG.md](CHANGELOG.md)。
