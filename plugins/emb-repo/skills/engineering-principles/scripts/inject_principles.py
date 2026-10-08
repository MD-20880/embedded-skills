#!/usr/bin/env python3
"""Inject a small, shared engineering-principles reference at Claude Code hook events.

Only local plugin files are read. No repository writes, network calls or decisions.
"""
import json
import sys
from pathlib import Path


CORE = Path(__file__).resolve().parent.parent / "references" / "core-principles.md"


def main():
    try:
        event = json.load(sys.stdin).get("hook_event_name")
    except (ValueError, AttributeError):
        return 0

    if event not in ("SessionStart", "SubagentStart"):
        return 0

    try:
        context = CORE.read_text(encoding="utf-8").strip()
    except OSError:
        return 0

    if not context:
        return 0

    if event == "SessionStart":
        print(context)
    else:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SubagentStart",
                "additionalContext": context,
            }
        }, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
