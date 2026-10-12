#!/usr/bin/env python3
"""Integrity check for a project's engineering artifact registry.

The registry (default docs/engineering-artifacts.yaml) opts in with
`integrity: sha256`; each artifact entry then carries `sha256: <hex>` written
by this tool. CI runs `check`; people and agents run `update` after an
intentional change to a managed file.

Usage:
    registry_check.py check  [--registry PATH] [--root DIR] [--base REF]
    registry_check.py update [--registry PATH] [--root DIR] (--all | ID ...) [--allow-frozen]
    registry_check.py hash   [--root DIR] PATH ...

check   Every entry's path exists, its type is declared, ids are unique, and
        the file content matches the recorded sha256. With --base REF (for
        example origin/main in a PR), entries that were already superseded or
        archived at REF must keep the same sha256: their content is frozen.
update  Recompute and write sha256 for the given ids (or --all). Refuses to
        change the hash of a superseded / archived entry that already has one,
        unless --allow-frozen (writing a first baseline hash is allowed). Only the
        `sha256:` line of each entry is touched; comments and order are kept.
hash    Print the normalized sha256 of files (for debugging).

Hashing: Git LFS pointer files contribute their recorded `oid sha256:`; files
tracked by LFS or containing NUL bytes are hashed as raw bytes (matching the
LFS oid); other files are treated as text and CRLF/CR are normalized to LF so
Windows and Linux checkouts agree.

A changed hash only shows that a managed file changed. It is not an approval;
pair it with review rules such as CODEOWNERS on the registry if needed.

Exit status: 0 ok, 1 problems found, 2 usage or configuration error.
Requires PyYAML for reading the registry (pip install pyyaml).
Copied into a project, this file is self-contained.

Origin: github.com/MD-20880/embedded-skills,
plugins/emb-repo/skills/artifact-conventions/scripts/registry_check.py.
When upgrading a project copy, replace the whole file.
"""

import argparse
import hashlib
import os
import re
import subprocess
import sys

TOOL_VERSION = "1.0"
DEFAULT_REGISTRY = "docs/engineering-artifacts.yaml"
FROZEN = {"superseded", "archived"}
LFS_POINTER = re.compile(rb"^version https://git-lfs\.github\.com/spec/v1\n(?:.*\n)*?oid sha256:([0-9a-f]{64})\n", re.M)
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def die(msg):
    print(f"ERROR {msg}", file=sys.stderr)
    sys.exit(2)


def load_yaml(text, where):
    try:
        import yaml
    except ImportError:
        die("需要 PyYAML 才能读取登记表：pip install pyyaml")
    try:
        data = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        die(f"{where} 不是合法 YAML：{exc}")
    if not isinstance(data, dict):
        die(f"{where} 顶层必须是映射")
    return data


def git(root, *args):
    try:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None


def lfs_tracked(root, rel):
    out = git(root, "check-attr", "filter", "--", rel)
    return bool(out) and out.strip().endswith(": lfs")


def file_hash(root, rel):
    with open(os.path.join(root, rel), "rb") as f:
        data = f.read()
    m = LFS_POINTER.match(data) if len(data) < 1024 else None
    if m:
        return m.group(1).decode()
    if b"\0" not in data and not lfs_tracked(root, rel):
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def read_registry(root, registry):
    path = os.path.join(root, registry)
    if not os.path.isfile(path):
        die(f"找不到登记表：{registry}")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return text, load_yaml(text, registry)


def entries(data):
    arts = data.get("artifacts") or []
    if not isinstance(arts, list):
        die("artifacts 必须是列表")
    return [a for a in arts if isinstance(a, dict)]


# ------------------------------------------------------------------ check

def cmd_check(args):
    text, data = read_registry(args.root, args.registry)
    if data.get("integrity") != "sha256":
        print(f"{args.registry} 未声明 integrity: sha256，跳过完整性检查。")
        return 0
    problems = []
    types = data.get("types") or {}
    seen = {}
    base_hash = {}
    if args.base:
        old = git(args.root, "show", f"{args.base}:{args.registry}")
        if old is not None:
            for e in entries(load_yaml(old, f"{args.base}:{args.registry}")):
                if e.get("status") in FROZEN and e.get("id"):
                    base_hash[e["id"]] = e.get("sha256")
    for e in entries(data):
        aid, path, status = e.get("id"), e.get("path"), e.get("status")
        label = aid or f"<无 id，path={path}>"
        if not aid:
            problems.append(f"{label}: 缺少 id")
        elif aid in seen:
            problems.append(f"{aid}: id 重复")
        seen[aid] = True
        if e.get("type") not in types:
            problems.append(f"{label}: type `{e.get('type')}` 未在 types 中声明")
        if not e.get("scope"):
            problems.append(f"{label}: scope 为空")
        if not path or not os.path.isfile(os.path.join(args.root, path)):
            problems.append(f"{label}: 路径不存在：{path}")
            continue
        recorded = str(e.get("sha256") or "")
        if not HEX64.match(recorded):
            problems.append(f"{label}: 缺少有效的 sha256；确认内容后运行 `update {aid}`")
            continue
        actual = file_hash(args.root, path)
        if aid in base_hash and base_hash[aid] and recorded != base_hash[aid]:
            problems.append(f"{label}: 状态为 {status} 的文件已冻结，但登记的 sha256 被修改；"
                            "应新建修订并用 supersedes 取代，而不是改动原文件")
        elif actual != recorded:
            if status in FROZEN:
                problems.append(f"{label}: 状态为 {status} 的文件已冻结，内容却发生了变化（{path}）")
            else:
                problems.append(f"{label}: 内容与登记的 sha256 不一致（{path}）；"
                                f"如属有意修改，运行 `update {aid}` 并在同一变更中提交")
    for p in problems:
        print(f"FAIL {p}")
    n = len(entries(data))
    print(f"{args.registry}: {n} 个条目，{len(problems)} 个问题 —— {'未通过' if problems else '通过'}")
    return 1 if problems else 0


# ------------------------------------------------------------------ update

ITEM = re.compile(r"^(\s*)-\s+")


def entry_blocks(lines):
    """Yield (start, end, indent_of_keys, id) for each list item under `artifacts:`."""
    in_arts = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^artifacts\s*:", line):
            in_arts = True
            i += 1
            continue
        if in_arts and re.match(r"^[^\s#-]", line):
            in_arts = False
        m = ITEM.match(line) if in_arts else None
        if not m:
            i += 1
            continue
        dash_indent = len(m.group(1))
        key_indent = len(m.group(0))
        j = i + 1
        while j < len(lines):
            nxt = lines[j]
            if nxt.strip() and not nxt.lstrip().startswith("#"):
                ind = len(nxt) - len(nxt.lstrip())
                if ind <= dash_indent:
                    break
            j += 1
        block = "".join(lines[i:j])
        idm = re.search(r"(?:^|\n)\s*-?\s*id\s*:\s*[\"']?([^\"'\s#]+)", block)
        yield i, j, key_indent, idm.group(1) if idm else None
        i = j


def cmd_update(args):
    text, data = read_registry(args.root, args.registry)
    if data.get("integrity") != "sha256":
        die(f"{args.registry} 未声明 integrity: sha256；先在登记表顶层加入 `integrity: sha256` 再更新 hash")
    by_id = {e.get("id"): e for e in entries(data)}
    targets = list(by_id) if args.all else args.ids
    if not targets:
        die("请指定要更新的 id，或使用 --all")
    for t in targets:
        if t not in by_id:
            die(f"登记表中没有 id `{t}`")
    lines = text.splitlines(keepends=True)
    updated, skipped = [], []
    for start, end, key_indent, aid in reversed(list(entry_blocks(lines))):
        if aid not in targets:
            continue
        e = by_id[aid]
        has_hash = bool(HEX64.match(str(e.get("sha256") or "")))
        if e.get("status") in FROZEN and has_hash and not args.allow_frozen:
            skipped.append(f"{aid}（状态 {e.get('status')}，已冻结）")
            continue
        path = e.get("path")
        if not path or not os.path.isfile(os.path.join(args.root, path)):
            die(f"{aid}: 路径不存在：{path}")
        new = f"{' ' * key_indent}sha256: {file_hash(args.root, path)}\n"
        block = lines[start:end]
        for k, line in enumerate(block):
            if re.match(r"^\s*sha256\s*:", line):
                block[k] = new
                break
        else:
            pos = next((k + 1 for k, line in enumerate(block) if re.match(r"^\s*-?\s*path\s*:", line)), len(block))
            block.insert(pos, new)
        lines[start:end] = block
        updated.append(aid)
    with open(os.path.join(args.root, args.registry), "w", encoding="utf-8") as f:
        f.write("".join(lines))
    for aid in reversed(updated):
        print(f"已更新 {aid}")
    for s in skipped:
        print(f"跳过 {s}；冻结文件应新建修订并用 supersedes 取代。确需修正时加 --allow-frozen")
    return 0 if not skipped or updated else 1


def cmd_hash(args):
    for rel in args.paths:
        print(f"{file_hash(args.root, rel)}  {rel}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"registry_check {TOOL_VERSION}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("check", "update", "hash"):
        p = sub.add_parser(name)
        p.add_argument("--root", default=".", help="项目根目录（默认当前目录）")
        if name != "hash":
            p.add_argument("--registry", default=DEFAULT_REGISTRY, help=f"登记表路径（默认 {DEFAULT_REGISTRY}）")
        if name == "check":
            p.add_argument("--base", help="比较基线，如 origin/main；用于检查冻结条目")
        if name == "update":
            p.add_argument("ids", nargs="*")
            p.add_argument("--all", action="store_true")
            p.add_argument("--allow-frozen", action="store_true")
        if name == "hash":
            p.add_argument("paths", nargs="+")
    args = ap.parse_args()
    args.root = os.path.abspath(args.root)
    return {"check": cmd_check, "update": cmd_update, "hash": cmd_hash}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
