# emb-repo · 项目 Repo 管理

维护嵌入式仓库的“地基”：项目画像、通用工程默认原则、目录与构建约定、文档索引、版本发布。

## 适用场景

- 项目首次接入 embedded-skills（先建项目画像）
- 新增板子 / 硬件版本 / 程序时按约定落位
- 保持 README 与文档索引和实际目录一致
- 发版时整理变更记录

## Skills

| Skill | 调用方式 | 状态 | 作用 |
| --- | --- | --- | --- |
| [project-profile](skills/project-profile/SKILL.md) | `/emb-repo:project-profile` | ✅ 已发布 | 建立 / 更新 / 核查项目画像 `docs/embedded-profile.md`，供所有 skills 共用 |
| [engineering-principles](skills/engineering-principles/SKILL.md) | `/emb-repo:engineering-principles` | ✅ 已发布 | 提供工程知识、假设与承诺、契约一致性、证据与交接原则；SessionStart/SubagentStart 注入精简原则 |
| repo-layout | `/emb-repo:repo-layout` | 📝 规划中 | 梳理或执行目录与构建约定：新增板、硬件版本、程序时的落位与改动清单 |
| docs-index-sync | `/emb-repo:docs-index-sync` | 📝 规划中 | 检查并同步 README、文档索引与实际目录 |
| release-notes | `/emb-repo:release-notes` | 📝 规划中 | 整理版本变更记录与发布说明 |

> 状态说明：✅ 已发布（含评测用例）；📝 规划中（名称与范围可能调整）。新增 skill 的流程见仓库根目录 [CONTRIBUTING.md](../../CONTRIBUTING.md)。

## 默认原则自动加载

插件启用时，`hooks/hooks.json` 注册两个只读 hook，内容都来自同一份 [轻量工程原则](skills/engineering-principles/references/core-principles.md)：

| 时机 | 注入内容 | 大约体积 |
| --- | --- | --- |
| 会话开始（`SessionStart`） | 完整的轻量原则（6 条） | 约 1.5K 字符 |
| 子 Agent 启动（`SubagentStart`） | 一行精简版：6 条原则的标题 | 约 150 字符 |

hook 只读取插件自身的文件，不审批、不拦截、不写入仓库、不访问网络。需要完整说明时，调用 `/emb-repo:engineering-principles`；普通编码任务不会因此被要求写管理报告。

### 关闭自动注入

所有领域插件都依赖 `emb-repo`，所以安装任何一个插件都会带上这些 hook。不需要时可以关闭：

- 在 Claude Code 中打开 `/config`，找到 `emb-repo` 的“自动注入工程原则 / Inject engineering principles”，设为关闭；或
- 在终端执行：`echo '{"inject_principles":"false"}' | claude plugin configure emb-repo@embedded-skills --values-stdin`

关闭后不再注入任何内容，`project-profile` 等 skill 不受影响，`/emb-repo:engineering-principles` 仍可手动调用。

### 运行要求

hook 以 exec 形式调用 `python3`（不经过 shell）。Windows 上若只有 `python` 或 `py`、没有 `python3`，每次启动会话都会出现 hook 错误；此时请安装提供 `python3` 的 Python 发行版，或按上文关闭自动注入。

修改原则或 hook 后，运行 `python3 skills/engineering-principles/scripts/selfcheck.py` 检查两种输出、开关和体积上限（仓库 lint 也会自动运行它）。

## 依赖的项目画像章节

全部章节（本插件负责生成画像）。画像规范见 [profile-spec](../emb-repo/skills/project-profile/references/profile-spec.md)；项目中尚无画像时，先运行 `/emb-repo:project-profile`。

## 安装

```text
/plugin marketplace add MD-20880/embedded-skills
/plugin install emb-repo@embedded-skills
```

## 版本

当前版本见 [.claude-plugin/plugin.json](.claude-plugin/plugin.json)，变更记录见 [CHANGELOG.md](CHANGELOG.md)。
