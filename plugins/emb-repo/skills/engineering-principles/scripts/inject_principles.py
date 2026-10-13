#!/usr/bin/env python3
"""Inject the shared engineering principles at Claude Code hook events.

- SessionStart: the full light-weight text of references/core-principles.md.
- SubagentStart: a one-line digest built from the same file (the bold rule
  titles), so subagents doing narrow tasks pay only a few dozen tokens.
- Disabled when the plugin option `inject_principles` is off
  (exported by Claude Code as CLAUDE_PLUGIN_OPTION_INJECT_PRINCIPLES).

Only local plugin files are read. No repository writes, network calls or decisions.
"""
import json
import os
import re
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parent.parent / "references" / "core-principles.md"
OPTION = "CLAUDE_PLUGIN_OPTION_INJECT_PRINCIPLES"
OFF_VALUES = {"false", "0", "no", "off"}


def enabled():
    return os.environ.get(OPTION, "true").strip().lower() not in OFF_VALUES


def digest(core):
    """One line listing the numbered rule titles, e.g. '1. **角色分明**：…' -> '角色分明'."""
    titles = re.findall(r"^\d+\.\s*\*\*(.+?)\*\*", core, re.MULTILINE)
    return ("工程默认原则（精简，来自 emb-repo）：" + "；".join(titles)
            + "。项目正式约束和用户要求优先；普通任务保持轻量，复杂工程判断可调用 /emb-repo:engineering-principles。")


def main():
    try:  # Claude Code sends UTF-8; do not decode with the locale (cp936 / GBK on Chinese Windows)
        event = json.loads(sys.stdin.buffer.read().decode("utf-8")).get("hook_event_name")
    except (ValueError, AttributeError):
        return 0
    if event not in ("SessionStart", "SubagentStart") or not enabled():
        return 0
    try:
        core = CORE.read_text(encoding="utf-8").strip()
    except OSError:
        return 0
    if not core:
        return 0

    # Write bytes: print() would use the locale encoding on Windows, while Claude Code reads UTF-8.
    if event == "SessionStart":
        sys.stdout.buffer.write(core.encode("utf-8") + b"\n")
    else:
        sys.stdout.buffer.write(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SubagentStart",
                "additionalContext": digest(core),
            }
        }).encode("ascii") + b"\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
