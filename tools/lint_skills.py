#!/usr/bin/env python3
"""Repository linter for embedded-skills.

Checks the marketplace catalog, every plugin manifest, every skill and its eval
cases, and all relative Markdown links. A skill may ship scripts/selfcheck.py for
skill-specific checks; it is run here and must exit 0. Complements `claude plugin validate`,
which checks the Claude Code schema; this script checks this repository's own
conventions (see docs/authoring-guide.md).

Usage:
    python3 tools/lint_skills.py                      # lint the whole repo
    python3 tools/lint_skills.py --strict             # warnings also fail
    python3 tools/lint_skills.py --changed-since origin/main
                                                      # also require a version bump
                                                      # for every plugin changed since REF
Exit code: 0 = clean, 1 = errors found.
"""

import argparse
import json
import os
import re
import subprocess
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("缺少依赖 PyYAML：pip install -r tools/requirements.txt")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PLUGIN_PREFIX = "emb-"
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$")
CJK = re.compile(r"[一-鿿]")
LATIN_SENTENCE = re.compile(r"[A-Za-z]{3,}[^一-鿿]*[A-Za-z]{3,}")
# Template placeholders always start with a CJK character (e.g. __填写说明__), so C
# identifiers common in embedded docs (__FILE__, __NOP, __IO) are never flagged.
PLACEHOLDER = re.compile(r"__[一-鿿][^\n]*?__")
MD_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
DESCRIPTION_LIMIT = 1536
SKILL_LINE_LIMIT = 500
SKILL_KEYS = {
    "name", "description", "when_to_use", "argument-hint", "arguments",
    "disable-model-invocation", "user-invocable", "allowed-tools", "disallowed-tools",
    "model", "effort", "context", "agent", "background", "paths", "shell", "hooks",
    "metadata", "license", "compatibility",
}
GRADER_TYPES = {"regex", "tool_used", "tool_order", "file_exists", "llm", "baseline"}
SKIP_DIRS = {".git", "node_modules", "results", "__pycache__"}


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def error(self, where, msg):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"{where}: {msg}")


def rel(path):
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def split_frontmatter(text):
    """Return (frontmatter dict or None, body, error message or None)."""
    if not text.startswith("---\n"):
        return None, text, "缺少 YAML frontmatter"
    end = text.find("\n---", 4)
    if end < 0:
        return None, text, "frontmatter 未闭合"
    try:
        data = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError as exc:
        return None, text, f"frontmatter 不是合法 YAML：{exc}"
    if not isinstance(data, dict):
        return None, text, "frontmatter 必须是映射"
    return data, text[end + 4:].lstrip("\n"), None


# ---------------------------------------------------------------- marketplace

def lint_marketplace(r):
    path = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
    try:
        market = json.loads(read(path))
    except (OSError, ValueError) as exc:
        r.error(rel(path), f"无法读取：{exc}")
        return []
    for key in ("name", "owner", "plugins"):
        if key not in market:
            r.error(rel(path), f"缺少字段 `{key}`")
    entries = market.get("plugins", [])
    listed = set()
    for i, entry in enumerate(entries):
        where = f"{rel(path)} plugins[{i}]"
        name = entry.get("name", "")
        listed.add(name)
        if not name.startswith(PLUGIN_PREFIX) or not KEBAB.match(name):
            r.error(where, f"插件名 `{name}` 须为 kebab-case 且以 `{PLUGIN_PREFIX}` 开头")
        if entry.get("source") != f"./plugins/{name}":
            r.error(where, f"source 应为 `./plugins/{name}`，实际为 `{entry.get('source')}`")
        if "version" in entry:
            r.error(where, "版本号只写在插件的 plugin.json，市场条目中不要写 version")
        if not entry.get("description"):
            r.error(where, "缺少 description")
        if name != "emb-repo" and "emb-repo" not in (entry.get("dependencies") or []):
            r.error(where, "领域插件须在条目中声明 \"dependencies\": [\"emb-repo\"]（项目画像能力）")
    plugins_dir = os.path.join(ROOT, "plugins")
    on_disk = {d for d in os.listdir(plugins_dir) if os.path.isdir(os.path.join(plugins_dir, d))}
    for d in sorted(on_disk - listed):
        r.error(f"plugins/{d}", "目录存在但未在 marketplace.json 中登记")
    for d in sorted(listed - on_disk):
        r.error(rel(path), f"登记了插件 `{d}` 但目录 plugins/{d} 不存在")
    return sorted(listed & on_disk)


# ---------------------------------------------------------------- plugin

def lint_plugin(r, name):
    root = os.path.join(ROOT, "plugins", name)
    manifest_path = os.path.join(root, ".claude-plugin", "plugin.json")
    try:
        manifest = json.loads(read(manifest_path))
    except (OSError, ValueError) as exc:
        r.error(rel(manifest_path), f"无法读取：{exc}")
        return
    where = rel(manifest_path)
    if manifest.get("name") != name:
        r.error(where, f"name 应与目录名和市场条目一致：`{name}`")
    version = manifest.get("version", "")
    if not SEMVER.match(str(version)):
        r.error(where, f"version `{version}` 不是语义化版本 MAJOR.MINOR.PATCH")
    if not manifest.get("description"):
        r.error(where, "缺少 description")
    if "dependencies" in manifest:
        r.error(where, "依赖写在 marketplace.json 的插件条目中，不写在 plugin.json："
                       "plugin.json 中的依赖会让 claude plugin eval 按路径评测时无法加载本插件")
    if not (manifest.get("author") or {}).get("name"):
        r.error(where, "缺少 author.name")
    if os.path.isdir(os.path.join(root, "bin")):
        r.error(rel(root), "插件根目录不要放 bin/（claude.ai 组织同步会拒绝），脚本放 skill 的 scripts/")

    readme = os.path.join(root, "README.md")
    changelog = os.path.join(root, "CHANGELOG.md")
    readme_text = read(readme) if os.path.exists(readme) else ""
    if not readme_text:
        r.error(rel(root), "缺少 README.md")
    if not os.path.exists(changelog):
        r.error(rel(root), "缺少 CHANGELOG.md")
    elif f"## [{version}]" not in read(changelog):
        r.error(rel(changelog), f"没有当前版本 `## [{version}]` 的条目")

    skills_dir = os.path.join(root, "skills")
    skills = sorted(d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))) \
        if os.path.isdir(skills_dir) else []
    for skill in skills:
        lint_skill(r, name, root, skill, readme_text)

    evals_dir = os.path.join(root, "evals")
    if os.path.isdir(evals_dir):
        for d in sorted(os.listdir(evals_dir)):
            if os.path.isdir(os.path.join(evals_dir, d)) and d not in skills and d not in ("mocks", "results"):
                r.error(rel(os.path.join(evals_dir, d)), "评测目录没有对应的 skill（应为 evals/<skill名>/<用例>/）")


# ---------------------------------------------------------------- skill

def lint_skill(r, plugin, plugin_root, skill, readme_text):
    sdir = os.path.join(plugin_root, "skills", skill)
    spath = os.path.join(sdir, "SKILL.md")
    where = rel(spath)
    if not KEBAB.match(skill):
        r.error(rel(sdir), "skill 目录名须为 kebab-case")
    if not os.path.exists(spath):
        r.error(rel(sdir), "缺少 SKILL.md")
        return
    text = read(spath)
    fm, body, err = split_frontmatter(text)
    if err:
        r.error(where, err)
        return
    for key in sorted(set(fm) - SKILL_KEYS):
        r.error(where, f"未知 frontmatter 字段 `{key}`（Claude Code 会静默忽略，通常是拼写错误）")
    if fm.get("name") != skill:
        r.error(where, f"name 须与目录名一致：`{skill}`")
    desc = str(fm.get("description") or "")
    trigger = str(fm.get("when_to_use") or "")
    if not desc:
        r.error(where, "缺少 description")
    if len(desc) + len(trigger) > DESCRIPTION_LIMIT:
        r.error(where, f"description + when_to_use 共 {len(desc) + len(trigger)} 字符，超过 {DESCRIPTION_LIMIT}")
    if not CJK.search(desc) or not LATIN_SENTENCE.search(desc):
        r.error(where, "description 须同时包含中文说明与英文说明（中英并列，提升触发命中率）")
    if not trigger:
        r.warn(where, "建议填写 when_to_use，列出中英文触发语")
    lines = text.count("\n") + 1
    if lines > SKILL_LINE_LIMIT:
        r.error(where, f"SKILL.md 共 {lines} 行，超过 {SKILL_LINE_LIMIT} 行；把细节移到 references/")
    for path in walk_files(sdir):
        if path.endswith((".md", ".py", ".sh")):
            m = PLACEHOLDER.search(read(path))
            if m:
                r.error(rel(path), f"残留模板占位符 `{m.group(0)}`")
        if path.endswith(".py"):
            try:
                compile(read(path), path, "exec")
            except SyntaxError as exc:
                r.error(rel(path), f"Python 语法错误（第 {exc.lineno} 行）：{exc.msg}")
    selfcheck = os.path.join(sdir, "scripts", "selfcheck.py")
    if os.path.exists(selfcheck):
        # Child output is UTF-8 on every platform, so a Chinese Windows locale (cp936 / GBK) cannot garble it.
        res = subprocess.run([sys.executable, selfcheck], cwd=sdir, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        if res.returncode != 0:
            detail = "; ".join(l for l in res.stdout.splitlines() if l.startswith("FAIL")) or res.stderr.strip()
            r.error(rel(selfcheck), f"skill 自检未通过：{detail}")
    if skill != "project-profile" and "embedded-profile.md" not in body:
        r.warn(where, "未读取项目画像 `docs/embedded-profile.md`；需要项目事实的 skill 应按 profile-spec 第 6 节读取")
    if f"skills/{skill}/SKILL.md" not in readme_text:
        r.error(f"plugins/{plugin}/README.md", f"Skills 表中缺少指向 `skills/{skill}/SKILL.md` 的链接")
    lint_evals(r, plugin_root, skill)


def lint_evals(r, plugin_root, skill):
    edir = os.path.join(plugin_root, "evals", skill)
    if not os.path.isdir(edir):
        r.error(rel(edir), "缺少评测目录：每个 skill 至少需要一个评测用例")
        return
    cases = [d for d in sorted(os.listdir(edir)) if os.path.isdir(os.path.join(edir, d))]
    if not cases:
        r.error(rel(edir), "评测目录为空")
        return
    has_negative = False
    for case in cases:
        cdir = os.path.join(edir, case)
        prompt = os.path.join(cdir, "prompt.md")
        case_yaml = os.path.join(cdir, "case.yaml")
        if not os.path.exists(prompt) and not os.path.exists(case_yaml):
            r.error(rel(cdir), "缺少 prompt.md 或 case.yaml")
            continue
        if os.path.exists(prompt):
            fm, body, err = split_frontmatter(read(prompt))
            if err and err != "缺少 YAML frontmatter":
                r.error(rel(prompt), err)
            if not body.strip():
                r.error(rel(prompt), "prompt 正文为空")
        if os.path.exists(case_yaml):
            try:
                cy = yaml.safe_load(read(case_yaml)) or {}
            except yaml.YAMLError as exc:
                r.error(rel(case_yaml), f"不是合法 YAML：{exc}")
                cy = {}
            if str(cy.get("schema_version")) != "1.1" or not cy.get("name"):
                r.error(rel(case_yaml), "case.yaml 需要 schema_version: \"1.1\" 与 name")
            script = (cy.get("context") or {}).get("scaffold_script")
            if script and not os.path.exists(os.path.join(cdir, script)):
                r.error(rel(case_yaml), f"scaffold_script `{script}` 不存在")
        for path in walk_files(cdir):
            if path.endswith((".md", ".yaml", ".sh")):
                m = PLACEHOLDER.search(read(path))
                if m:
                    r.error(rel(path), f"残留模板占位符 `{m.group(0)}`")
        gdir = os.path.join(cdir, "graders")
        graders = [g for g in sorted(os.listdir(gdir)) if g.endswith(".md")] if os.path.isdir(gdir) else []
        if not graders:
            r.error(rel(cdir), "至少需要一个 graders/*.md 评分器")
        for g in graders:
            gpath = os.path.join(gdir, g)
            fm, _, err = split_frontmatter(read(gpath))
            if err:
                r.error(rel(gpath), err)
                continue
            if fm.get("type") not in GRADER_TYPES:
                r.error(rel(gpath), f"type 须为 {sorted(GRADER_TYPES)} 之一")
            if fm.get("type") == "tool_used" and fm.get("tool") == "Skill" and fm.get("max") == 0:
                has_negative = True
    if not has_negative:
        r.warn(rel(edir), "建议至少一个反向用例（不该触发时 Skill 调用次数 max: 0），防止误触发")


# ---------------------------------------------------------------- links

def walk_files(top):
    for dirpath, dirnames, filenames in os.walk(top):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            yield os.path.join(dirpath, f)


def lint_links(r):
    for path in walk_files(ROOT):
        if not path.endswith(".md") or "/templates/" in path.replace(os.sep, "/"):
            continue
        text = read(path)
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)  # ignore code blocks
        for target in MD_LINK.findall(text):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            file_part = target.split("#", 1)[0]
            if not file_part:
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(path), file_part))
            if not os.path.exists(resolved):
                r.error(rel(path), f"链接目标不存在：`{target}`")


# ---------------------------------------------------------------- version bump

def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def lint_version_bump(r, ref, plugins):
    try:
        changed = git("diff", "--name-only", f"{ref}...HEAD").split()
    except subprocess.CalledProcessError as exc:
        r.error("git", f"无法与 `{ref}` 比较：{exc.stderr.strip()}")
        return
    for name in plugins:
        prefix = f"plugins/{name}/"
        touched = [c for c in changed if c.startswith(prefix)]
        if not touched:
            continue
        manifest = f"{prefix}.claude-plugin/plugin.json"
        try:
            old = json.loads(git("show", f"{ref}:{manifest}")).get("version")
        except (subprocess.CalledProcessError, ValueError):
            continue  # new plugin
        new = json.loads(read(os.path.join(ROOT, manifest))).get("version")
        if old == new:
            r.error(manifest, f"插件内容有改动（{len(touched)} 个文件）但版本仍为 {new}；请按 docs/release.md 升级版本并更新 CHANGELOG")


def main():
    for stream in (sys.stdout, sys.stderr):
        try:  # UTF-8 in CI logs and pipes even under a cp936 / GBK locale
            stream.reconfigure(errors="replace", **({} if stream.isatty() else {"encoding": "utf-8"}))
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--changed-since", metavar="REF", help="require version bumps for plugins changed since REF")
    args = ap.parse_args()

    r = Report()
    plugins = lint_marketplace(r)
    for name in plugins:
        lint_plugin(r, name)
    lint_links(r)
    if args.changed_since:
        lint_version_bump(r, args.changed_since, plugins)

    for w in r.warnings:
        print(f"WARN  {w}")
    for e in r.errors:
        print(f"ERROR {e}")
    failed = bool(r.errors) or (args.strict and bool(r.warnings))
    print(f"\n{len(plugins)} 个插件，{len(r.errors)} 个错误，{len(r.warnings)} 个警告 —— {'未通过' if failed else '通过'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
