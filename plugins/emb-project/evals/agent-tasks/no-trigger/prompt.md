---
max_turns: 5
allowed_tools: [Read, Glob, Grep, Skill]
tags: [agent-tasks, negative]
---

UART 接收用 DMA 加空闲中断，环形缓冲的读写指针要不要加 volatile？在 Cortex-M4 上单生产者单消费者需要关中断吗？
