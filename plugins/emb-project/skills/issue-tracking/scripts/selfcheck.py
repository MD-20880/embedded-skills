#!/usr/bin/env python3
"""issue-tracking skill 的开发期自检（CI 自动运行，见仓库 docs/authoring-guide.md）。

frontmatter、相对链接等通用检查由仓库的 tools/lint_skills.py 负责；这里只检查本 skill 特有的内容。

检查项：
  1. 章节引用：各文件中“method.md 第 X 章 / 第 X.Y 节”和 method.md 内部的“第 X 章 / 节”都能找到对应标题。
  2. 反引号中引用的 skill 内路径（references/、assets/、scripts/）都存在。
  3. assets/github/*.yml 都是合法 YAML，且含 name、description、body。
  4. 可选：--deny-file 指定一个禁用词文件（每行一个词，# 开头为注释），任一词出现即失败。
     用来防止项目专有名词混进本 skill；该文件放在仓库外，不提交。

用法：python3 scripts/selfcheck.py [--deny-file PATH]
依赖：PyYAML（pip install pyyaml）
"""
import argparse
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEXT_SUFFIXES = {".md", ".yml", ".yaml", ".py"}
errors = []


def fail(msg):
    errors.append(msg)


def text_files():
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and p.suffix in TEXT_SUFFIXES and ".git" not in p.parts:
            yield p


def check_section_refs():
    method = (ROOT / "references/method.md").read_text(encoding="utf-8")
    heads = set(re.findall(r"^## (\d+)\.", method, re.M))
    heads |= set(re.findall(r"^### (\d+\.\d+)", method, re.M))
    for p in (ROOT / "SKILL.md", ROOT / "references/method.md", ROOT / "references/examples.md"):
        for ref in re.findall(r"第 (\d+(?:\.\d+)?) [章节]", p.read_text(encoding="utf-8")):
            if ref not in heads:
                fail(f"{p.relative_to(ROOT)}: 引用了不存在的第 {ref} 章/节")


def check_paths():
    for p in text_files():
        if p.suffix != ".md":
            continue
        s = p.read_text(encoding="utf-8")
        for ref in re.findall(r"`((?:references|assets|scripts)/[^`*<>\s]+)`", s):
            if not (ROOT / ref).exists():
                fail(f"{p.relative_to(ROOT)}: 引用的路径不存在：{ref}")


def check_forms():
    forms = sorted((ROOT / "assets/github").glob("*.yml"))
    if not forms:
        fail("assets/github: 没有表单")
    for f in forms:
        try:
            d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            fail(f"{f.relative_to(ROOT)}: YAML 解析失败：{e}")
            continue
        for key in ("name", "description", "body"):
            if key not in d:
                fail(f"{f.relative_to(ROOT)}: 缺少 {key}")


def check_deny(path):
    words = [w.strip() for w in pathlib.Path(path).read_text(encoding="utf-8").splitlines()]
    words = [w for w in words if w and not w.startswith("#")]
    for p in text_files():
        if p == pathlib.Path(__file__).resolve():
            continue
        s = p.read_text(encoding="utf-8")
        for w in words:
            if w in s:
                fail(f"{p.relative_to(ROOT)}: 出现禁用词“{w}”")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--deny-file", help="禁用词文件，每行一个词")
    args = ap.parse_args()
    check_section_refs()
    check_paths()
    check_forms()
    if args.deny_file:
        check_deny(args.deny_file)
    for e in errors:
        print("FAIL", e)
    print("PASS" if not errors else f"{len(errors)} 项失败")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
