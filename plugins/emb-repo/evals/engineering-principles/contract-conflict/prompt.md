---
max_turns: 18
allowed_tools: [Read, Glob, Grep, Skill]
tags: [engineering-principles, positive]
---

固件仓库就在当前目录。我们现在几个 AI 同时写固件，A 要按刚讨论的 UART 协议新草案开发，B 继续改旧验证 Demo，另一个同事看见 docs/README 说两份都是正式协议。如何正确理解 Issue、ADR、当前契约、旧实现和测试各自的作用？什么东西可以继续探索，什么不能带着冲突合入主线？请结合仓库里的实际文件给我工程判断原则，不要替我改仓库或管理 Agent。
