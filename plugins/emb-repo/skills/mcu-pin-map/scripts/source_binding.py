#!/usr/bin/env python3
"""Capture source bytes, publish a pin map, or check its source binding.

Python 3.8+, standard library only. ``publish`` writes a local Markdown file;
it does not publish externally. Metadata is JSON inside YAML frontmatter
delimiters (a YAML-compatible subset), not arbitrary hand-written YAML.
Capture selects hash modes using artifact-conventions/registry_check.py rules,
then pins each input's mode. Check/publish never reinterpret Git attributes.
Unresolved Git LFS pointers are rejected: they are not source evidence.

Exit status: 0 success / CURRENT, 1 STALE, 2 UNVERIFIABLE / usage error.
Matching hashes do not validate extracted facts, output integrity or hardware.
"""

import argparse
import hashlib
import json
import os
import re
import secrets
import stat
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath, PureWindowsPath

SCHEMA = "mcu-pin-map/v1"
SNAPSHOT_SCHEMA = "mcu-pin-map-snapshot/v1"
HASH_POLICY = "sha256-text-lf-binary-raw-v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
NOTES_START = "<!-- manual-notes:start -->"
NOTES_END = "<!-- manual-notes:end -->"


class BindingError(ValueError):
    def __init__(self, message, code=2):
        super().__init__(message)
        self.code = code


def utf8_output():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace", **({} if stream.isatty() else {"encoding": "utf-8"}))
        except (AttributeError, ValueError):
            pass


def keys(value, expected, where):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise BindingError("{}: expected fields {}".format(where, ", ".join(expected)))


def nonblank(value, where):
    if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 for c in value):
        raise BindingError("{}: expected nonblank text without control characters".format(where))


def relative_name(value):
    nonblank(value, "path")
    if ("\\" in value or ":" in value or value.startswith("/")
            or PureWindowsPath(value).drive
            or any(part in ("", ".", "..") for part in value.split("/"))):
        raise BindingError("unsafe repository-relative path: {}".format(value))
    return PurePosixPath(value)


def inside(root, name):
    path = root.joinpath(*relative_name(name).parts).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        raise BindingError("path escapes root through a symlink: {}".format(name))
    return path


def read_regular(path):
    """Reject devices/FIFOs and changes observed while reading one file."""
    before = path.stat()
    if not stat.S_ISREG(before.st_mode):
        raise BindingError("not a regular file: {}".format(path))
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        data = stream.read()
        after = os.fstat(stream.fileno())
    current = path.stat()
    signatures = {(s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
                  for s in (before, opened, after, current)}
    if len(signatures) != 1:
        raise BindingError("file changed while reading: {}".format(path), 1)
    return data


def digest(data):
    return hashlib.sha256(data).hexdigest()


def has_git_metadata(directory):
    marker = directory / ".git"
    if marker.is_dir() and not marker.is_symlink():
        try:
            # An empty .git directory is not a working tree (some sandboxes
            # place such inert directories above otherwise ordinary files).
            return next(marker.iterdir(), None) is not None
        except OSError:
            return True
    return os.path.lexists(str(marker))


def lfs_tracked(root, name):
    """Resolve attributes during capture; never guess in a Git worktree."""
    try:
        result = subprocess.run(
            ["git", "check-attr", "-z", "filter", "--", name], cwd=str(root),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (OSError, subprocess.CalledProcessError):
        parent = root.joinpath(*relative_name(name).parts).parent
        ancestors = (parent,) + tuple(parent.parents)
        if any(has_git_metadata(p) or os.path.lexists(str(p / ".gitattributes"))
               for p in ancestors):
            raise BindingError("Git attributes unavailable; cannot select hash mode for " + name)
        return False
    fields = result.stdout.split(b"\0")
    if len(fields) != 4 or fields[1] != b"filter" or fields[-1] != b"":
        raise BindingError("unreadable Git attributes for " + name)
    return fields[2] == b"lfs"


def selected_mode(data, is_lfs):
    return "raw" if is_lfs or b"\0" in data else "text-lf"


def source_digest(data, mode):
    if mode not in ("text-lf", "raw"):
        raise BindingError("unsupported input hash mode")
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if normalized.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
        raise BindingError("unresolved Git LFS pointer; obtain the actual source content")
    return digest(data if mode == "raw" else normalized)


def load_json(text, where):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise BindingError("{}: duplicate JSON key {}".format(where, key))
            result[key] = value
        return result

    def invalid_constant(value):
        raise BindingError("{}: invalid JSON constant {}".format(where, value))

    try:
        return json.loads(text, object_pairs_hook=unique, parse_constant=invalid_constant)
    except json.JSONDecodeError as exc:
        raise BindingError("{}: expected JSON metadata ({})".format(where, exc))


def validate_metadata(metadata):
    keys(metadata, ("schema", "target", "source_binding"), "metadata")
    if metadata["schema"] != SCHEMA:
        raise BindingError("unsupported map schema")
    keys(metadata["target"], ("board", "revision", "mcu_ref"), "target")
    for key, value in metadata["target"].items():
        nonblank(value, "target." + key)
    binding = metadata["source_binding"]
    keys(binding, ("hash_policy", "inputs"), "source_binding")
    if binding["hash_policy"] != HASH_POLICY:
        raise BindingError("unsupported hash policy")
    if not isinstance(binding["inputs"], list) or not binding["inputs"]:
        raise BindingError("source_binding.inputs must be a nonempty list")
    seen = set()
    for entry in binding["inputs"]:
        keys(entry, ("path", "sha256", "hash_mode"), "input")
        relative_name(entry["path"])
        if entry["hash_mode"] not in ("text-lf", "raw"):
            raise BindingError("invalid hash_mode for " + entry["path"])
        if entry["path"] in seen:
            raise BindingError("duplicate input path: " + entry["path"])
        seen.add(entry["path"])
        if not isinstance(entry["sha256"], str) or not HEX64.fullmatch(entry["sha256"]):
            raise BindingError("invalid sha256 for " + entry["path"])
    return metadata


def split_document(data):
    text = data.decode("utf-8")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise BindingError("missing frontmatter")
    closing = next((i for i in range(1, len(lines)) if lines[i].rstrip("\r\n") == "---"), None)
    if closing is None:
        raise BindingError("unterminated frontmatter")
    metadata = validate_metadata(load_json("".join(lines[1:closing]), "frontmatter"))
    body = "".join(lines[closing + 1:])
    notes_span(body)
    return metadata, body


def notes_span(body):
    if body.count(NOTES_START) != 1 or body.count(NOTES_END) != 1:
        raise BindingError("body must contain exactly one manual-notes marker pair")
    start, end = body.index(NOTES_START) + len(NOTES_START), body.index(NOTES_END)
    if end < start:
        raise BindingError("manual-notes markers are reversed")
    return start, end


def same_file(left, right):
    return left == right or (left.exists() and right.exists() and os.path.samefile(str(left), str(right)))


def inspect_sources(root, metadata, forbidden=()):
    results = []
    for entry in metadata["source_binding"]["inputs"]:
        name, expected = entry["path"], entry["sha256"]
        actual, reason = None, ""
        try:
            path = inside(root, name)
            if any(same_file(path, item) for item in forbidden):
                raise BindingError("source aliases the output or temporary input")
            actual = source_digest(read_regular(path), entry["hash_mode"])
            state = "CURRENT" if actual == expected else "STALE"
            if state == "STALE":
                reason = "source content changed"
        except (OSError, ValueError, RuntimeError) as exc:
            state, reason = "UNVERIFIABLE", str(exc)
        results.append({"path": name, "expected": expected, "actual": actual,
                        "status": state, "reason": reason})
    code = 2 if any(r["status"] == "UNVERIFIABLE" for r in results) else int(any(r["status"] == "STALE" for r in results))
    return code, results


def print_sources(results):
    for result in results:
        print("{status} {path} expected={expected} actual={actual}{reason}".format(
            **dict(result, actual=result["actual"] or "unavailable",
                   reason=(" reason=" + result["reason"]) if result["reason"] else "")))


def ensure_sources(root, metadata, forbidden=()):
    code, results = inspect_sources(root, metadata, forbidden)
    if code:
        print_sources(results)
        raise BindingError("sources no longer match this snapshot; capture and regenerate again", code)


def capture(args, root):
    target = {"board": args.board, "revision": args.revision, "mcu_ref": args.mcu_ref}
    inputs, copies = [], []
    for name in args.source:
        path = inside(root, name)
        data = read_regular(path)
        is_lfs = lfs_tracked(root, name)
        mode = selected_mode(data, is_lfs)
        inputs.append({"path": name, "sha256": source_digest(data, mode), "hash_mode": mode})
        copies.append((name, data, is_lfs))
    metadata = validate_metadata({"schema": SCHEMA, "target": target,
                                  "source_binding": {"hash_policy": HASH_POLICY, "inputs": inputs}})
    destination = Path(args.snapshot).resolve()
    if destination.exists():
        raise BindingError("snapshot destination already exists: {}".format(destination))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".pin-map-snapshot-", dir=str(destination.parent)) as staging:
        staging_path = Path(staging)
        files = []
        for name, data, is_lfs in copies:
            copy_path = staging_path / "sources" / name
            copy_path.parent.mkdir(parents=True, exist_ok=True)
            copy_path.write_bytes(data)
            files.append({"path": name, "raw_sha256": digest(data), "lfs": is_lfs})
        manifest = {"schema": SNAPSHOT_SCHEMA, "metadata": metadata, "files": files}
        (staging_path / "manifest.json").write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        ensure_sources(root, metadata)
        if destination.exists():
            raise BindingError("snapshot destination appeared while capturing")
        os.rename(staging, str(destination))
    print("CAPTURED {}".format(destination))
    for entry in inputs:
        print("READ {} sha256={}".format(destination / "sources" / entry["path"], entry["sha256"]))
    return 0


def read_snapshot(snapshot):
    manifest = load_json(read_regular(snapshot / "manifest.json").decode("utf-8"), "snapshot manifest")
    keys(manifest, ("schema", "metadata", "files"), "snapshot")
    if manifest["schema"] != SNAPSHOT_SCHEMA:
        raise BindingError("unsupported snapshot schema")
    metadata = validate_metadata(manifest["metadata"])
    files = manifest["files"]
    if not isinstance(files, list) or len(files) != len(metadata["source_binding"]["inputs"]):
        raise BindingError("snapshot input count mismatch")
    for entry, captured in zip(metadata["source_binding"]["inputs"], files):
        keys(captured, ("path", "raw_sha256", "lfs"), "snapshot file")
        if captured["path"] != entry["path"] or type(captured["lfs"]) is not bool:
            raise BindingError("snapshot input identity mismatch")
        data = read_regular(inside(snapshot, "sources/" + entry["path"]))
        if entry["hash_mode"] != selected_mode(data, captured["lfs"]):
            raise BindingError("snapshot hash mode selection changed: " + entry["path"])
        if digest(data) != captured["raw_sha256"] or source_digest(data, entry["hash_mode"]) != entry["sha256"]:
            raise BindingError("snapshot bytes changed: " + entry["path"])
    return metadata


def open_staging(parent, mode=0o666):
    """Exclusive staging file; never widen replacement permissions while writing."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    for _ in range(100):
        path = parent / (".pin-map-" + secrets.token_hex(8) + ".tmp")
        try:
            descriptor = os.open(str(path), flags, mode)
        except FileExistsError:
            continue
        return path, os.fdopen(descriptor, "wb")
    raise BindingError("could not create a unique staging file")


def publish(args, root):
    snapshot = Path(args.snapshot).resolve()
    metadata = read_snapshot(snapshot)
    output = inside(root, args.output)
    body_path = Path(args.body).resolve()
    if same_file(output, body_path) or snapshot == output or snapshot in output.parents:
        raise BindingError("output aliases body or snapshot")
    if root.joinpath(*relative_name(args.output).parts).is_symlink():
        raise BindingError("output must not be a symlink")
    ensure_sources(root, metadata, (output, body_path))
    body = read_regular(body_path).decode("utf-8")
    if not body.strip() or body.lstrip().startswith("---\n") or body.lstrip().startswith("---\r\n"):
        raise BindingError("body must be nonempty Markdown without frontmatter")
    start, end = notes_span(body)
    original = None
    original_mode = None
    if output.exists():
        if not args.replace:
            raise BindingError("output exists; use --replace only for an intentional update")
        original = read_regular(output)
        original_mode = stat.S_IMODE(output.stat().st_mode)
        old_metadata, old_body = split_document(original)
        if old_metadata["target"] != metadata["target"]:
            raise BindingError("target differs; use a separate map for each board/revision/MCU")
        old_start, old_end = notes_span(old_body)
        body = body[:start] + old_body[old_start:old_end] + body[end:]
    content = ("---\n" + json.dumps(metadata, ensure_ascii=False, indent=2) + "\n---\n\n" + body.lstrip("\r\n"))
    if not content.endswith("\n"):
        content += "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        temp_path, stream = open_staging(output.parent, original_mode if original_mode is not None else 0o666)
        with stream:
            stream.write(content.encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        if original_mode is not None:
            os.chmod(str(temp_path), original_mode)
        ensure_sources(root, metadata, (output, body_path))
        read_snapshot(snapshot)
        if original is not None:
            if read_regular(output) != original or stat.S_IMODE(output.stat().st_mode) != original_mode:
                raise BindingError("output changed while publishing; preserve the newer file")
            os.replace(str(temp_path), str(output))
        else:
            # link is atomic and fails if another process created the destination.
            os.link(str(temp_path), str(output))
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
    print("PUBLISHED {} (local file; source binding checked at write time)".format(args.output))
    return 0


def check(args, root):
    path = inside(root, args.map)
    metadata, _ = split_document(read_regular(path))
    code, results = inspect_sources(root, metadata, (path,))
    print("{} {}".format(("CURRENT", "STALE", "UNVERIFIABLE")[code], args.map))
    print_sources(results)
    return code


def main(argv=None):
    utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    capture_parser = commands.add_parser("capture", help="capture the exact files the agent will read")
    for option in ("board", "revision", "mcu-ref", "snapshot"):
        capture_parser.add_argument("--" + option, required=True)
    capture_parser.add_argument("--source", action="append", required=True)
    publish_parser = commands.add_parser("publish", help="atomically write a local map from a captured snapshot")
    for option in ("snapshot", "body", "output"):
        publish_parser.add_argument("--" + option, required=True)
    publish_parser.add_argument("--replace", action="store_true")
    check_parser = commands.add_parser("check", help="read-only source freshness check")
    check_parser.add_argument("--map", required=True)
    for command in (capture_parser, publish_parser, check_parser):
        command.add_argument("--root", default=".", help="project repository root (default: current directory)")
    args = parser.parse_args(argv)
    try:
        root = Path(args.root).resolve(strict=True)
        if not root.is_dir():
            raise BindingError("root is not a directory")
        return {"capture": capture, "publish": publish, "check": check}[args.command](args, root)
    except (OSError, ValueError, RuntimeError) as exc:
        code = exc.code if isinstance(exc, BindingError) else 2
        print("{} {}".format("STALE" if code == 1 else "UNVERIFIABLE", exc), file=sys.stderr)
        return code


if __name__ == "__main__":
    sys.exit(main())
