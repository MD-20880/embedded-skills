#!/usr/bin/env python3
"""Deterministic tests for registry_check.py (run by the repository lint).

Builds throw-away registries in a temporary directory and checks: opt-in,
missing / matching / changed hashes, update keeping comments and order,
frozen entries (with and without --base), CRLF normalization, Git LFS
pointers, binary files, duplicate ids and both YAML list indent styles.
Prints `FAIL ...` lines and exits 1 on failure.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "registry_check.py")
REMINDER = os.path.join(HERE, "integrity_reminder.py")
HOOKS = os.path.join(HERE, "..", "..", "..", "hooks", "hooks.json")
failures = []

REGISTRY = """schema_version: 1
integrity: sha256
types:
  specification: {purpose: "spec"}
  reference: {purpose: "datasheet"}
  design: {purpose: "design"}
artifacts:
  # 当前协议
  - id: SPEC-1
    type: specification
    path: docs/spec.md
    status: active
    scope: ["project"]
  - id: REF-1
    type: reference
    path: docs/chip.pdf
    status: active
    scope: ["board:a"]
  - id: OLD-1
    type: design
    path: docs/old.md
    status: archived
    scope: ["project"]
  - id: LFS-1
    type: reference
    path: docs/big.bin
    status: active
    scope: ["project"]
"""
LFS_OID = "a" * 64


def run(root, *args):
    return subprocess.run([sys.executable, TOOL, *args, "--root", root], capture_output=True, text=True)


def remind(root, rel, tool="Edit", option=None, env_pyyaml=True):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_OPTION_INTEGRITY_REMINDERS"}
    if option is not None:
        env["CLAUDE_PLUGIN_OPTION_INTEGRITY_REMINDERS"] = option
    payload = {"hook_event_name": "PostToolUse", "tool_name": tool, "cwd": root,
               "tool_input": {"file_path": os.path.join(root, rel)}}
    r = subprocess.run([sys.executable, "-S", REMINDER], input=json.dumps(payload), capture_output=True,
                       text=True, env=env)
    if r.returncode != 0 or not r.stdout.strip():
        return r.returncode, ""
    return r.returncode, json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]


def check(cond, msg):
    if not cond:
        failures.append(msg)


def write(root, rel, data):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data if isinstance(data, bytes) else data.encode())


def git(root, *args):
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=root,
                          capture_output=True, text=True)


def main():
    tmp = tempfile.mkdtemp(prefix="registry-selfcheck-")
    try:
        root = os.path.join(tmp, "repo")
        write(root, "docs/engineering-artifacts.yaml", REGISTRY)
        write(root, "docs/spec.md", "# Spec\nline\n")
        write(root, "docs/chip.pdf", b"%PDF-1.7\n\0\x01binary\r\n")
        write(root, "docs/old.md", "# Old design\n")
        write(root, "docs/big.bin", f"version https://git-lfs.github.com/spec/v1\noid sha256:{LFS_OID}\nsize 123\n")
        has_git = shutil.which("git") is not None and git(root, "init", "-q").returncode == 0

        r = run(root, "check")
        check(r.returncode == 1 and "缺少有效的 sha256" in r.stdout, "未写 hash 时 check 应失败并提示 update")

        r = run(root, "update", "--all")
        check(r.returncode == 0 and "已更新 OLD-1" in r.stdout and "已更新 SPEC-1" in r.stdout,
              "首次写入基线时，update --all 应同时为冻结条目写入 hash")
        text = open(os.path.join(root, "docs/engineering-artifacts.yaml"), encoding="utf-8").read()
        check("# 当前协议" in text, "update 应保留注释")
        check(text.index("SPEC-1") < text.index("REF-1") < text.index("OLD-1"), "update 应保留条目顺序")
        check(text.count("sha256:") == 4, "每个条目应恰好有一行 sha256")
        check(f"sha256: {LFS_OID}" in text, "LFS 指针文件应使用指针中的 oid")

        r = run(root, "check")
        check(r.returncode == 0, f"全部 hash 写入后 check 应通过：{r.stdout}")

        raw = b"%PDF-1.7\n\0\x01binary\r\n"
        check(f"sha256: {hashlib.sha256(raw).hexdigest()}" in text, "二进制文件应按原始字节计算，不做换行转换")

        write(root, "docs/crlf.md", "# Spec\r\nline\r\n")
        a = run(root, "hash", "docs/spec.md").stdout.split()[0]
        b = run(root, "hash", "docs/crlf.md").stdout.split()[0]
        check(a == b, "CRLF 与 LF 的同一文本应得到相同 hash")

        write(root, "docs/spec.md", "# Spec\nline changed\n")
        r = run(root, "check")
        check(r.returncode == 1 and "SPEC-1" in r.stdout and "update SPEC-1" in r.stdout, "内容变化后 check 应失败并指明 id")
        run(root, "update", "SPEC-1")
        check(run(root, "check").returncode == 0, "update 之后 check 应恢复通过")

        if has_git:
            git(root, "add", "-A")
            git(root, "commit", "-qm", "base")
            write(root, "docs/old.md", "# Old design, edited\n")
            r = run(root, "check")
            check(r.returncode == 1 and "已冻结" in r.stdout, "冻结文件内容变化应失败")
            r = run(root, "update", "OLD-1")
            check(r.returncode == 1 and "跳过 OLD-1" in r.stdout, "已有 hash 的冻结条目，update 默认应拒绝")
            r = run(root, "update", "OLD-1", "--allow-frozen")
            check(r.returncode == 0, "--allow-frozen 应允许改写冻结条目的 hash")
            r = run(root, "check")
            check(r.returncode == 0, "不带 --base 时，仅凭登记表无法发现冻结 hash 被改")
            r = run(root, "check", "--base", "HEAD")
            check(r.returncode == 1 and "已冻结" in r.stdout, "带 --base 时应发现冻结条目的 hash 被改")

        root2 = os.path.join(tmp, "flat")
        write(root2, "docs/engineering-artifacts.yaml",
              "integrity: sha256\ntypes:\n  design: {purpose: d}\nartifacts:\n- id: D-1\n  type: design\n"
              "  path: docs/d.md\n  status: draft\n  scope: [project]\n- id: D-1\n  type: design\n"
              "  path: docs/d.md\n  status: draft\n  scope: [project]\n")
        write(root2, "docs/d.md", "d\n")
        run(root2, "update", "--all")
        text2 = open(os.path.join(root2, "docs/engineering-artifacts.yaml"), encoding="utf-8").read()
        check(text2.count("  sha256: ") == 2, "无缩进列表写法也应正确插入 sha256")
        r = run(root2, "check")
        check(r.returncode == 1 and "id 重复" in r.stdout, "重复 id 应被发现")

        # ---- PostToolUse reminder（-S 运行：不加载 site-packages，确认不依赖 PyYAML）
        code, msg = remind(root, "docs/spec.md")
        check(code == 0 and "SPEC-1" in msg and "update SPEC-1" in msg, "编辑 active 受控文件后应提醒 update")
        code, msg = remind(root, "docs/old.md", tool="Write")
        check("已冻结" in msg and "撤销" in msg, "编辑冻结文件后应提醒撤销")
        check(remind(root, "docs/crlf.md")[1] == "", "未登记的文件应静默")
        check(remind(root, "docs/engineering-artifacts.yaml")[1] == "", "编辑登记表本身应静默")
        check(remind(root, "docs/spec.md", option="false")[1] == "", "选项关闭时应静默")
        check(remind(root, "docs/spec.md", tool="Read")[1] == "", "非 Edit / Write 工具应静默")
        check(remind(root2, "docs/d.md")[1] != "", "无缩进列表写法的登记表也应识别")
        hooks = json.load(open(HOOKS, encoding="utf-8"))["hooks"].get("PostToolUse", [])
        check(any(e.get("matcher") == "Edit|Write" and any(
            h.get("command") == "python3" and h.get("args", [""])[0].endswith("integrity_reminder.py")
            for h in e.get("hooks", [])) for e in hooks), "hooks.json 应以 exec 形式为 Edit|Write 注册提醒")

        root3 = os.path.join(tmp, "optout")
        write(root3, "docs/engineering-artifacts.yaml", "types: {}\nartifacts: []\n")
        r = run(root3, "check")
        check(r.returncode == 0 and "跳过" in r.stdout, "未声明 integrity 时 check 应跳过")
        r = run(root3, "update", "--all")
        check(r.returncode == 2, "未声明 integrity 时 update 应拒绝")
        write(root3, "docs/x.md", "x\n")
        check(remind(root3, "docs/x.md")[1] == "", "未启用 integrity 的项目不应提醒")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    for f in failures:
        print("FAIL " + f)
    if failures:
        return 1
    print("PASS registry_check + integrity_reminder: opt-in, hashes, update, frozen, CRLF, LFS, binary, duplicates, reminders")
    return 0


if __name__ == "__main__":
    sys.exit(main())
