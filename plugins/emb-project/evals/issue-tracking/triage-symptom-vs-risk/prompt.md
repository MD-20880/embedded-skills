---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
tags: [issue-tracking, positive]
---

今天联调发现两件事，帮我决定各开成什么 issue，并起草标题和标签：

1. 主板 B 版 #2 上播放提示音时，大概每十次有一次爆音。还不知道是功放供电、I²S 时钟还是固件缓冲的问题。
2. 我看原理图时担心：满载时 3V3 可能超出 MCU 的额定电压。还没有测过，器件手册给了上限。
