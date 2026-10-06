# emb-drivers · 外设驱动开发

从芯片手册到可用驱动：提取寄存器与时序、生成驱动骨架、做跨 MCU 移植。

## 适用场景

- 为新外设芯片（传感器、显示、音频、射频等）编写驱动
- 从 datasheet 提取寄存器表、命令集、时序要求
- 把已有驱动移植到另一颗 MCU 或另一套 HAL
- 为驱动设计可移植的总线抽象层（I2C / SPI / UART）

## Skills

| Skill | 调用方式 | 状态 | 作用 |
| --- | --- | --- | --- |
| driver-from-datasheet | `/emb-drivers:driver-from-datasheet` | 📝 规划中 | 阅读芯片手册，产出寄存器表、初始化序列与驱动实现 |
| register-map-gen | `/emb-drivers:register-map-gen` | 📝 规划中 | 从手册表格生成寄存器 / 位域头文件，并给出校验方法 |
| driver-port | `/emb-drivers:driver-port` | 📝 规划中 | 将驱动移植到新 MCU / HAL，梳理需要适配的移植层接口 |
| bus-abstraction | `/emb-drivers:bus-abstraction` | 📝 规划中 | 设计或审查 I2C / SPI / UART 总线抽象与错误处理 |

> 状态说明：✅ 已发布（含评测用例）；📝 规划中（名称与范围可能调整）。新增 skill 的流程见仓库根目录 [CONTRIBUTING.md](../../CONTRIBUTING.md)。

## 依赖的项目画像章节

2 硬件清单、3 软件栈、5 目录约定、6 编码约定。画像规范见 [profile-spec](../emb-repo/skills/project-profile/references/profile-spec.md)；项目中尚无画像时，先运行 `/emb-repo:project-profile`。

## 安装

```text
/plugin marketplace add MD-20880/embedded-skills
/plugin install emb-drivers@embedded-skills
```

## 版本

当前版本见 [.claude-plugin/plugin.json](.claude-plugin/plugin.json)，变更记录见 [CHANGELOG.md](CHANGELOG.md)。
