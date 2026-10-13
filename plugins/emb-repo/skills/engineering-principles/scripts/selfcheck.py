#!/usr/bin/env python3
"""Check the shared core text, hook wiring and every injector output shape.

No network or Claude CLI is needed. Prints `FAIL ...` lines and exits 1 on failure.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
PLUGIN_DIR = SKILL_DIR.parents[1]
INJECT = SKILL_DIR / "scripts" / "inject_principles.py"
CORE = SKILL_DIR / "references" / "core-principles.md"
HOOK = PLUGIN_DIR / "hooks" / "hooks.json"
MANIFEST = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
SCRIPT_ARG = "${CLAUDE_PLUGIN_ROOT}/skills/engineering-principles/scripts/inject_principles.py"
HOOK_CMD = f'sh "${{CLAUDE_PLUGIN_ROOT}}/hooks/run-python.sh" "{SCRIPT_ARG}"'
OPTION = "CLAUDE_PLUGIN_OPTION_INJECT_PRINCIPLES"
SESSION_LIMIT = 4000   # well under Claude Code's 10,000-character hook output cap
DIGEST_LIMIT = 300
failures = []


def check(condition, message):
    if not condition:
        failures.append(message)
    return condition


def gbk_env(tmp):
    """Environment whose locale encoding is GBK (like cp936 on Chinese Windows), or None if unavailable."""
    if not shutil.which("localedef"):
        return None
    subprocess.run(["localedef", "-i", "zh_CN", "-f", "GBK", os.path.join(tmp, "zh_CN.GBK")], capture_output=True)
    env = dict(os.environ, LOCPATH=tmp, LC_ALL="zh_CN.GBK", PYTHONUTF8="0")
    probe = subprocess.run([sys.executable, "-c", "import locale;print(locale.getpreferredencoding(False))"],
                           capture_output=True, text=True, env=env)
    return env if probe.stdout.strip().upper() in ("GBK", "CP936") else None


def run(event, option=None, base_env=None):
    env = {k: v for k, v in (base_env or os.environ).items() if k != OPTION}
    if option is not None:
        env[OPTION] = option
    return subprocess.run([sys.executable, str(INJECT)], input=json.dumps({"hook_event_name": event}),
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5, env=env)


def main():
    core = CORE.read_text(encoding="utf-8").strip()
    check(150 <= len(core) <= SESSION_LIMIT, f"core-principles.md 长度 {len(core)} 不在 150~{SESSION_LIMIT} 字符")

    cfg = json.loads(HOOK.read_text(encoding="utf-8"))
    for event in ("SessionStart", "SubagentStart"):
        hooks = [h for entry in cfg["hooks"].get(event, []) for h in entry.get("hooks", [])]
        check(len(hooks) == 1, f"{event}: 应恰好有一个 hook")
        if hooks:
            h = hooks[0]
            check(h.get("type") == "command" and h.get("command") == HOOK_CMD and "args" not in h,
                  f"{event}: hook 须经 hooks/run-python.sh 调用 {SCRIPT_ARG}")

    option = json.loads(MANIFEST.read_text(encoding="utf-8")).get("userConfig", {}).get("inject_principles", {})
    check(option.get("type") == "boolean" and option.get("default") is True,
          "plugin.json 须声明 userConfig.inject_principles（boolean，默认 true）")

    a = run("SessionStart")
    check(a.returncode == 0 and a.stdout.strip() == core, "SessionStart 应原样输出 core-principles.md")

    b = run("SubagentStart")
    try:
        data = json.loads(b.stdout)["hookSpecificOutput"]
        text = data["additionalContext"]
        check(data["hookEventName"] == "SubagentStart", "SubagentStart: hookEventName 错误")
        check(0 < len(text) <= DIGEST_LIMIT, f"SubagentStart 精简版长度 {len(text)} 超过 {DIGEST_LIMIT}")
        check(text.count("；") >= 5, "SubagentStart 精简版应列出全部原则标题")
    except (ValueError, KeyError) as exc:
        check(False, f"SubagentStart 输出不是预期 JSON：{exc}")

    for value in ("false", "0", "off"):
        for event in ("SessionStart", "SubagentStart"):
            r = run(event, value)
            check(r.returncode == 0 and r.stdout == "", f"选项为 {value} 时 {event} 应静默")
    for value in ("true", "1"):
        check(run("SessionStart", value).stdout.strip() == core, f"选项为 {value} 时应注入")

    # Claude Code reads hook output as UTF-8; a cp936 / GBK locale (Chinese Windows) must not change that
    with tempfile.TemporaryDirectory() as tmp:
        env = gbk_env(tmp)
        if env is None:
            print("NOTE 未能生成 GBK locale，跳过本地编码用例")
        else:
            g = run("SessionStart", base_env=env)
            check(g.returncode == 0 and g.stdout.strip() == core, "GBK 本地编码下 SessionStart 仍应输出 UTF-8 原文")

    c = run("PostToolUse")
    check(c.returncode == 0 and c.stdout == "", "无关事件应静默")

    for f in failures:
        print("FAIL " + f)
    if failures:
        return 1
    print("PASS engineering-principles hooks: session, subagent digest, option off/on, unrelated event")
    return 0


if __name__ == "__main__":
    sys.exit(main())
