#!/usr/bin/env python3
"""Scaffold a new skill from templates/.

Usage:
    python3 tools/new_skill.py <plugin> <skill-name>
    python3 tools/new_skill.py emb-drivers driver-from-datasheet

Creates:
    plugins/<plugin>/skills/<skill>/SKILL.md            (from templates/skill)
    plugins/<plugin>/skills/<skill>/references/README.md
    plugins/<plugin>/evals/<skill>/basic/               (positive case)
    plugins/<plugin>/evals/<skill>/no-trigger/          (negative case)
and marks the skill as "🚧 开发中" in the plugin README's Skills table.
The generated files contain __占位符__ that tools/lint_skills.py reports until filled in.
"""

import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

NEGATIVE_PROMPT = """---
max_turns: 5
allowed_tools: [Read, Glob, Grep, Skill]
tags: [{skill}, negative]
---

__写一个相近但不该触发本 skill 的请求，例如同领域的概念问答__
"""
NEGATIVE_GRADER = """---
type: tool_used
tool: Skill
input_match: '"skill"\\s*:\\s*"(?:[\\w-]+:)?{skill}"'
min: 0
max: 0
arm: both
---
"""


def fill(path, skill):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    with open(path, "w", encoding="utf-8") as f:
        f.write(text.replace("__SKILL_NAME__", skill))


def mark_in_readme(plugin, skill):
    readme = os.path.join(ROOT, "plugins", plugin, "README.md")
    with open(readme, encoding="utf-8") as f:
        text = f.read()
    link = f"[{skill}](skills/{skill}/SKILL.md)"
    row = re.compile(rf"^\| {re.escape(skill)} \| (`[^`]+`) \| [^|]+ \|", re.MULTILINE)
    if row.search(text):
        text = row.sub(lambda m: f"| {link} | {m.group(1)} | 🚧 开发中 |", text, count=1)
    else:
        lines = text.splitlines()
        last_row = max(i for i, line in enumerate(lines) if line.startswith("| ") and "/" + plugin + ":" in line)
        lines.insert(last_row + 1, f"| {link} | `/{plugin}:{skill}` | 🚧 开发中 | __一句话说明作用__ |")
        text = "\n".join(lines) + "\n"
    with open(readme, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    plugin, skill = sys.argv[1], sys.argv[2]
    proot = os.path.join(ROOT, "plugins", plugin)
    if not os.path.isdir(proot):
        print(f"插件不存在：plugins/{plugin}（可选：{', '.join(sorted(os.listdir(os.path.join(ROOT, 'plugins'))))}）")
        return 1
    if not KEBAB.match(skill):
        print(f"skill 名须为 kebab-case：{skill}")
        return 1
    sdir = os.path.join(proot, "skills", skill)
    if os.path.exists(sdir):
        print(f"已存在：{os.path.relpath(sdir, ROOT)}")
        return 1

    shutil.copytree(os.path.join(ROOT, "templates", "skill"), sdir)
    fill(os.path.join(sdir, "SKILL.md"), skill)

    edir = os.path.join(proot, "evals", skill)
    basic = os.path.join(edir, "basic")
    shutil.copytree(os.path.join(ROOT, "templates", "eval-case"), basic)
    for dirpath, _, files in os.walk(basic):
        for f in files:
            fill(os.path.join(dirpath, f), skill)
    neg = os.path.join(edir, "no-trigger")
    os.makedirs(os.path.join(neg, "graders"))
    with open(os.path.join(neg, "prompt.md"), "w", encoding="utf-8") as f:
        f.write(NEGATIVE_PROMPT.format(skill=skill))
    with open(os.path.join(neg, "graders", "skill-not-fired.md"), "w", encoding="utf-8") as f:
        f.write(NEGATIVE_GRADER.format(skill=skill))

    for sub in ("skills", "evals"):
        keep = os.path.join(proot, sub, ".gitkeep")
        if os.path.exists(keep):
            os.remove(keep)
    mark_in_readme(plugin, skill)

    print(f"已创建 /{plugin}:{skill}：")
    print(f"  {os.path.relpath(sdir, ROOT)}/")
    print(f"  {os.path.relpath(edir, ROOT)}/{{basic,no-trigger}}/")
    print("下一步（详见 CONTRIBUTING.md）：")
    print("  1. 填写 SKILL.md 与 references/，删除 references/README.md")
    print("  2. 填写评测用例中的 __占位符__")
    print(f"  3. 完成后把 plugins/{plugin}/README.md 中的状态改为 ✅ 已发布，更新 CHANGELOG 并升级版本")
    print("  4. 运行 python3 tools/lint_skills.py 与 claude plugin validate . --strict")
    return 0


if __name__ == "__main__":
    sys.exit(main())
