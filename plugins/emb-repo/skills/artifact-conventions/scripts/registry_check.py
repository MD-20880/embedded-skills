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
    registry_check.py history  [--registry PATH] [--root DIR] [--markdown] ID
    registry_check.py baseline [--registry PATH] [--root DIR] [--markdown] [--ref REF]
    registry_check.py relations [--registry PATH] [--root DIR] [--markdown] [--of ID]

check   Every entry's path exists, its type is declared, ids are unique, and
        the file content matches the recorded sha256. With --base REF (for
        example origin/main in a PR), entries that were already superseded or
        archived at REF must still be listed and keep the same sha256: their
        content is frozen. An unreadable REF is an error, never a silent skip.
update  Recompute and write sha256 for the given ids (or --all). Refuses to
        change the hash of a superseded / archived entry that already has one,
        unless --allow-frozen (writing a first baseline hash is allowed). Only the
        `sha256:` line of each entry is touched; comments and order are kept.
hash    Print the normalized sha256 of files (for debugging).
history Trace one artifact through git: every commit that changed its registry
        entry (registered, content hash, revision, status, path, removed) or its
        file, oldest first. A commit that changed the file without touching the
        entry is flagged; before the entry existed, file commits are listed as
        pre-registration history. Read-only.
baseline
        Print the registry as of REF (default: the working tree) with each
        entry's revision, status and hash, and whether the file content at REF
        still matches the recorded hash. Meant to be archived with a release
        tag as the controlled baseline. Read-only.
relations
        Check the relation fields between entries (depends_on, refines,
        verifies, supersedes; each an id or a list of ids). FAIL: a malformed
        value, a target id that is not in the registry, a self reference, a
        supersedes cycle, an undeclared layer. WARN only (exit status stays 0):
        a depends_on or refines cycle, and a depends_on edge that the source
        layer's `may_depend_on` list in the top-level `layers` does not allow.
        An entry's layer is its own `layer`, else its type's `layer`; without
        `layers` no direction check is made. With --of ID, list what that entry
        points to and what points to it (change impact). Works with or without
        `integrity`. Read-only.

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

TOOL_VERSION = "1.2"
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
    """Run git; return stdout decoded as UTF-8, or None if git fails.

    Output is read as bytes and decoded explicitly: with text=True Python would
    use the locale encoding (e.g. cp936 / GBK on Chinese Windows) and fail on
    UTF-8 registries that contain Chinese comments.
    """
    try:
        out = subprocess.run(["git", *args], cwd=root, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    try:
        return out.decode("utf-8")
    except UnicodeDecodeError:
        die(f"git {' '.join(args)} 的输出不是合法的 UTF-8；登记表必须使用 UTF-8 编码")


def git_ok(root, *args):
    try:
        return subprocess.run(["git", *args], cwd=root, capture_output=True).returncode == 0
    except OSError:
        return False


def git_bytes(root, *args):
    try:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None


def require_repo(root):
    if git(root, "rev-parse", "--git-dir") is None:
        die(f"{root} 不是 git 仓库；history / baseline 需要读取 git 历史")


def lfs_tracked(root, rel):
    out = git(root, "check-attr", "filter", "--", rel)
    return bool(out) and out.strip().endswith(": lfs")


def data_hash(root, rel, data):
    m = LFS_POINTER.match(data) if len(data) < 1024 else None
    if m:
        return m.group(1).decode()
    if b"\0" not in data and not lfs_tracked(root, rel):
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def file_hash(root, rel):
    with open(os.path.join(root, rel), "rb") as f:
        return data_hash(root, rel, f.read())


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
        if git(args.root, "rev-parse", "--verify", "--quiet", f"{args.base}^{{commit}}") is None:
            die(f"无法读取基线 `{args.base}`：引用不存在、未 fetch，或当前目录不是 git 仓库。"
                "基线无效时不能跳过冻结检查；请先 fetch 目标分支（CI 中 checkout 需 fetch-depth: 0）")
        if not git_ok(args.root, "cat-file", "-e", f"{args.base}:{args.registry}"):
            old = None
            print(f"提示：基线 {args.base} 中没有 {args.registry}（首次启用），跳过冻结比较。")
        else:
            old = git(args.root, "show", f"{args.base}:{args.registry}")
            if old is None:
                die(f"无法读取基线中的登记表 {args.base}:{args.registry}；不能跳过冻结检查")
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
    current_ids = {e.get("id") for e in entries(data)}
    for aid in sorted(set(base_hash) - current_ids):
        problems.append(f"{aid}: 基线中已冻结的条目从登记表中被删除；冻结条目须保留以供追溯，"
                        "若文件已不再需要，保持其状态为 archived 即可")
    for p in problems:
        print(f"FAIL {p}")
    n = len(entries(data))
    print(f"{args.registry}: {n} 个条目，{len(problems)} 个问题 —— {'未通过' if problems else '通过'}")
    return 1 if problems else 0


# ------------------------------------------------------------------ update

ITEM = re.compile(r"^(\s*)-\s+")


def top_key(line, key, key_indent, first):
    """Match `key:` at the entry's own level: on the item's dash line, or at key_indent.

    Nested mappings (e.g. `source: {sha256: ...}` written as a block) sit deeper
    and must never be read or rewritten as the entry's own fields.
    """
    if first:
        return re.match(rf"^\s*-\s+{key}\s*:\s*(.*)$", line)
    return re.match(rf"^ {{{key_indent}}}{key}\s*:\s*(.*)$", line)


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
        aid = None
        for k in range(i, j):
            idm = top_key(lines[k], "id", key_indent, k == i)
            if idm:
                aid = idm.group(1).split(" #", 1)[0].strip().strip("\"'") or None
                break
        yield i, j, key_indent, aid
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
    updated, skipped, expected = [], [], {}
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
            if top_key(line, "sha256", key_indent, k == 0):
                if k == 0:  # sha256 written as the item's first key
                    block[k] = line[:line.index("-")] + "- " + new.lstrip()
                else:
                    block[k] = new
                break
        else:
            pos = next((k + 1 for k, line in enumerate(block) if top_key(line, "path", key_indent, k == 0)), None)
            if pos is None:  # no top-level path line: append after the entry's last line with content
                pos = max(k for k, line in enumerate(block) if line.strip()) + 1
            if not block[pos - 1].endswith("\n"):  # e.g. last line of a file without a trailing newline
                block[pos - 1] += "\n"
            block.insert(pos, new)
        lines[start:end] = block
        updated.append(aid)
        expected[aid] = new.split(":", 1)[1].strip()

    handled = set(updated) | {s.split("（", 1)[0] for s in skipped}
    unsupported = [t for t in targets if t not in handled]
    if unsupported:
        for t in unsupported:
            print(f"FAIL {t}: 无法定位该条目的块状写法（例如单行 flow-style `- {{id: …, path: …}}`），未更新。"
                  "请把该条目改为每个字段一行的写法后重试")
        print("登记表未修改。")
        return 1

    new_text = "".join(lines)
    result = {e.get("id"): e for e in entries(load_yaml(new_text, f"{args.registry}（更新后）"))}
    broken = [aid for aid, h in expected.items() if str((result.get(aid) or {}).get("sha256")) != h]
    if broken or set(result) != set(by_id):
        die(f"更新后的登记表校验失败（{', '.join(broken) or '条目集合发生变化'}），登记表未修改；请报告此问题")
    path = os.path.join(args.root, args.registry)
    with open(path, "rb") as f:  # keep the file's own line endings (CRLF on Windows checkouts, LF elsewhere)
        newline = "\r\n" if b"\r\n" in f.read() else "\n"
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(new_text.replace("\n", newline) if newline != "\n" else new_text)
    for aid in reversed(updated):
        print(f"已更新 {aid}")
    for s in skipped:
        print(f"跳过 {s}；冻结文件应新建修订并用 supersedes 取代。确需修正时加 --allow-frozen")
    return 0 if not skipped or updated else 1


# ------------------------------------------------------------------ history / baseline

FIELDS = ("path", "status", "revision", "sha256")
SEP = "\x1f"


def log(root, paths):
    """Commits touching any of `paths`, oldest first: (sha, date, author, subject)."""
    out = git(root, "log", "--reverse", "--date=short", f"--format=%H{SEP}%ad{SEP}%an{SEP}%s", "--", *paths)
    if out is None:
        die("git log 失败")
    return [tuple(line.split(SEP, 3)) for line in out.splitlines() if line.count(SEP) == 3]


def entry_at(root, rev, registry, aid):
    """The entry with `aid` in the registry at `rev`; None if absent; False if the registry is unreadable."""
    text = git(root, "show", f"{rev}:{registry}")
    if text is None:
        return None
    try:
        import yaml
        data = yaml.safe_load(text) or {}
    except Exception:  # an old, broken registry revision must not stop the trace
        return False
    if not isinstance(data, dict):
        return False
    arts = data.get("artifacts")
    for e in arts if isinstance(arts, list) else []:
        if isinstance(e, dict) and e.get("id") == aid:
            return {k: (None if e.get(k) is None else str(e.get(k))) for k in FIELDS}
    return None


def short(h):
    return (h or "")[:12] or "—"


def describe(prev, cur):
    if not prev and not cur:
        return []
    if not prev:
        rev = f"，版本 {cur['revision']}" if cur.get("revision") else ""
        return [f"登记：{cur['status']}{rev}，{cur['path']}"]
    if prev and not cur:
        return ["从登记表中移除"]
    notes = []
    if prev["path"] != cur["path"]:
        notes.append(f"路径 {prev['path']} → {cur['path']}")
    if prev["revision"] != cur["revision"]:
        notes.append(f"版本 {prev['revision'] or '—'} → {cur['revision'] or '—'}")
    if prev["status"] != cur["status"]:
        notes.append(f"状态 {prev['status']} → {cur['status']}")
    if prev["sha256"] != cur["sha256"]:
        notes.append("内容哈希 " + (f"{short(prev['sha256'])} → {short(cur['sha256'])}" if prev["sha256"] else
                                     f"写入基线 {short(cur['sha256'])}"))
    return notes


def hash_matches(root, rev, rel, recorded):
    blob = git_bytes(root, "show", f"{rev}:{rel}")
    return blob is not None and data_hash(root, rel, blob) == recorded


def cell(text):
    return str(text).replace("|", "\\|")


def cmd_history(args):
    require_repo(args.root)
    _, data = read_registry(args.root, args.registry)
    by_id = {e.get("id"): e for e in entries(data)}
    reg_commits = log(args.root, [args.registry])
    states, prev, seen = {}, None, False
    for sha, *_ in reg_commits:  # the entry as of every commit that touched the registry
        cur = entry_at(args.root, sha, args.registry, args.id)
        if cur is False:
            continue
        states[sha] = cur
    known = [s for s in states.values() if s]
    if args.id not in by_id and not known:
        die(f"当前登记表和历史中都没有 id `{args.id}`")
    paths = sorted({s["path"] for s in known if s.get("path")} |
                   ({str(by_id[args.id].get("path"))} if by_id.get(args.id, {}).get("path") else set()))
    file_commits = {c[0] for c in log(args.root, paths)} if paths else set()
    rows = []
    for sha, date, author, subject in log(args.root, [args.registry, *paths]):
        notes = []
        if sha in states:
            cur = states[sha]
            notes = describe(prev, cur)
            prev = cur
            seen = seen or bool(cur)
        if sha in file_commits:
            if not prev:
                notes = notes or ["文件改动（已移出登记表）" if seen else "文件改动（登记前）"]
            elif prev["sha256"] and not hash_matches(args.root, sha, prev["path"], prev["sha256"]):
                notes.append("文件内容与登记的哈希不一致（改了文件但没有更新登记）")
            elif not notes:
                notes = ["文件改动"]
        if notes:
            rows.append((date, sha[:9], author, "；".join(notes), subject))
    title = f"{args.id}  " + (f"{by_id[args.id].get('type')}  {by_id[args.id].get('path')}" if args.id in by_id
                              else "（当前登记表中已没有该条目）")
    if args.markdown:
        print(f"### {title}\n")
        print("| 日期 | 提交 | 作者 | 变化 | 提交说明 |")
        print("| --- | --- | --- | --- | --- |")
        for r in rows:
            print("| " + " | ".join(cell(x) for x in r) + " |")
    else:
        print(title)
        for date, sha, author, notes, subject in rows:
            print(f"{date}  {sha}  {author}  {notes}\n            {subject}")
    if not rows:
        print("没有找到相关提交（文件或登记表尚未提交？）")
    return 0


def cmd_baseline(args):
    if args.ref:
        require_repo(args.root)
        commit = git(args.root, "rev-parse", "--verify", "--quiet", f"{args.ref}^{{commit}}")
        if commit is None:
            die(f"无法读取 `{args.ref}`：引用不存在或未 fetch")
        commit = commit.strip()
        text = git(args.root, "show", f"{commit}:{args.registry}")
        if text is None:
            die(f"{args.ref} 中没有 {args.registry}")
        data = load_yaml(text, f"{args.ref}:{args.registry}")
        when = (git(args.root, "show", "-s", "--format=%ad", "--date=short", commit) or "").strip()
        source = f"{args.ref}（{commit[:12]}，{when}）"

        def content(rel):
            return git_bytes(args.root, "show", f"{commit}:{rel}")
    else:
        _, data = read_registry(args.root, args.registry)
        head = git(args.root, "rev-parse", "--short=12", "HEAD")
        dirty = bool((git(args.root, "status", "--porcelain") or "").strip()) if head else False
        source = "工作区" + (f"（HEAD {head.strip()}{'，有未提交改动' if dirty else ''}）" if head else "")

        def content(rel):
            path = os.path.join(args.root, rel)
            if not os.path.isfile(path):
                return None
            with open(path, "rb") as f:
                return f.read()
    integrity = data.get("integrity") == "sha256"
    rows, mismatched = [], 0
    for e in entries(data):
        rel, recorded = e.get("path"), str(e.get("sha256") or "")
        blob = content(rel) if rel else None
        if blob is None:
            state = "文件缺失"
        elif not integrity:
            state = "—"
        elif not HEX64.match(recorded):
            state = "无哈希"
        else:
            state = "一致" if data_hash(args.root, rel, blob) == recorded else "不一致"
        mismatched += state not in ("一致", "—")
        scope = e.get("scope")
        rows.append((e.get("id"), e.get("type"), e.get("status"), e.get("revision") or "—",
                     ", ".join(map(str, scope)) if isinstance(scope, list) else scope, rel, short(recorded), state))
    counts = {}
    for r in rows:
        counts[r[2]] = counts.get(r[2], 0) + 1
    summary = (f"{len(rows)} 个条目（" + "，".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: str(kv[0]))) +
               f"）；覆盖：{data.get('coverage', '未声明')}；完整性：{'sha256' if integrity else '未启用'}" +
               (f"；{mismatched} 个条目与登记不符" if mismatched else ""))
    if args.markdown:
        print(f"## 受控基线：{source}\n\n{summary}\n")
        print("| 编号 | 类型 | 状态 | 版本 | 范围 | 路径 | sha256 | 校验 |")
        print("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for r in rows:
            print("| " + " | ".join(cell(x) for x in r) + " |")
    else:
        print(f"受控基线：{source}\n{summary}")
        for r in rows:
            print("  ".join(str(x) for x in r))
    return 1 if mismatched else 0


# ------------------------------------------------------------------ relations

RELATIONS = ("depends_on", "refines", "verifies", "supersedes")
REL_NAME = {"depends_on": "依赖", "refines": "细化", "verifies": "验证", "supersedes": "取代"}


def find_cycle(edges):
    """Return one cycle in `edges` (id -> [id]) as a list of ids, or None. Iterative: no recursion limit."""
    state = {}
    for start in sorted(edges):
        if start in state:
            continue
        state[start] = 1
        path, todo = [start], [iter(edges.get(start, []))]
        while todo:
            m = next(todo[-1], None)
            if m is None:
                state[path.pop()] = 2
                todo.pop()
            elif state.get(m) == 1:
                return path[path.index(m):] + [m]
            elif m not in state:
                state[m] = 1
                path.append(m)
                todo.append(iter(edges.get(m, [])))
    return None


def cmd_relations(args):
    _, data = read_registry(args.root, args.registry)
    arts = [e for e in entries(data) if e.get("id")]
    ids = {e["id"] for e in arts}
    types = data.get("types") or {}
    layers = data.get("layers") or {}
    fails, warns = [], []
    if not isinstance(layers, dict):
        die("layers 必须是以层名为键的映射")

    def layer_of(e):
        own = e.get("layer")
        t = types.get(e.get("type"))
        return own if own else (t.get("layer") if isinstance(t, dict) else None)

    for name, spec in layers.items():
        allowed = (spec or {}).get("may_depend_on") if isinstance(spec, dict) else None
        for target in allowed or []:
            if target not in layers:
                fails.append(f"layers.{name}: may_depend_on 中的层 `{target}` 未在 layers 中声明")
    edges = {r: {} for r in RELATIONS}
    for e in arts:
        aid = e["id"]
        lay = layer_of(e)
        if layers and lay is not None and lay not in layers:
            fails.append(f"{aid}: 层 `{lay}` 未在 layers 中声明")
        for r in RELATIONS:
            v = e.get(r)
            if v is None:
                continue
            targets = [v] if isinstance(v, str) else v
            if not isinstance(targets, list) or not all(isinstance(t, str) and t for t in targets):
                fails.append(f"{aid}: {r} 应为编号或编号列表")
                continue
            for t in targets:
                if t == aid:
                    fails.append(f"{aid}: {r} 指向自己")
                elif t not in ids:
                    fails.append(f"{aid}: {r} 指向的编号 `{t}` 不在登记表中")
                else:
                    edges[r].setdefault(aid, []).append(t)
    for r, level in (("supersedes", fails), ("depends_on", warns), ("refines", warns)):
        cyc = find_cycle(edges[r])
        if cyc:
            level.append(f"{r} 成环：{' → '.join(cyc)}")
    if layers:
        by_id = {e["id"]: e for e in arts}
        for src, targets in sorted(edges["depends_on"].items()):
            ls = layer_of(by_id[src])
            spec = layers.get(ls) if ls else None
            allowed = spec.get("may_depend_on") if isinstance(spec, dict) else None
            if allowed is None:
                continue
            for t in targets:
                lt = layer_of(by_id[t])
                if lt is not None and lt not in allowed:
                    warns.append(f"{src}（{ls}）depends_on {t}（{lt}）：{ls} 层只应依赖 "
                                 f"{', '.join(allowed) or '（无）'}；跨模块的合计与取舍应放在联合文档")
    if args.of:
        if args.of not in ids:
            die(f"登记表中没有 id `{args.of}`")
        out = [(REL_NAME[r], t) for r in RELATIONS for t in edges[r].get(args.of, [])]
        inc = [(REL_NAME[r], s) for r in RELATIONS for s, ts in sorted(edges[r].items()) if args.of in ts]
        if args.markdown:
            print(f"### {args.of} 的关系\n")
            print("| 方向 | 关系 | 编号 |")
            print("| --- | --- | --- |")
            for rel, t in out:
                print(f"| 指向 | {rel} | {cell(t)} |")
            for rel, s_ in inc:
                print(f"| 被指向 | {rel} | {cell(s_)} |")
        else:
            print(f"{args.of} 指向：" + ("；".join(f"{rel} {t}" for rel, t in out) or "无"))
            print(f"指向 {args.of}：" + ("；".join(f"{s_} {rel}" for rel, s_ in inc) or "无"))
            print("改动它时，检查“指向它”的条目是否需要同步。")
    for p in fails:
        print(f"FAIL {p}")
    for w in warns:
        print(f"WARN {w}")
    n_edges = sum(len(ts) for r in RELATIONS for ts in edges[r].values())
    print(f"{args.registry}: {len(arts)} 个条目，{n_edges} 条关系，{len(fails)} 个问题，{len(warns)} 个提醒 —— "
          f"{'未通过' if fails else '通过'}")
    return 1 if fails else 0


def cmd_hash(args):
    for rel in args.paths:
        print(f"{file_hash(args.root, rel)}  {rel}")
    return 0


def main():
    for stream in (sys.stdout, sys.stderr):
        try:  # pipes (CI logs, Claude Code's Bash tool) get UTF-8 even under a cp936 / GBK locale
            stream.reconfigure(errors="replace", **({} if stream.isatty() else {"encoding": "utf-8"}))
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"registry_check {TOOL_VERSION}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("check", "update", "hash", "history", "baseline", "relations"):
        p = sub.add_parser(name)
        p.add_argument("--root", default=".", help="项目根目录（默认当前目录）")
        if name in ("history", "baseline", "relations"):
            p.add_argument("--markdown", action="store_true", help="输出 Markdown 表格")
        if name == "history":
            p.add_argument("id")
        if name == "baseline":
            p.add_argument("--ref", help="提交、分支或标签，如 v0.2.0；默认读取工作区")
        if name == "relations":
            p.add_argument("--of", help="列出该编号指向的条目和指向它的条目")
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
    return {"check": cmd_check, "update": cmd_update, "hash": cmd_hash,
            "history": cmd_history, "baseline": cmd_baseline, "relations": cmd_relations}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
