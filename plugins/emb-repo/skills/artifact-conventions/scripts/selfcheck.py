#!/usr/bin/env python3
"""Deterministic tests for registry_check.py (run by the repository lint).

Builds throw-away registries in a temporary directory and checks: opt-in,
missing / matching / changed hashes, update keeping comments and order,
frozen entries (with and without --base), CRLF normalization, Git LFS
pointers, binary files, duplicate ids, both YAML list indent styles, and the
history / baseline traces over a throw-away git history.
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
    return subprocess.run([sys.executable, TOOL, *args, "--root", root], capture_output=True, text=True,
                          encoding="utf-8")


def remind(root, rel, tool="Edit", option=None, env_pyyaml=True, base_env=None, cmd=None):
    env = {k: v for k, v in (base_env or os.environ).items() if k != "CLAUDE_PLUGIN_OPTION_INTEGRITY_REMINDERS"}
    if option is not None:
        env["CLAUDE_PLUGIN_OPTION_INTEGRITY_REMINDERS"] = option
    payload = {"hook_event_name": "PostToolUse", "tool_name": tool, "cwd": root,
               "tool_input": {"file_path": os.path.join(root, rel)}}
    # Claude Code sends UTF-8 JSON on stdin, whatever the locale.
    r = subprocess.run(cmd or [sys.executable, "-S", REMINDER], input=json.dumps(payload, ensure_ascii=False),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if r.returncode != 0 or not r.stdout.strip():
        return r.returncode, ""
    return r.returncode, json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]


def gbk_env(tmp):
    """Environment whose locale encoding is GBK (like cp936 on Chinese Windows), or None if unavailable."""
    if not shutil.which("localedef"):
        return None
    locpath = os.path.join(tmp, "locales")
    os.makedirs(locpath, exist_ok=True)
    subprocess.run(["localedef", "-i", "zh_CN", "-f", "GBK", os.path.join(locpath, "zh_CN.GBK")],
                   capture_output=True)
    env = dict(os.environ, LOCPATH=locpath, LC_ALL="zh_CN.GBK", PYTHONUTF8="0")
    probe = subprocess.run([sys.executable, "-c", "import locale;print(locale.getpreferredencoding(False))"],
                           capture_output=True, text=True, env=env)
    return env if probe.stdout.strip().upper() in ("GBK", "CP936") else None


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
    for stream in (sys.stdout, sys.stderr):
        try:  # UTF-8 in CI logs and pipes even under a cp1252 / cp936 locale on Windows
            stream.reconfigure(errors="replace", **({} if stream.isatty() else {"encoding": "utf-8"}))
        except (AttributeError, ValueError):
            pass
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
            h.get("command", "").startswith('sh "${CLAUDE_PLUGIN_ROOT}/hooks/run-python.sh" ')
            and h["command"].endswith('/integrity_reminder.py"') for h in e.get("hooks", [])) for e in hooks),
            "hooks.json 应经 hooks/run-python.sh 为 Edit|Write 注册提醒")

        # ---- PR #6 评审回归用例
        # (1) 嵌套字段：source.sha256 与 source.id 不能被当成条目自己的字段
        root4 = os.path.join(tmp, "nested")
        write(root4, "docs/a.pdf", b"%PDF\0x")
        write(root4, "docs/engineering-artifacts.yaml",
              "integrity: sha256\ntypes:\n  reference: {purpose: r}\nartifacts:\n"
              "  - type: reference\n    source:\n      id: VENDOR-DS\n      sha256: " + "1" * 64 + "\n"
              "    id: REF-1\n    path: docs/a.pdf\n    status: active\n    scope: [project]\n")
        r = run(root4, "update", "REF-1")
        text4 = open(os.path.join(root4, "docs/engineering-artifacts.yaml"), encoding="utf-8").read()
        check(r.returncode == 0 and "      sha256: " + "1" * 64 in text4, "update 不得改写嵌套的 source.sha256")
        check(text4.count("\n    sha256: ") == 1, "update 应在条目这一层新增一行 sha256")
        check(run(root4, "check").returncode == 0, "嵌套 source 不影响 check")
        # 评审中的原始布局：id 在前，source 块在条目末尾
        write(root4, "docs/engineering-artifacts.yaml",
              "integrity: sha256\ntypes:\n  reference: {purpose: r}\nartifacts:\n"
              "  - id: REF-1\n    type: reference\n    path: docs/a.pdf\n    status: active\n    scope: [project]\n"
              "    source:\n      url: https://example.com/a.pdf\n      sha256: " + "1" * 64 + "\n")
        run(root4, "update", "REF-1")
        text4 = open(os.path.join(root4, "docs/engineering-artifacts.yaml"), encoding="utf-8").read()
        check("      sha256: " + "1" * 64 in text4 and text4.count("\n    sha256: ") == 1,
              "id 在前、source 在后时，update 也不得覆盖 source.sha256")
        # sha256 写在条目第一行的情况
        write(root4, "docs/engineering-artifacts.yaml",
              "integrity: sha256\ntypes:\n  reference: {purpose: r}\nartifacts:\n"
              "  - sha256: " + "0" * 64 + "\n    id: REF-1\n    type: reference\n    path: docs/a.pdf\n"
              "    status: active\n    scope: [project]\n")
        run(root4, "update", "REF-1")
        check(run(root4, "check").returncode == 0, "sha256 为条目首个字段时 update 也应正确改写")

        if has_git:
            # (2) 基线中已冻结的条目被整条删除
            root5 = os.path.join(tmp, "removed")
            write(root5, "docs/old.md", "old\n")
            write(root5, "docs/engineering-artifacts.yaml",
                  "integrity: sha256\ntypes:\n  design: {purpose: d}\nartifacts:\n  - id: OLD-1\n"
                  "    type: design\n    path: docs/old.md\n    status: archived\n    scope: [project]\n")
            git(root5, "init", "-q")
            run(root5, "update", "--all")
            git(root5, "add", "-A")
            git(root5, "commit", "-qm", "base")
            write(root5, "docs/old.md", "old, edited\n")
            write(root5, "docs/engineering-artifacts.yaml", "integrity: sha256\ntypes:\n  design: {purpose: d}\nartifacts: []\n")
            r = run(root5, "check", "--base", "HEAD")
            check(r.returncode == 1 and "OLD-1" in r.stdout and "删除" in r.stdout, "删除基线中已冻结的条目应失败")
            # (3) 基线引用无效 → 报错退出，不能静默通过
            git(root5, "checkout", "-q", "--", ".")
            r = run(root5, "check", "--base", "origin/not-fetched")
            check(r.returncode == 2 and "无法读取基线" in r.stderr, "无效基线应以退出码 2 报错")
            # 基线有效但其中还没有登记表（首次启用）→ 提示后继续
            root6 = os.path.join(tmp, "first-adoption")
            write(root6, "README.md", "x\n")
            git(root6, "init", "-q")
            git(root6, "add", "-A")
            git(root6, "commit", "-qm", "before registry")
            write(root6, "docs/d.md", "d\n")
            write(root6, "docs/engineering-artifacts.yaml",
                  "integrity: sha256\ntypes:\n  design: {purpose: d}\nartifacts:\n  - id: D-1\n"
                  "    type: design\n    path: docs/d.md\n    status: draft\n    scope: [project]\n")
            run(root6, "update", "--all")
            r = run(root6, "check", "--base", "HEAD")
            check(r.returncode == 0 and "首次启用" in r.stdout, "首次启用时基线没有登记表应提示并通过")

            # history / baseline：按提交追溯条目与文件的变化，导出某个引用上的基线
            rh = os.path.join(tmp, "history")
            reg = ("integrity: sha256\ntypes:\n  specification: {{purpose: s}}\nartifacts:\n  - id: S-1\n"
                   "    type: specification\n    path: {path}\n    status: {status}\n    scope: [project]\n"
                   "    revision: \"{rev}\"\n")
            write(rh, "docs/s.md", "v0\n")
            git(rh, "init", "-q")
            git(rh, "add", "-A")
            git(rh, "commit", "-qm", "before registry")
            write(rh, "docs/engineering-artifacts.yaml", reg.format(path="docs/s.md", status="draft", rev="0.1"))
            run(rh, "update", "S-1")
            git(rh, "add", "-A")
            git(rh, "commit", "-qm", "register")
            git(rh, "tag", "base")
            write(rh, "docs/s.md", "v1, unregistered\n")
            git(rh, "commit", "-qam", "edit without registry")
            r = run(rh, "baseline", "--ref", "HEAD")
            check(r.returncode == 1 and "不一致" in r.stdout, "baseline --ref 应发现该引用上文件与登记哈希不符")
            write(rh, "docs/engineering-artifacts.yaml", reg.format(path="docs/s.md", status="active", rev="1.0"))
            run(rh, "update", "S-1")
            git(rh, "commit", "-qam", "release 1.0")
            git(rh, "mv", "docs/s.md", "docs/spec.md")
            write(rh, "docs/engineering-artifacts.yaml", reg.format(path="docs/spec.md", status="active", rev="1.0"))
            run(rh, "update", "S-1")
            git(rh, "commit", "-qam", "move")
            r = run(rh, "history", "S-1")
            out = r.stdout
            check(r.returncode == 0, f"history 应成功：{r.stderr}")
            check("登记前" in out and "登记：draft" in out, "history 应列出登记前的文件提交和登记事件")
            check("没有更新登记" in out, "history 应标出改了文件却没更新登记的提交")
            move = [l for l in out.splitlines() if "路径 docs/s.md" in l]
            check(move and "没有更新登记" not in move[0], "纯改名且已更新登记的提交不应被标为未更新登记")
            check("版本 0.1 → 1.0" in out and "状态 draft → active" in out and "内容哈希" in out,
                  "history 应列出版本、状态与内容哈希的变化")
            check("路径 docs/s.md → docs/spec.md" in out, "history 应跟随登记表中的路径变化")
            check(out.index("before registry") < out.index("move"), "history 应按时间从早到晚排列")
            r = run(rh, "history", "S-1", "--markdown")
            check(r.stdout.count("\n| 20") >= 5, "history --markdown 应每个事件一行表格")
            check(run(rh, "history", "NOPE").returncode == 2, "history 未知 id 应以退出码 2 报错")
            r = run(rh, "baseline", "--ref", "base", "--markdown")
            check(r.returncode == 0 and "| S-1 |" in r.stdout and "0.1" in r.stdout and "一致" in r.stdout,
                  "baseline --ref 应输出该标签上的条目、版本与校验结果")
            r = run(rh, "baseline")
            check(r.returncode == 0 and "1.0" in r.stdout and "docs/spec.md" in r.stdout, "baseline 默认读取工作区")
            check(run(rh, "baseline", "--ref", "no-such-tag").returncode == 2, "baseline 无效引用应以退出码 2 报错")

        # (4) hook：多行 scope 列表、字段顺序不同、嵌套映射都不影响状态识别
        root7 = os.path.join(tmp, "hook-nested")
        write(root7, "docs/old.md", "old\n")
        write(root7, "docs/new.md", "new\n")
        write(root7, "docs/engineering-artifacts.yaml",
              "integrity: sha256\nartifacts:\n  - id: OLD-1\n    path: docs/old.md\n    type: design\n"
              "    scope:\n      - project\n      - board:rev-a\n    source:\n      status: active\n"
              "    status: archived\n  - path: docs/new.md\n    scope:\n      - project\n"
              "    id: NEW-1\n    status: draft\n")
        msg = remind(root7, "docs/old.md")[1]
        check("OLD-1" in msg and "archived" in msg and "撤销" in msg, "多行 scope 之后的 status 应归属正确的条目")
        msg = remind(root7, "docs/new.md")[1]
        check("NEW-1" in msg and "draft" in msg and "update NEW-1" in msg, "字段顺序不同的条目也应识别 id 与状态")

        # ---- PR #6 第二轮评审回归用例
        # (1) 本地编码为 GBK 时，读取含中文注释的基线登记表不得失败或被当成“首次启用”
        if has_git:
            root8 = os.path.join(tmp, "gbk")
            write(root8, "docs/a.md", "old\n")
            write(root8, "docs/engineering-artifacts.yaml",
                  "integrity: sha256\ntypes:\n  design: {purpose: d}\nartifacts:\n  # 当前协议\n  - id: A\n"
                  "    type: design\n    path: docs/a.md\n    status: archived\n    scope: [project]\n")
            git(root8, "init", "-q")
            run(root8, "update", "A")
            git(root8, "add", "-A")
            git(root8, "commit", "-qm", "base")
            write(root8, "docs/a.md", "old, edited\n")
            run(root8, "update", "A", "--allow-frozen")
            env = gbk_env(tmp)
            if env is None:
                print("NOTE 未能生成 GBK locale，跳过本地编码回归用例")
            else:
                r = subprocess.run([sys.executable, TOOL, "check", "--base", "HEAD", "--root", root8],
                                   capture_output=True, env=env)
                check(r.returncode == 1 and b"Traceback" not in r.stderr,
                      "GBK 本地编码下也应正确读取基线并发现冻结条目被改")
        # (2) 末尾没有换行的登记表：update 不得把 sha256 接在上一行后面
        root9 = os.path.join(tmp, "no-eol")
        write(root9, "docs/a.md", "a\n")
        write(root9, "docs/engineering-artifacts.yaml",
              "integrity: sha256\ntypes:\n  design: {purpose: d}\nartifacts:\n  - id: A\n    type: design\n"
              "    status: draft\n    scope: [project]\n    path: docs/a.md")
        r = run(root9, "update", "A")
        check(r.returncode == 0 and run(root9, "check").returncode == 0, "末尾无换行时 update 后登记表仍应合法且通过 check")
        # (3) flow-style 条目：update 不得静默成功，登记表保持不变；hook 仍能识别
        root10 = os.path.join(tmp, "flow")
        write(root10, "docs/old.md", "old\n")
        flow = ("integrity: sha256\ntypes:\n  design: {purpose: d}\nartifacts:\n"
                "  - {id: OLD-1, path: docs/old.md, type: design, status: archived, scope: [project, board]}\n")
        write(root10, "docs/engineering-artifacts.yaml", flow)
        r = run(root10, "update", "OLD-1")
        after = open(os.path.join(root10, "docs/engineering-artifacts.yaml"), encoding="utf-8").read()
        check(r.returncode == 1 and "OLD-1" in r.stdout and after == flow, "flow-style 条目应明确报错且不修改登记表")
        msg = remind(root10, "docs/old.md")[1]
        check("OLD-1" in msg and "archived" in msg, "hook 应能识别单行 flow-style 条目")

        # 带 UTF-8 BOM 的登记表（Windows 记事本常见）：hook 仍应识别 integrity 并提醒
        root11 = os.path.join(tmp, "bom")
        write(root11, "docs/a.md", "a\n")
        write(root11, "docs/engineering-artifacts.yaml",
              b"\xef\xbb\xbfintegrity: sha256\ntypes:\n  design: {purpose: d}\nartifacts:\n  - id: A\n"
              b"    type: design\n    path: docs/a.md\n    status: draft\n    scope: [project]\n")
        check("update A" in remind(root11, "docs/a.md")[1], "登记表带 BOM 时 hook 仍应提醒")
        check(run(root11, "update", "A").returncode == 0 and run(root11, "check").returncode == 0,
              "登记表带 BOM 时 update / check 应正常")

        # ---- Windows 相关回归用例
        body = ("integrity: sha256\ntypes:\n  design: {purpose: d}\nartifacts:\n  - id: A\n"
                "    type: design\n    path: docs/a.md\n    status: draft\n    scope: [project]\n")
        # (1) update 保留登记表原有换行符（Windows 上文本模式写回会把 LF 全部改成 CRLF）
        for name, nl in (("crlf-registry", "\r\n"), ("lf-registry", "\n")):
            r12 = os.path.join(tmp, name)
            write(r12, "docs/a.md", "a\n")
            write(r12, "docs/engineering-artifacts.yaml", body.replace("\n", nl))
            ok = run(r12, "update", "A").returncode == 0 and run(r12, "check").returncode == 0
            raw = open(os.path.join(r12, "docs/engineering-artifacts.yaml"), "rb").read()
            kept = raw.count(b"\r\n") == (raw.count(b"\n") if nl == "\r\n" else 0)
            check(ok and kept and b"sha256:" in raw, f"update 应保留登记表的 {name.split('-')[0].upper()} 换行")
        # (2) 项目路径含中文：hook 按 UTF-8 读 stdin（在 Windows CI 上，本地编码不是 UTF-8，此项才真正生效）
        root13 = os.path.join(tmp, "中文目录")
        write(root13, "docs/a.md", "a\n")
        write(root13, "docs/engineering-artifacts.yaml", body)
        check("update A" in remind(root13, "docs/a.md")[1], "项目路径含中文时 hook 应提醒")
        # GBK 本地编码下 hook 的输出仍须是 Claude Code 能按 UTF-8 读的内容。Linux 上 GBK locale 会按 GBK
        # 编码文件名而找不到 UTF-8 创建的中文目录（Windows 文件接口始终是 Unicode，无此问题），所以这里用 ASCII 路径
        env = gbk_env(tmp)
        if env is None:
            print("NOTE 未能生成 GBK locale，跳过 hook 的本地编码回归用例")
        else:
            msg = remind(root, "docs/spec.md", base_env=env)[1]
            check("update SPEC-1" in msg and "受控文件" in msg, "GBK 本地编码下 hook 输出的中文应能按 UTF-8 正确解析")
        # (3) hooks/run-python.sh：python3 不可用（如 Windows 只装了 python / py）时改用其他候选
        launcher = os.path.normpath(os.path.join(HERE, "..", "..", "..", "hooks", "run-python.sh"))
        sh = shutil.which("sh")
        if sh is None:
            print("NOTE 未找到 sh，跳过 run-python.sh 用例")
        else:
            via = [sh, launcher, REMINDER]
            check("update A" in remind(root13, "docs/a.md", cmd=via)[1], "经 run-python.sh 启动时 hook 应提醒")
            if os.name != "nt":  # fake interpreters below are POSIX shell scripts
                fake = os.path.join(tmp, "fakebin")
                write(fake, "python3", "#!/bin/sh\nexit 9009\n")  # like the Microsoft Store stub
                write(fake, "python", f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
                for f in ("python3", "python"):
                    os.chmod(os.path.join(fake, f), 0o755)
                env = dict(os.environ, PATH=fake + os.pathsep + os.environ.get("PATH", ""))
                check("update A" in remind(root13, "docs/a.md", base_env=env, cmd=via)[1],
                      "python3 不可用时 run-python.sh 应改用 python")
                os.remove(os.path.join(fake, "python"))
                code, _ = remind(root13, "docs/a.md", base_env=dict(os.environ, PATH=fake), cmd=via)
                check(code == 1, "找不到任何可用 Python 时 run-python.sh 应以非零退出（让 Claude Code 显示 hook 错误）")

        root3 = os.path.join(tmp, "optout")
        write(root3, "docs/engineering-artifacts.yaml", "types: {}\nartifacts: []\n")
        r = run(root3, "check")
        check(r.returncode == 0 and "跳过" in r.stdout, "未声明 integrity 时 check 应跳过")
        r = run(root3, "update", "--all")
        check(r.returncode == 2, "未声明 integrity 时 update 应拒绝")
        write(root3, "docs/x.md", "x\n")
        check(remind(root3, "docs/x.md")[1] == "", "未启用 integrity 的项目不应提醒")

        # relations: works without integrity; FAIL vs WARN; layer defaults from type, entry override
        root4 = os.path.join(tmp, "relations")
        rel_head = """schema_version: 1
layers:
  product: {may_depend_on: []}
  system: {may_depend_on: [product, module, interface]}
  module: {may_depend_on: [product, interface]}
  interface: {may_depend_on: [product]}
types:
  requirement: {purpose: r, layer: product}
  design: {purpose: d, layer: module}
  specification: {purpose: s, layer: interface}
  verification: {purpose: v}
artifacts:
  - {id: REQ-1, type: requirement, path: r.md, status: active, scope: [project]}
  - {id: IF-1, type: specification, path: i.md, status: active, scope: [project]}
  - {id: AUD-1, type: design, path: a.md, status: active, scope: [project], depends_on: [IF-1], refines: REQ-1}
  - {id: SYS-1, type: design, layer: system, path: s.md, status: draft, scope: [project], depends_on: [AUD-1, IF-1]}
  - {id: VER-1, type: verification, path: v.md, status: draft, scope: [project], verifies: [SYS-1]}
"""
        write(root4, "docs/engineering-artifacts.yaml", rel_head)
        r = run(root4, "relations")
        check(r.returncode == 0 and "FAIL" not in r.stdout and "WARN" not in r.stdout and "5 条关系" in r.stdout,
              f"合规的关系应通过且无提醒：{r.stdout}")
        r = run(root4, "check")
        check(r.returncode == 0 and "跳过" in r.stdout, "增加关系字段后，未声明 integrity 的 check 行为不变")
        r = run(root4, "relations", "--of", "AUD-1")
        check("依赖 IF-1" in r.stdout and "细化 REQ-1" in r.stdout and "SYS-1 依赖" in r.stdout,
              f"--of 应列出指向与被指向：{r.stdout}")
        r = run(root4, "relations", "--of", "AUD-1", "--markdown")
        check("| 被指向 | 依赖 | SYS-1 |" in r.stdout, "--of --markdown 应输出表格")
        write(root4, "docs/engineering-artifacts.yaml", rel_head + """  - {id: NFC-1, type: design, path: n.md, status: draft, scope: [project], depends_on: [AUD-1, SYS-1]}
  - {id: X-1, type: design, path: x.md, status: draft, scope: [project], depends_on: X-2}
  - {id: X-2, type: design, layer: system, path: y.md, status: draft, scope: [project], depends_on: [X-1]}
""")
        r = run(root4, "relations")
        check(r.returncode == 0 and "WARN NFC-1（module）depends_on AUD-1（module）" in r.stdout
              and "WARN NFC-1（module）depends_on SYS-1（system）" in r.stdout,
              f"模块依赖模块、模块依赖系统层应只提醒：{r.stdout}")
        check("WARN depends_on 成环" in r.stdout, "depends_on 成环应只提醒")
        write(root4, "docs/engineering-artifacts.yaml", rel_head + """  - {id: OLD-1, type: design, path: o.md, status: superseded, scope: [project], supersedes: NEW-1}
  - {id: NEW-1, type: design, path: n.md, status: active, scope: [project], supersedes: [OLD-1]}
  - {id: BAD-1, type: design, layer: board, path: b.md, status: draft, scope: [project], depends_on: [GONE-1, BAD-1], verifies: 3}
""")
        r = run(root4, "relations")
        for frag, msg in (("FAIL supersedes 成环", "supersedes 成环应失败"),
                          ("`GONE-1` 不在登记表中", "指向不存在的编号应失败"),
                          ("BAD-1: depends_on 指向自己", "自指应失败"),
                          ("BAD-1: verifies 应为编号或编号列表", "非法取值应失败"),
                          ("层 `board` 未在 layers 中声明", "未声明的层应失败")):
            check(frag in r.stdout, msg)
        check(r.returncode == 1, "有 FAIL 时 relations 应以 1 退出")
        write(root4, "docs/engineering-artifacts.yaml", rel_head.replace("layers:", "old_layers:"))
        r = run(root4, "relations")
        check(r.returncode == 0 and "WARN" not in r.stdout, "未声明 layers 时不做方向检查")
        chain = "".join(f"  - {{id: C{i}, type: design, path: c.md, status: draft, scope: [project]"
                        f"{', depends_on: [C%d]' % (i + 1) if i < 1999 else ''}}}\n" for i in range(2000))
        write(root4, "docs/engineering-artifacts.yaml", "types: {design: {purpose: d}}\nartifacts:\n" + chain)
        r = run(root4, "relations")
        check(r.returncode == 0 and "1999 条关系" in r.stdout, f"2000 个条目的长依赖链不应超出递归深度：{r.stderr[-200:]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    for f in failures:
        print("FAIL " + f)
    if failures:
        return 1
    print("PASS registry_check + integrity_reminder: opt-in, hashes, update, frozen, CRLF, LFS, binary, duplicates, history, baseline, relations, reminders, review regressions (2 rounds)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
