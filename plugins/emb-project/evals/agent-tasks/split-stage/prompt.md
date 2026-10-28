---
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
tags: [agent-tasks, positive]
---

我们有个阶段 issue #120「[板间链路] 底板麦克风数据经 UART 送到主板」。完成定义：底板固件按 docs/link.md 第 5 节的 STRM 帧发送 16 kHz 单声道 PCM；主板端解析并放进环形缓冲；主机测试覆盖拆帧和 CRC；在 A2 底板 V2.5 + A1 V1.5 实板上连续 10 分钟丢帧率低于 0.1%。代码分别在 projects/a2_bottom/ 和 services/audio/，主机测试在 tests/host/。刚才我们在聊天里讨论过缓冲深度取 4 块。

我想把这个阶段交给 Codex 这类 agent 去做，帮我把执行 issue 草稿写出来（标题和正文），先不要在 GitHub 上建。
