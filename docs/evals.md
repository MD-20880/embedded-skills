# 评测指南

本仓库用 Claude Code 官方的 [`claude plugin eval`](https://code.claude.com/docs/en/plugin-evals) 评测 skill 的行为：它是否在该触发时触发、在不该触发时保持沉默，以及触发后的产出是否达标。

## 1. 目录约定

```text
plugins/<插件>/evals/
└── <skill名>/                 # 按 skill 分组（非用例目录，仅用于归类）
    ├── <正向用例>/
    │   ├── prompt.md          # frontmatter：轮数、工具等；正文：用户请求
    │   ├── case.yaml          # 可选：需要构造工作区时使用（scaffold_script）
    │   ├── setup.sh           # 可选：构造用例所需的仓库文件
    │   └── graders/*.md       # 评分器，每个文件一个
    └── no-trigger/            # 反向用例
        ├── prompt.md
        └── graders/skill-not-fired.md
```

- `evals/` 下的一级目录名必须是本插件已有的 skill 名。**【lint】**
- 评测只加载被测插件本身。因此插件依赖要写在 `marketplace.json` 条目中，不能写在 `plugin.json`，否则被测插件不会被加载，所有“skill 被触发”的评分器都会失败（见 [架构说明 4.3](architecture.md#43-项目画像方法与事实分离)）。**【lint】**
- 评测结果写在 `evals/results/`，已加入 `.gitignore`，不要提交。

## 2. 用例设计

### 正向用例

- **请求用用户的口吻写**，不要点名 skill，例如“帮我把这个项目的基本情况整理一下，以后写驱动要用”，而不是“运行 project-profile”。
- **构造有陷阱的输入**：在 `setup.sh` 中放入真实项目常见的问题，例如 README 与链接脚本的容量冲突、已删除的 preset，检验 skill 是否遵守“不猜测、标注待确认”这类关键规则。
- **每个用例两类评分器**：一类检查结果（文件内容、回复内容），一类检查过程（skill 是否被触发、是否调用了不该用的工具）。

### 反向用例

选**同领域但不该触发**的请求，例如对 `project-profile` 问“volatile 能保证原子性吗”。评分器：

```markdown
---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?<skill名>"'
min: 0
max: 0
arm: both
---
```

## 3. 评分器选择

| 想检查 | 评分器 | 费用 |
| --- | --- | --- |
| skill 被触发 / 未被触发 | `tool_used`（`tool: Skill` + `input_match`） | 免费 |
| 生成了某个文件 | `file_exists` | 免费 |
| 文件或回复包含关键内容 | `regex`（`target: { source: file, path: … }` 或默认的最终回复） | 免费 |
| 没有改文件 | `tool_used`（`tool: Write` / `Edit`，`min: 0`、`max: 0`、`arm: both`） | 免费 |
| 回答在语义上是否正确 | `llm`（正文写具体的 PASS / FAIL 条件） | 每次运行约 3 次评审模型调用 |

优先使用免费的确定性评分器；`llm` 评分器只用于短文本，规则要写成具体的 PASS / FAIL 条件。

## 4. 运行

在插件目录下运行（例如 `plugins/emb-repo`）：

```bash
# 迭代时：单个用例、单次运行、不跑无插件对照，最省钱
claude plugin eval . --case <用例名> --runs 1 --ablation none

# 用例需要构造工作区、写文件、跑脚本时，显式授予工具
claude plugin eval . --case init-multi-board --runs 1 --ablation none \
  --scaffold --allow-tools Write "Bash(python3 *)" "Bash(git *)"

# 发布前：完整套件，默认每个用例跑 3 次，并与“不装插件”对照
claude plugin eval . --scaffold --allow-tools Write "Bash(python3 *)" "Bash(git *)"
```

注意：

- `--case` 每次只能传一个用例名（或一个 glob）。
- 授予 Bash 时，Linux 需要安装 `bubblewrap` 和 `socat` 作为沙箱，否则运行会被拒绝。
- `--scaffold` 会以当前用户身份执行用例中的 `setup.sh`，只对本仓库自己写的用例使用。
- 每次运行都会调用模型并计费；可用 `--max-cost-usd` 设上限。

## 5. 读结果

- 终端输出每个评分器的 ✓ / ✗ 及原因；`--keep-temp` 会保留工作区和 `trace.jsonl`，可用于排查。
- `WITH` / `W/OUT` / `Δ`：装插件与不装插件的分数和差值。Δ 接近 0 说明这个用例检验不出 skill 的价值，应该改用例。
- 分数下降时，先看 trace 中 skill 是否被触发，再看是哪一步偏离了流程，最后才去改 SKILL.md。

## 6. 在 CI 中运行

`.github/workflows/evals.yml` 提供手动触发的评测任务（需要在仓库 Secrets 中配置 `ANTHROPIC_API_KEY`）。每个 PR 上不自动运行评测，因为评测会产生模型调用费用；发布新版本前请手动触发一次。

## 7. 已验证的基线

| 插件 | 用例 | 结果（2026-10-06） |
| --- | --- | --- |
| emb-repo | `project-profile/init-multi-board` | 1.00（1 次） |
| emb-repo | `project-profile/check-stale` | 1.00（1 次） |
| emb-repo | `project-profile/no-trigger-general-c` | 1.00（1 次） |
| emb-project | `issue-tracking/close-check-checklist-done` | 1.00（3 次） |
| emb-project | `issue-tracking/gate-review-dvt` | 1.00（3 次） |
| emb-project | `issue-tracking/no-trigger-driver-code` | 1.00（3 次） |
