# CLAUDE.md

本仓库是嵌入式软件工程 skills 的 Claude Code 插件市场。这里写的是 skill（方法），不是固件代码。

## 必读

- 整体设计：[docs/architecture.md](docs/architecture.md)
- skill 写法：[docs/authoring-guide.md](docs/authoring-guide.md)
- 评测：[docs/evals.md](docs/evals.md)；发布与版本：[docs/release.md](docs/release.md)
- 项目画像规范（跨插件契约）：[plugins/emb-repo/skills/project-profile/references/profile-spec.md](plugins/emb-repo/skills/project-profile/references/profile-spec.md)

## 常用命令

```bash
python3 tools/lint_skills.py                            # 仓库规范检查（提交前必跑）
python3 tools/lint_skills.py --changed-since origin/main # 同时检查改动过的插件是否升级了版本
claude plugin validate . --strict                       # 官方 schema 校验
python3 tools/new_skill.py <插件> <skill名>              # 生成新 skill 骨架
claude plugin eval plugins/<插件> --case <用例> --runs 1 --ablation none   # 抽测单个用例（计费）
```

## 工作规则

- 新增 skill 时使用 `/new-skill`，先通过提问收集用户的实际经验，再动笔；不要凭通用知识直接写完。
- 任何插件内的改动都要升级该插件的 `plugin.json` 版本，并写 CHANGELOG。
- 需要项目事实的 skill，第一步必须按 profile-spec 第 6 节读取 `docs/embedded-profile.md`。
- 修改 profile-spec 属于跨插件变更：检查所有读取画像的 skill 是否需要同步修改。
- skill 中涉及寄存器、时序、容量、主频等数值时，必须要求有来源，禁止猜测。
- 文档语言为中文；skill 的 `description` 与 `when_to_use` 中英并列。
- 不要提交 `plugins/*/evals/results/`。
