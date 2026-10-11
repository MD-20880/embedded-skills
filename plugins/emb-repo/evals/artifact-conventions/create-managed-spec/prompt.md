---
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
tags: [artifact-conventions, positive]
---

我在这个固件项目新写一份“链路超时恢复规范”，现在只是给几个板卡之间协调的草案：发生超时后统一释放资源，重传细则尚未确认。请创建 `docs/protocols/link-timeout.md`，把它作为受管理规范正确登记到项目的工程文件索引里。仓库里已有 YAML 登记表和其他受管理文件，请不要丢掉原有条目，也不要把草案当成已批准的协议。普通调试脚本不需要跟着纳管。
