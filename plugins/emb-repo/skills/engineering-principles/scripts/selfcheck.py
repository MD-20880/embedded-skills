#!/usr/bin/env python3
"""Check the shared core and both hook output shapes without network or Claude CLI."""
import json
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
PLUGIN_DIR = SKILL_DIR.parents[1]
INJECT = SKILL_DIR / "scripts" / "inject_principles.py"
CORE = SKILL_DIR / "references" / "core-principles.md"
HOOK = PLUGIN_DIR / "hooks" / "hooks.json"


def check(condition, message):
    if not condition:
        print("FAIL " + message)
        raise SystemExit(1)


def run(event):
    return subprocess.run(
        [sys.executable, str(INJECT)],
        input=json.dumps({"hook_event_name": event}),
        capture_output=True, text=True, encoding="utf-8", timeout=5,
        check=True,
    )


def main():
    core = CORE.read_text(encoding="utf-8").strip()
    check(len(core) >= 150, "core principles unexpectedly empty")
    cfg = json.loads(HOOK.read_text(encoding="utf-8"))
    for event in ("SessionStart", "SubagentStart"):
        entries = cfg["hooks"][event]
        check(len(entries) == 1 and len(entries[0]["hooks"]) == 1, event + " hook count")
        h = entries[0]["hooks"][0]
        check(h["type"] == "command" and h["command"] == "python3", event + " command")
        check(h["args"] == ["${CLAUDE_PLUGIN_ROOT}/skills/engineering-principles/scripts/inject_principles.py"], event + " script path")
    a = run("SessionStart")
    check(a.returncode == 0 and a.stdout.strip() == core, "SessionStart text mismatch")
    b = run("SubagentStart")
    value = json.loads(b.stdout)
    data = value["hookSpecificOutput"]
    check(data["hookEventName"] == "SubagentStart" and data["additionalContext"] == core, "SubagentStart context mismatch")
    c = run("PostToolUse")
    check(c.stdout == "" and c.returncode == 0, "other events should remain silent")
    print("PASS engineering-principles hooks: session, subagent, unrelated event")
    return 0


if __name__ == "__main__":
    sys.exit(main())
