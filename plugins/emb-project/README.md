# emb-project · 项目管理

管理嵌入式产品开发的推进过程：让每个 issue 一眼看出“完没完、卡在哪、谁拍板”，并回答“离下一个开发阶段还差什么”。

## 适用场景

- 新建、改写、拆分、分诊、复核或关闭 issue / 工单（GitHub、GitLab、Jira、飞书等任何工具）
- 判断一个 issue 能不能关闭，验收条件和判据怎么写
- 做 open issue 清单、验证矩阵、项目总览
- EVT / DVT / PVT / MP 阶段评审：能不能进入下一阶段
- 为项目建立 issue 模板、标签和管理规范

## Skills

| Skill | 调用方式 | 状态 | 作用 |
| --- | --- | --- | --- |
| [issue-tracking](skills/issue-tracking/SKILL.md) | `/emb-project:issue-tracking` | ✅ 已发布 | 四类 issue（问题、验证、缺陷、任务）的写法与关闭方式，证据等级 L0–L4，总览与阶段门禁检查 |
| risk-register | `/emb-project:risk-register` | 📝 规划中 | 项目风险登记与跟踪：概率、影响、触发条件、应对措施、复核节奏 |
| status-report | `/emb-project:status-report` | 📝 规划中 | 从 issue 总览生成周报 / 阶段状态汇报 |
| change-control | `/emb-project:change-control` | 📝 规划中 | 设计变更（ECN）管理：变更原因、影响范围、涉及的板与版本、验证要求 |

> 状态说明：✅ 已发布（含评测用例）；📝 规划中（名称与范围可能调整）。新增 skill 的流程见仓库根目录 [CONTRIBUTING.md](../../CONTRIBUTING.md)。

## issue-tracking 一览

**五条核心约定**：完没完一眼可见；结论绑定对象（板、硬件版本、固件版本）；不编造；证据分等级；一个 issue 只管一件事。

| 类型 | 管什么 | 怎样算完 |
| --- | --- | --- |
| 问题 | 结论未知、会影响后续决定的事：选型、取舍、门槛、不确定算不算错 | 写出答案，决策人确认 |
| 验证 | 对照已知规格或限值判断是否达标 | 判定通过或不通过，附证据 |
| 缺陷 | 看到了现象，或按资料能确定是错的；原因可以还不知道 | 按处置方式完成。硬件缺陷：改板修复、软件规避、接受限制；软件缺陷：固件修复、软件规避、接受限制 |
| 任务 | 做完就能直接验收的工作 | 交付并通过验收 |

缺陷先定位、再归类：还没定位的标 `defect:tbd`，查出根因后换成 `defect:hw` 或 `defect:sw`；按根因定归属，不按修法定。三种归属用同一个模板。

证据等级：L0 资料与计算 → L1 仿真与主机测试 → L2 台架实测 → L3 整机实测 → L4 认证与第三方测试。

skill 提供 7 个工作流：新建、改写或迁移、判断能否关闭、记录结论、维护总览、阶段门禁检查、在项目中落地。所有改动外部系统的操作（新建、编辑、关闭 issue，打标签，发评论）都会先给你确认。

- 完整方法：[references/method.md](skills/issue-tracking/references/method.md)
- 完整示例（改写前后、能否关闭、DVT 门禁）：[references/examples.md](skills/issue-tracking/references/examples.md)
- 可直接复制到项目的模板：[assets/templates/](skills/issue-tracking/assets/templates/)、GitHub issue 表单 [assets/github/](skills/issue-tracking/assets/github/)

## 与其他插件的分工

| 场景 | 用哪个 |
| --- | --- |
| 验证项的判据、判定与关闭（“过没过”） | `emb-project:issue-tracking` |
| 上板验证的过程记录（怎么测的、波形、日志） | `emb-bringup:validation-record`（规划中），记录链接到对应的验证 issue 作为证据 |
| 技术方案的取舍与决策记录 | `emb-design:adr-write`（规划中）；对应的“问题”issue 以 ADR 作为答案 |

## 依赖的项目画像章节

1 项目概述（当前阶段）、2 硬件清单（板与硬件版本的标准命名）、8 文档约定（issue 管理映射文档的位置）。画像规范见 [profile-spec](../emb-repo/skills/project-profile/references/profile-spec.md)；项目中尚无画像时，先运行 `/emb-repo:project-profile`。

## 安装

```text
/plugin marketplace add MD-20880/embedded-skills
/plugin install emb-project@embedded-skills
```

## 版本

当前版本见 [.claude-plugin/plugin.json](.claude-plugin/plugin.json)，变更记录见 [CHANGELOG.md](CHANGELOG.md)。许可：issue-tracking 沿用原仓库的 [MIT 许可](skills/issue-tracking/LICENSE)。
