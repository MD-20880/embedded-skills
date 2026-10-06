# 贡献指南

本文说明如何在本仓库新增、修改和发布 skill。第一次贡献前，建议先读 [架构说明](docs/architecture.md) 了解整体设计。

## 环境准备

| 工具 | 用途 | 安装 |
| --- | --- | --- |
| Python ≥ 3.9 + PyYAML | 运行 `tools/` 下的脚本 | `pip install -r tools/requirements.txt` |
| Claude Code ≥ 2.1.269 | 官方校验 `claude plugin validate`、评测 `claude plugin eval` | 见 [官方文档](https://code.claude.com/docs/en/setup) |
| bubblewrap、socat（Linux） | 评测中授予 Bash 时所需的沙箱 | `apt install bubblewrap socat` |

本地调试插件时，可以直接把本仓库作为本地市场添加，修改后在会话中执行 `/reload-plugins` 即可生效，不必升级版本：

```bash
claude plugin marketplace add ./           # 在本仓库根目录执行
claude plugin install emb-repo@embedded-skills
```

## 新增一个 skill

### 推荐方式：用 `/new-skill` 对话完成

在本仓库中打开 Claude Code，输入 `/new-skill <想沉淀的工作>`。Claude 会依次：

1. 通过提问收集你的实际做法、判断标准和踩过的坑
2. 确定所属插件与 skill 名
3. 运行脚手架，起草 SKILL.md、references 和评测用例
4. 运行检查并修正
5. 更新插件 README、CHANGELOG 和版本号

### 手动方式

1. **确定归属**：按 [编写规范 · 归属](docs/authoring-guide.md#1-归属与命名) 选择插件和 skill 名。
2. **生成骨架**：

   ```bash
   python3 tools/new_skill.py <插件> <skill名>      # 例：python3 tools/new_skill.py emb-drivers driver-port
   ```

   生成 `skills/<skill>/`、`evals/<skill>/{basic,no-trigger}/`，并把插件 README 中该 skill 的状态改为 🚧 开发中。

3. **编写 SKILL.md 与 references**：遵循 [编写规范](docs/authoring-guide.md)。所有 `__占位符__` 都必须替换掉，lint 会检查。
4. **编写评测用例**：至少一个正向用例和一个反向用例，见 [评测指南](docs/evals.md)。
5. **本地检查**：

   ```bash
   python3 tools/lint_skills.py                  # 仓库规范
   claude plugin validate . --strict             # 官方 schema
   claude plugin eval plugins/<插件> --case <用例> --runs 1 --ablation none   # 抽测（会产生模型调用费用）
   ```

6. **发布准备**：把插件 README 中的状态改为 ✅ 已发布，在插件 `CHANGELOG.md` 中新增版本条目，并升级 `plugin.json` 的 `version`（新增 skill 升 MINOR），见 [发布流程](docs/release.md)。
7. **提交 PR**：CI 会运行 lint 与官方校验，并检查改动过的插件是否升级了版本。

## 修改已有 skill

1. 先读该 skill 的 SKILL.md、references 和评测用例，弄清现有行为。
2. 修改前先跑一次相关评测并记下基线分数；如果是修复问题，先补一个能复现问题的评测用例。
3. 修改后重跑评测，分数不应下降。
4. 升级插件版本并写 CHANGELOG（修复升 PATCH，行为变化升 MINOR，不兼容变化升 MAJOR）。

## 提交规范

- 提交信息格式：`<插件或范围>: <做了什么>`，例如 `emb-drivers: add driver-port skill`、`tools: check eval placeholders`。
- 一个 PR 聚焦一件事；跨插件的规范调整与单个 skill 的改动分开提交。
- 修改 [项目画像规范](plugins/emb-repo/skills/project-profile/references/profile-spec.md) 属于跨插件变更，须在 PR 描述中说明对各插件 skill 的影响。
