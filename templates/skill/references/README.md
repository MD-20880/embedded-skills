# references/ 使用说明（新建 skill 后删除本文件）

- 放 SKILL.md 中按需加载的详细资料：检查清单、术语表、规范、示例。
- 每个文件聚焦一个主题，文件名用 kebab-case，从 SKILL.md 用相对链接引用。
- 需要执行的脚本放 `scripts/`，在 SKILL.md 中用 `${CLAUDE_SKILL_DIR}/scripts/<name>` 调用，只用 Python 标准库。
