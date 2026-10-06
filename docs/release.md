# 发布流程

## 1. 版本规则

每个插件独立使用[语义化版本](https://semver.org/lang/zh-CN/) `MAJOR.MINOR.PATCH`，版本号**只写在** `plugins/<插件>/.claude-plugin/plugin.json` 的 `version` 字段中（市场条目里不写版本）。

| 变更 | 升级 | 例子 |
| --- | --- | --- |
| 修正错别字、措辞、修复不改变流程的问题 | PATCH | 0.1.0 → 0.1.1 |
| 新增 skill；已有 skill 新增步骤、检查项或参数 | MINOR | 0.1.1 → 0.2.0 |
| 删除或重命名 skill；改变产出格式；项目画像规范升级到不兼容的新版本 | MAJOR | 0.2.0 → 1.0.0 |
| 只改评测用例、插件 README | PATCH（CI 会因插件目录有改动而要求升级） | |

`1.0.0` 之前，MINOR 也可以包含不兼容变化，但须在 CHANGELOG 中注明。

**为什么必须升版本**：使用方只有在插件版本号变化时才会拉取新内容。不升级，改动就到不了使用方；反过来，写到一半的改动只要不升版本，也不会被推送出去。

## 2. 发布步骤

1. 在 `plugins/<插件>/CHANGELOG.md` 顶部新增条目：

   ```markdown
   ## [0.2.0] - 2026-10-20

   ### 新增
   - `driver-port`：……

   ### 变更
   - ……

   ### 修复
   - ……
   ```

2. 修改 `plugin.json` 的 `version`，使其与 CHANGELOG 中的最新条目一致。**【lint：CHANGELOG 中必须有当前版本】**
3. 运行检查：

   ```bash
   python3 tools/lint_skills.py --changed-since origin/main
   claude plugin validate . --strict
   ```

4. 涉及 skill 行为的改动，手动跑一次相关评测，见 [评测指南](evals.md)。
5. 提交 PR，CI 通过后合并到 `main`。合并后，使用方执行 `/plugin marketplace update embedded-skills`（或开启了自动更新）即可获得新版本。

## 3. 重命名或删除插件

插件名会写进使用方的设置（`enabledPlugins`），改名或删除会导致已安装的用户报错。必须改名或删除时：

1. 在 `marketplace.json` 顶层的 `renames` 中登记 `"旧名": "新名"`（删除则为 `null`），只追加、不修改已有条目；
2. 在受影响插件的 CHANGELOG 中说明；
3. 只修改展示名称时，改 `plugin.json` 的 `displayName` 即可，不要改 `name`。

## 4. 重命名或删除 skill

skill 名是调用命令的一部分（`/插件:skill`），改名会影响用户习惯和项目文档中的引用。

- 按 MAJOR 变更处理（1.0.0 之前按 MINOR，并在 CHANGELOG 中标注“不兼容”）；
- 同时移动 `evals/<旧名>/` 到 `evals/<新名>/`，并更新插件 README。
