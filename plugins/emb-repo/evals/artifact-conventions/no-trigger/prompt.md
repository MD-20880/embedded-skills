---
max_turns: 7
allowed_tools: [Read, Glob, Grep, Skill, Write]
tags: [artifact-conventions, negative]
---

请写一个临时 Python 脚本 `tools/filter_uart_log.py`，把串口日志里的空行过滤掉并打印剩余文本。这只是调试工具，不是协议规范或交付工程文档。
