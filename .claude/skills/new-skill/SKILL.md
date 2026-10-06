---
name: new-skill
description: 在 embedded-skills 仓库中，通过访谈用户的实际经验，新建一个嵌入式 skill（含 SKILL.md、references、评测用例、README/CHANGELOG/版本更新）。Interview the user and author a new embedded skill end to end in this repository.
when_to_use: 用户想把某项嵌入式工作沉淀成 skill 时使用。触发语如“新建一个 skill”“把……沉淀成 skill”“加一个审查 skill”；"add a new skill", "turn this workflow into a skill".
argument-hint: "[想沉淀的工作，如：I2C 驱动移植]"
disable-model-invocation: true
allowed-tools: Read Glob Grep Bash(python3 tools/*)
---

# 新建 skill（new-skill）

和用户一起，把一项嵌入式工作沉淀为本仓库中的一个 skill。**skill 的价值来自用户的真实经验**：先访谈，再动笔。

开始前阅读：

- [docs/authoring-guide.md](../../../docs/authoring-guide.md)：写法规范（必须遵守）
- [docs/evals.md](../../../docs/evals.md)：评测用例写法
- 目标插件的 `README.md`：看看是否已有规划中的同类 skill

## 流程

### 1. 访谈（不要跳过）

围绕 `$ARGUMENTS` 逐轮提问。每轮最多 3 个问题，优先用选择题；用户回答后再追问细节。必须弄清：

1. **触发场景**：什么时候会做这件事？用户通常会怎么说？
2. **输入**：手头有什么（代码、手册、日志、波形、需求文档）？
3. **产出**：交付物是什么？放在哪里？什么格式？做到什么程度算完成？
4. **做法**：用户自己是按什么步骤做的？每一步怎么判断做对了？
5. **坑**：过去出过什么问题？新手最容易犯什么错？哪些地方绝对不能猜？
6. **边界**：哪些相关工作不属于这个 skill（交给哪个 skill）？
7. **例子**：有没有可参考的真实例子（如 overide_glove 中的某个驱动或文档）？

访谈结束时，用 5~10 行复述你的理解，请用户确认后再继续。

### 2. 定归属与命名

按 authoring-guide 第 1 节确定插件与 skill 名，并检查是否与已有或规划中的 skill 重叠。把结论告诉用户，确认后继续。

### 3. 生成骨架

```bash
python3 tools/new_skill.py <插件> <skill名>
```

### 4. 编写

1. `SKILL.md`：按模板骨架写，第一步固定为读取项目画像，并写明需要哪些章节；把访谈中的“做法”写成编号步骤，把“坑”写成判断标准和约束。
2. `references/`：长检查清单、规范摘要、示例放这里；删除模板自带的 `references/README.md`。
3. `scripts/`：只有能确定性完成的工作（解析、校验、统计）才写脚本，只用标准库。
4. 评测用例：至少一个正向用例和一个反向用例；正向用例要在 `setup.sh` 中埋入访谈中提到的“坑”。

### 5. 检查

```bash
python3 tools/lint_skills.py
claude plugin validate . --strict
```

逐条修正直到没有错误。告诉用户评测命令，并说明运行评测会产生费用，由用户决定是否现在运行。

### 6. 收尾

1. 插件 README 的 Skills 表：状态改为 ✅ 已发布（尚未评测通过时保持 🚧 开发中），补全“作用”一栏。
2. 插件 CHANGELOG 新增版本条目；`plugin.json` 的版本按 docs/release.md 升级（新增 skill 升 MINOR）。
3. 向用户汇报：新增文件清单、skill 的调用方式、访谈中仍未确定的问题、建议的下一步（例如在真实项目中试用后再迭代）。

## 约束

- 不要在访谈完成之前写 SKILL.md 正文。
- 不要把某个具体项目的事实（板名、引脚、命令）写进 skill；这些属于项目画像。
- 用户没有提到的做法，可以作为建议提出，但要标明是建议，并由用户决定是否采纳。
