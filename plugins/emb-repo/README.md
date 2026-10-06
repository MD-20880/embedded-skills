# emb-repo · 项目 Repo 管理

维护嵌入式仓库的“地基”：项目画像、目录与构建约定、文档索引、版本发布。

## 适用场景

- 项目首次接入 embedded-skills（先建项目画像）
- 新增板子 / 硬件版本 / 程序时按约定落位
- 保持 README 与文档索引和实际目录一致
- 发版时整理变更记录

## Skills

| Skill | 调用方式 | 状态 | 作用 |
| --- | --- | --- | --- |
| [project-profile](skills/project-profile/SKILL.md) | `/emb-repo:project-profile` | ✅ 已发布 | 建立 / 更新 / 核查项目画像 `docs/embedded-profile.md`，供所有 skills 共用 |
| repo-layout | `/emb-repo:repo-layout` | 📝 规划中 | 梳理或执行目录与构建约定：新增板、硬件版本、程序时的落位与改动清单 |
| docs-index-sync | `/emb-repo:docs-index-sync` | 📝 规划中 | 检查并同步 README、文档索引与实际目录 |
| release-notes | `/emb-repo:release-notes` | 📝 规划中 | 整理版本变更记录与发布说明 |

> 状态说明：✅ 已发布（含评测用例）；📝 规划中（名称与范围可能调整）。新增 skill 的流程见仓库根目录 [CONTRIBUTING.md](../../CONTRIBUTING.md)。

## 依赖的项目画像章节

全部章节（本插件负责生成画像）。画像规范见 [profile-spec](../emb-repo/skills/project-profile/references/profile-spec.md)；项目中尚无画像时，先运行 `/emb-repo:project-profile`。

## 安装

```text
/plugin marketplace add MD-20880/embedded-skills
/plugin install emb-repo@embedded-skills
```

## 版本

当前版本见 [.claude-plugin/plugin.json](.claude-plugin/plugin.json)，变更记录见 [CHANGELOG.md](CHANGELOG.md)。
