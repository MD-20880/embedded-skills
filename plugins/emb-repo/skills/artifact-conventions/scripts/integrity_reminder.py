#!/usr/bin/env python3
"""PostToolUse hook: remind Claude to maintain registry hashes after editing a managed file.

Runs after Edit / Write. If the edited file is listed in an engineering artifact
registry (docs/engineering-artifacts.yaml, found by walking up from the file)
that declares `integrity: sha256`, it adds a short context message:

- draft / active entry: run `registry_check.py update <id>` in the same change;
- superseded / archived entry: the file is frozen, revert the edit and tell the user.

Silent in every other case (no registry, integrity not enabled, file not listed,
option `integrity_reminders` off). Read-only: never edits, blocks or uses the network.
Standard library only, because it runs in users' environments without PyYAML.
"""
import json
import os
import re
import sys

REGISTRY = os.path.join("docs", "engineering-artifacts.yaml")
OPTION = "CLAUDE_PLUGIN_OPTION_INTEGRITY_REMINDERS"
OFF_VALUES = {"false", "0", "no", "off"}
FROZEN = {"superseded", "archived"}
SKILL_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "registry_check.py")


def find_registry(file_path):
    d = os.path.dirname(os.path.abspath(file_path))
    while True:
        candidate = os.path.join(d, REGISTRY)
        if os.path.isfile(candidate):
            return d, candidate
        parent = os.path.dirname(d)
        if parent == d:
            return None, None
        d = parent


def scalar(value):
    value = value.split(" #", 1)[0].strip()
    return value.strip("\"'")


def scan(text):
    """Minimal line scan of the registry: (integrity enabled?, [{id, path, status}])."""
    integrity = bool(re.search(r"^integrity\s*:\s*[\"']?sha256[\"']?\s*(#.*)?$", text, re.M))
    items, current, in_arts = [], None, False
    for line in text.splitlines():
        if re.match(r"^artifacts\s*:", line):
            in_arts = True
            continue
        if in_arts and re.match(r"^[^\s#-]", line):
            in_arts = False
        if not in_arts:
            continue
        m = re.match(r"^\s*(-\s+)?(id|path|status)\s*:\s*(.+)$", line)
        if re.match(r"^\s*-\s+", line):
            current = {}
            items.append(current)
        if m and current is not None:
            current[m.group(2)] = scalar(m.group(3))
    return integrity, items


def main():
    if os.environ.get(OPTION, "true").strip().lower() in OFF_VALUES:
        return 0
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    if event.get("hook_event_name") != "PostToolUse" or event.get("tool_name") not in ("Edit", "Write"):
        return 0
    file_path = (event.get("tool_input") or {}).get("file_path")
    if not file_path:
        return 0
    if not os.path.isabs(file_path):
        file_path = os.path.join(event.get("cwd") or os.getcwd(), file_path)
    root, registry = find_registry(file_path)
    if not registry or os.path.abspath(file_path) == os.path.abspath(registry):
        return 0  # no registry, or the registry itself was edited
    try:
        with open(registry, encoding="utf-8") as f:
            integrity, items = scan(f.read())
    except (OSError, UnicodeDecodeError):
        return 0
    if not integrity:
        return 0
    rel = os.path.relpath(os.path.abspath(file_path), root).replace(os.sep, "/")
    entry = next((e for e in items if e.get("path") == rel), None)
    if not entry:
        return 0
    aid, status = entry.get("id", "?"), entry.get("status", "?")
    project_copy = os.path.join(root, "tools", "registry_check.py")
    tool = project_copy if os.path.isfile(project_copy) else SKILL_SCRIPT
    if status in FROZEN:
        msg = (f"[artifact-conventions] 你刚修改的 {rel} 是受控文件 {aid}，状态为 {status}，在启用了 hash 校验的项目中已冻结，"
               f"CI 会拒绝这次修改。请撤销对该文件的修改，向用户说明它已冻结；如需变更，建议新建修订并用 supersedes 取代。"
               f"不要用 --allow-frozen 绕过，除非用户明确要求。")
    else:
        msg = (f"[artifact-conventions] 你刚修改的 {rel} 是受控文件 {aid}（{status}），项目启用了 hash 校验。"
               f"完成对它的修改后，在同一变更中运行：python3 {tool} update {aid} --root {root}，"
               f"再运行 check 确认通过；hash 更新不代表批准，汇报时如实说明。")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
