---
max_turns: 5
allowed_tools: [Read, Glob, Grep, Skill]
tags: [issue-tracking, negative]
---

用 C 写一个通过 I2C 读取 BMI270 芯片 ID 寄存器（地址 0x00）的函数，I2C 读接口假设为 int i2c_read(uint8_t dev, uint8_t reg, uint8_t *buf, size_t len)，设备地址 0x68。直接给代码。
