# emb-review · 嵌入式代码审查

针对嵌入式特有风险的代码审查：中断与并发、内存与栈、时序、可移植性。

## 适用场景

- 合入前审查固件改动
- 排查偶发死机、数据错乱等疑似并发问题
- 评估栈与内存使用是否安全
- 检查代码在多 MCU / 多编译器下的可移植性

## Skills

| Skill | 调用方式 | 状态 | 作用 |
| --- | --- | --- | --- |
| embedded-review | `/emb-review:embedded-review` | 📝 规划中 | 综合审查：按嵌入式风险清单逐项检查改动并分级输出 |
| isr-concurrency-audit | `/emb-review:isr-concurrency-audit` | 📝 规划中 | 中断与并发专项：共享数据、临界区、volatile、重入 |
| memory-stack-audit | `/emb-review:memory-stack-audit` | 📝 规划中 | 内存与栈专项：栈深度、静态分配、越界、对齐 |
| portability-check | `/emb-review:portability-check` | 📝 规划中 | 可移植性专项：字节序、类型宽度、编译器扩展、HAL 依赖 |

> 状态说明：✅ 已发布（含评测用例）；📝 规划中（名称与范围可能调整）。新增 skill 的流程见仓库根目录 [CONTRIBUTING.md](../../CONTRIBUTING.md)。

## 依赖的项目画像章节

3 软件栈、6 编码约定、7 测试与验证、9 已知约束与坑。画像规范见 [profile-spec](../emb-repo/skills/project-profile/references/profile-spec.md)；项目中尚无画像时，先运行 `/emb-repo:project-profile`。

## 安装

```text
/plugin marketplace add MD-20880/embedded-skills
/plugin install emb-review@embedded-skills
```

## 版本

当前版本见 [.claude-plugin/plugin.json](.claude-plugin/plugin.json)，变更记录见 [CHANGELOG.md](CHANGELOG.md)。
