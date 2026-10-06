---
name: project-profile
description: 为嵌入式项目建立、更新或核查“项目画像”（docs/embedded-profile.md）：汇总 MCU 与板卡、软件栈、构建与烧录命令、目录与编码约定、测试与验证方式、已知坑，每条附来源，供其他嵌入式 skills 共用。Create, update or check the embedded project profile that records boards, MCUs, toolchain, build/flash commands and conventions with sources.
when_to_use: 首次在项目中使用 embedded-skills、新增板子或硬件改版、构建方式变化、发版前核查时使用。触发语如“建立项目画像”“初始化嵌入式上下文”“更新画像”“检查画像是否过期”；"create project profile", "onboard this firmware repo", "refresh embedded context", "is the profile stale".
argument-hint: "[init|update|check]"
allowed-tools: Read Glob Grep Bash(python3 *) Bash(git log *) Bash(git ls-files *)
---

# 项目画像（project-profile）

为当前项目生成并维护 `docs/embedded-profile.md`。这份画像是所有 embedded-skills 共用的“项目事实缓存”：其他 skill 先读它，再做事。

- 画像的格式与消费规则：[references/profile-spec.md](references/profile-spec.md)（**权威定义，先读**）
- 画像模板：[references/profile-template.md](references/profile-template.md)
- 每一节去哪里找证据：[references/discovery-checklist.md](references/discovery-checklist.md)
- 证据扫描脚本：`python3 ${CLAUDE_SKILL_DIR}/scripts/scan_repo.py <项目根> [--json | --check <画像路径>]`

## 模式

根据参数 `$ARGUMENTS` 选择模式；未给参数时：画像不存在 → `init`，已存在 → `update`。

| 模式 | 作用 | 是否写文件 |
| --- | --- | --- |
| `init` | 从零建立画像 | 写入 `docs/embedded-profile.md` |
| `update` | 按当前仓库刷新画像，保留用户确认过的内容 | 修改画像 |
| `check` | 只报告过期或缺失的条目 | 否 |

## 流程

### 1. 准备

1. 阅读 `references/profile-spec.md`，明确章节与写法要求。
2. 确认项目根目录（`git rev-parse --show-toplevel` 或当前目录）。
3. 若画像已存在，完整读取它；记下其中标为 `用户确认` 的条目——这些条目在 `update` 中**只能在有反证时修改**，且须向用户说明。

### 2. 收集证据

1. 运行扫描脚本得到线索：`python3 ${CLAUDE_SKILL_DIR}/scripts/scan_repo.py <项目根>`。
   脚本只列项目自有文件，厂商 / 第三方目录只计数；它的输出是**线索不是结论**。
2. 按 `references/discovery-checklist.md` 的顺序阅读证据：先读项目自己的 README、文档索引、CLAUDE.md，再用配置文件（CMakePresets、链接脚本、工具链文件、CI 配置）核实，最后才从源码推断。
3. 多板项目逐板核实；同一板的多个硬件版本分别列行。
4. 遇到冲突（如 README 写 64 KB，链接脚本写 32 KB）：两者都记录，放入第 10 节“待确认”，不要自行裁决。

### 3. 编写画像（init / update）

1. 以 `references/profile-template.md` 为骨架，章节顺序与标题保持不变。
2. 每条事实一行并标注来源（相对路径 / 命令 / `用户确认 YYYY-MM-DD`）。
3. 能链接就不复制：引脚表、寄存器表、长命令说明链接到项目文档。
4. 没有证据的内容一律写入第 10 节，附扫描线索；**不得猜测型号、主频、容量、版本号**。
5. 篇幅控制在约 200 行以内；超出时把细节移回项目文档并改为链接。
6. 更新 frontmatter 的 `updated` 为今天日期。
7. `update` 模式：在回复中列出变更摘要（新增 / 修改 / 删除了哪些条目及原因）。

### 4. 核查（check，或 init/update 收尾）

1. 运行 `python3 ${CLAUDE_SKILL_DIR}/scripts/scan_repo.py <项目根> --check docs/embedded-profile.md`，检查画像中引用的路径与 preset 是否仍然存在。
2. 抽查第 4 节的构建命令与 CI 配置是否一致。
3. `check` 模式只输出报告：过期条目、缺失章节、建议动作；不修改文件。

### 5. 收尾

向用户汇报：

- 画像路径与各章节完成度（已确认 / 部分 / 待确认）
- 第 10 节“待确认”问题清单——逐条请用户回答；用户回答后把答案写回对应章节，来源记为 `用户确认 <日期>`
- 建议（由用户决定是否执行）：在项目 `CLAUDE.md` 中加一行“嵌入式项目事实见 `docs/embedded-profile.md`”；若项目有文档索引（如 `docs/README.md`），在索引中登记画像

## 约束

- 只写入 `docs/embedded-profile.md`，不修改项目中的其他文件。
- 不在画像中写入密钥、账号、内网地址等敏感信息；遇到时只写“见 <路径>”。
- 扫描脚本只读；不要为收集证据而运行构建、烧录或任何会改变设备状态的命令。
