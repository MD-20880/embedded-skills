---
max_turns: 30
allowed_tools: [Read, Glob, Grep, Skill, Write, "Bash(python3 *)", "Bash(mktemp *)"]
tags: [mcu-pin-map, positive, scaffold]
---

把 hardware/demo-board/rev-a.net 整理成 demo-board rev-a 上 U1 的 MCU 引脚资料，写到 docs/hardware/demo-board/rev-a/U1-pin-map.md，后面写驱动时复用。产物要绑定实际读取的源文件，能检查源文件是不是变过了。

手上只有这份导出的网表，没有 MCU 或传感器数据手册，也没有对应原理图原件。不要改项目画像和其他文件。
