#!/usr/bin/env python3
"""Collect machine-detectable evidence for an embedded project profile.

Usage:
    scan_repo.py [ROOT]                   # print evidence as Markdown
    scan_repo.py [ROOT] --json            # print evidence as JSON
    scan_repo.py [ROOT] --check PROFILE   # report stale paths / presets in PROFILE

Only the Python standard library is used, so the script runs in any project.
It never modifies files.
"""

import argparse
import json
import os
import re
import sys

SKIP_DIRS = {
    ".git", ".svn", "node_modules", "out", "build", "builds", "dist", "prebuilds",
    ".venv", "venv", "__pycache__", ".cache", ".idea", ".vscode-test",
}
MAX_FILES = 50000
MAX_LIST = 20

# (category, regex over the repo-relative path)
SIGNALS = [
    ("readme", r"(^|/)(README|CLAUDE|AGENTS|CONTRIBUTING)[^/]*\.md$"),
    ("build", r"(^|/)(CMakePresets\.json|CMakeLists\.txt|Makefile|[^/]+\.mk|platformio\.ini|west\.yml|meson\.build|SConstruct)$"),
    ("ide_project", r"\.(uvprojx|uvproj|ewp|wvproj|cproject)$"),
    ("toolchain", r"(^|/)(toolchain[^/]*\.cmake|toolchains?\.json|setup\.py)$"),
    ("linker_script", r"\.(ld|lds|icf|sct)$"),
    ("startup", r"(^|/)startup_[^/]+\.(s|S|c)$"),
    ("mcu_config", r"(^|/)([^/]+\.ioc|sdkconfig|prj\.conf|system_[^/]+\.c|[^/]+_hal_conf\.h|[^/]+_conf\.h)$"),
    ("rtos_config", r"(^|/)(FreeRTOSConfig\.h|rtconfig\.h|tx_user\.h|tx_port\.h)$"),
    ("debug_config", r"(\.jlink$|(^|/)openocd[^/]*\.cfg$|\.launch$|(^|/)launch\.json$)"),
    ("ci", r"(^|/)(\.github/workflows/[^/]+\.ya?ml|\.gitlab-ci\.yml|Jenkinsfile)$"),
    ("style", r"(^|/)(\.clang-format|\.clang-tidy|\.editorconfig|cppcheck[^/]*)$"),
    ("doc_hardware", r"\.pdf$"),
]
TOP_DIR_HINTS = [
    "boards", "bsp", "board", "targets", "platform", "platforms", "drivers", "components",
    "apps", "app", "examples", "vendor", "third_party", "lib", "libs", "tests", "test",
    "validation", "tools", "docs", "doc", "cmake", "firmware", "src", "include",
]
# Path segments that mark vendored code (SDK examples, third-party libraries).
# Hits inside them are only counted, so the project's own files stay visible.
VENDOR_SEGMENTS = {
    "vendor", "vendors", "third_party", "thirdparty", "third-party", "external", "extern",
    "deps", "sdk", "SDK", "Middlewares", "managed_components", "submodules",
}
MEMORY_RE = re.compile(
    r"^\s*(\w+)\s*(?:\([^)]*\))?\s*:\s*(?:ORIGIN|org|o)\s*=\s*(0x[0-9A-Fa-f]+)\s*,\s*"
    r"(?:LENGTH|len|l)\s*=\s*([0-9A-Fa-fxX]+\s*[KkMm]?)",
    re.MULTILINE,
)
CLOCK_RE = re.compile(r"^[ \t]*#define\s+(SystemCoreClock|HSE_VALUE|SYSCLK_FREQ\w*|configCPU_CLOCK_HZ)\s+\(?\s*([^\s/)]+)", re.MULTILINE)
ARCH_RE = re.compile(r"-m(cpu|arch)=([\w+.-]+)")
MAX_PARSE = 60  # files parsed per category for MEMORY / clock extraction


def walk(root):
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames
            if (d not in SKIP_DIRS and not d.startswith(".")) or d in (".github", ".claude", ".vscode")
        )
        for name in sorted(filenames):
            count += 1
            if count > MAX_FILES:
                return
            full = os.path.join(dirpath, name)
            yield os.path.relpath(full, root).replace(os.sep, "/")


def read_text(root, rel, limit=200_000):
    try:
        with open(os.path.join(root, rel), "r", encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except OSError:
        return ""


def is_vendored(rel):
    return any(seg in VENDOR_SEGMENTS for seg in rel.split("/")[:-1])


def collect(root):
    files = list(walk(root))
    evidence = {"root": os.path.abspath(root), "file_count": len(files), "top_dirs": [], "signals": {}}
    try:
        tops = sorted(e for e in os.listdir(root) if os.path.isdir(os.path.join(root, e)) and not e.startswith("."))
    except OSError:
        tops = []
    evidence["top_dirs"] = [
        {"dir": d, "children": sorted(c for c in os.listdir(os.path.join(root, d)) if not c.startswith("."))[:MAX_LIST]}
        if d in TOP_DIR_HINTS else {"dir": d}
        for d in tops
    ]
    own_hits = {}
    for cat, pattern in SIGNALS:
        rx = re.compile(pattern)
        hits = [f for f in files if rx.search(f)]
        if not hits:
            continue
        own = [f for f in hits if not is_vendored(f)]
        own_hits[cat] = own
        evidence["signals"][cat] = {"own_count": len(own), "own_paths": own[:MAX_LIST],
                                    "vendored_count": len(hits) - len(own)}

    presets = {}
    for rel in own_hits.get("build", []):
        if not rel.endswith("CMakePresets.json"):
            continue
        try:
            data = json.loads(read_text(root, rel))
        except ValueError:
            continue
        for kind in ("configurePresets", "buildPresets", "testPresets", "workflowPresets"):
            for p in data.get(kind, []):
                if p.get("hidden") or not p.get("name"):
                    continue
                entry = presets.setdefault(p["name"], {"name": p["name"], "file": rel, "kinds": [], "displayName": ""})
                entry["kinds"].append(kind.replace("Presets", ""))
                entry["displayName"] = entry["displayName"] or p.get("displayName", "")
    if presets:
        evidence["cmake_presets"] = [dict(v, kinds="/".join(v["kinds"])) for v in presets.values()]

    memories = []
    for rel in own_hits.get("linker_script", [])[:MAX_PARSE]:
        regions = {}
        for name, origin, length in MEMORY_RE.findall(read_text(root, rel)):
            sizes = regions.setdefault((name, origin), [])
            if length.replace(" ", "") not in sizes:
                sizes.append(length.replace(" ", ""))
        for (name, origin), sizes in regions.items():
            item = {"file": rel, "region": name, "origin": origin, "length": "/".join(sizes)}
            if len(sizes) > 1:
                item["note"] = "多个条件编译变体，需确认实际生效的一个"
            memories.append(item)
    if memories:
        evidence["memory_regions"] = memories[:MAX_LIST * 2]

    clocks, archs = [], set()
    for cat in ("mcu_config", "rtos_config"):
        for rel in own_hits.get(cat, [])[:MAX_PARSE]:
            for macro, value in CLOCK_RE.findall(read_text(root, rel)):
                clocks.append({"file": rel, "macro": macro, "value": value})
    for rel in files:
        if rel.endswith((".cmake", "CMakeLists.txt", "Makefile", ".mk")) and not is_vendored(rel):
            for flag, value in ARCH_RE.findall(read_text(root, rel, 50_000)):
                archs.add((f"-m{flag}", value, rel))
    if clocks:
        evidence["clock_defines"] = clocks[:MAX_LIST]
    if archs:
        evidence["arch_flags"] = [{"flag": f, "value": v, "file": p} for f, v, p in sorted(archs)][:MAX_LIST]
    return evidence


def to_markdown(ev):
    out = [f"# 扫描结果：{ev['root']}", "", f"文件数：{ev['file_count']}", "", "## 顶层目录", ""]
    for d in ev["top_dirs"]:
        kids = d.get("children")
        out.append(f"- `{d['dir']}/`" + (f"：{', '.join(kids)}" if kids else ""))
    out += ["", "## 信号文件（项目自有；厂商 / 第三方目录只计数）", ""]
    for cat, info in ev["signals"].items():
        notes = []
        if info["own_count"] > MAX_LIST:
            notes.append(f"自有共 {info['own_count']} 个，仅列前 {MAX_LIST}")
        if info["vendored_count"]:
            notes.append(f"另有 {info['vendored_count']} 个位于厂商 / 第三方目录")
        paths = ", ".join(f"`{p}`" for p in info["own_paths"]) or "（无自有文件）"
        out.append(f"- **{cat}**" + (f"（{'；'.join(notes)}）" if notes else "") + f"：{paths}")
    for key, title in (("cmake_presets", "CMake presets"), ("memory_regions", "链接脚本 MEMORY"),
                       ("clock_defines", "时钟宏"), ("arch_flags", "-mcpu / -march 标志")):
        if key in ev:
            out += ["", f"## {title}", ""]
            for item in ev[key]:
                out.append("- " + ", ".join(f"{k}={v}" for k, v in item.items() if v))
    out += ["", "> 以上为机械扫描线索，写入画像前需阅读对应文件确认。"]
    return "\n".join(out)


def check(root, profile_path):
    """Report backticked paths and preset names in the profile that no longer exist."""
    text = read_text(root, profile_path) if not os.path.isabs(profile_path) else open(profile_path, encoding="utf-8").read()
    if not text:
        print(f"未找到画像文件：{profile_path}")
        return 2
    problems = []
    for token in sorted(set(re.findall(r"`([^`\s]+)`", text))):
        looks_like_path = "/" in token or re.search(r"\.(md|json|txt|cmake|c|h|ld|py|ini|yml|yaml)$", token)
        if looks_like_path and not token.startswith(("http", "-", "$", "<")) and "*" not in token:
            if not os.path.exists(os.path.join(root, token.rstrip("/"))):
                problems.append(f"路径不存在：`{token}`")
    preset_names = {p["name"] for p in collect(root).get("cmake_presets", [])}
    for name in sorted(set(re.findall(r"--preset[ =]+([\w.-]+)", text))):
        if preset_names and name not in preset_names:
            problems.append(f"preset 不存在：`{name}`")
    m = re.search(r"^updated:\s*(\S+)", text, re.MULTILINE)
    print(f"画像最后核对日期：{m.group(1) if m else '未填写'}")
    if problems:
        print("发现过期项：")
        for p in problems:
            print(f"- {p}")
        return 1
    print("未发现过期的路径或 preset。")
    return 0


def main():
    for stream in (sys.stdout, sys.stderr):
        try:  # pipes (Claude Code's Bash tool, CI logs) get UTF-8 even under a cp1252 / cp936 locale on Windows
            stream.reconfigure(errors="replace", **({} if stream.isatty() else {"encoding": "utf-8"}))
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    ap.add_argument("--check", metavar="PROFILE", help="check a profile for stale paths and presets")
    args = ap.parse_args()
    if not os.path.isdir(args.root):
        print(f"不是目录：{args.root}", file=sys.stderr)
        return 2
    if args.check:
        return check(args.root, args.check)
    ev = collect(args.root)
    print(json.dumps(ev, ensure_ascii=False, indent=2) if args.json else to_markdown(ev))
    return 0


if __name__ == "__main__":
    sys.exit(main())
