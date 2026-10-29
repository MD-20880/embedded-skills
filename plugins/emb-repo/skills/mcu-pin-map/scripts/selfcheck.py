#!/usr/bin/env python3
"""Deterministic source-binding regression checks; no network or model calls."""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().with_name("source_binding.py")
spec = importlib.util.spec_from_file_location("source_binding", SCRIPT)
binding = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binding)
BODY = "# MCU 引脚资料\n\nU1.1 → U2.4；未确认有效电平。\n\n<!-- manual-notes:start -->\n原有人工备注。\n<!-- manual-notes:end -->\n"


class SourceBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mcu-pin-map-selfcheck-")
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        self.root = self.workspace / "项目 空间"
        self.root.mkdir()
        self.name = "hardware/板子.net"
        self.source = self.root / self.name
        self.source.parent.mkdir()
        self.source.write_bytes("网络 U1.1 U2.4\n".encode("utf-8"))
        self.snapshot = self.workspace / "snapshot"
        self.body = self.workspace / "body.md"
        self.body.write_bytes(BODY.encode("utf-8"))
        self.output_name = "docs/hardware/rev-a/U1-pin-map.md"
        self.output = self.root / self.output_name

    def run_cli(self, command, *args, expected=0):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = binding.main([command, "--root", str(self.root)] + [str(a) for a in args])
        log = stdout.getvalue() + stderr.getvalue()
        self.assertEqual(code, expected, log)
        return log

    def capture(self, snapshot=None, revision="rev-a", sources=None, expected=0):
        args = ["--board", "test-board", "--revision", revision, "--mcu-ref", "U1",
                "--snapshot", snapshot or self.snapshot]
        for name in sources or [self.name]:
            args += ["--source", name]
        return self.run_cli("capture", *args, expected=expected)

    def publish(self, snapshot=None, replace=False, expected=0, output=None, body=None):
        args = ["--snapshot", snapshot or self.snapshot, "--body", body or self.body,
                "--output", output or self.output_name]
        if replace:
            args += ["--replace"]
        return self.run_cli("publish", *args, expected=expected)

    def create_map(self):
        self.capture()
        self.publish()
        return self.output.read_bytes()

    def rewrite_metadata(self, metadata, body=BODY):
        self.output.write_bytes(("---\n" + json.dumps(metadata, ensure_ascii=False) + "\n---\n" + body).encode("utf-8"))

    def test_roundtrip_readonly_check_and_utf8(self):
        self.create_map()
        before = {str(p): (p.read_bytes(), p.stat().st_mtime_ns)
                  for p in self.root.rglob("*") if p.is_file()}
        log = self.run_cli("check", "--map", self.output_name)
        after = {str(p): (p.read_bytes(), p.stat().st_mtime_ns)
                 for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertIn("CURRENT", log)
        self.assertIn("expected=", log)
        self.assertIn("actual=", log)
        metadata, body = binding.split_document(self.output.read_bytes())
        self.assertEqual(metadata["target"]["mcu_ref"], "U1")
        self.assertIn("人工备注", body)
        self.assertNotIn("current", metadata)

    def test_stale_and_missing(self):
        self.create_map()
        self.source.write_bytes(b"changed\n")
        self.assertIn("STALE", self.run_cli("check", "--map", self.output_name, expected=1))
        self.source.unlink()
        self.assertIn("UNVERIFIABLE", self.run_cli("check", "--map", self.output_name, expected=2))
        self.source.mkdir()
        self.assertIn("regular file", self.run_cli("check", "--map", self.output_name, expected=2))

    def test_text_lf_crlf_cr_are_equal(self):
        self.source.write_bytes(b"a\r\nb\r\n")
        self.create_map()
        for data in (b"a\nb\n", b"a\rb\r"):
            self.source.write_bytes(data)
            self.run_cli("check", "--map", self.output_name)

    def test_binary_is_raw(self):
        self.source.write_bytes(b"a\0\r\nb\n")
        self.create_map()
        metadata, _ = binding.split_document(self.output.read_bytes())
        self.assertEqual(metadata["source_binding"]["inputs"][0]["sha256"], hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.source.write_bytes(b"a\0\nb\n")
        self.run_cli("check", "--map", self.output_name, expected=1)

    def test_lfs_hydrated_bytes_and_pointer(self):
        subprocess.run(["git", "init", str(self.root)], check=True, capture_output=True)
        (self.root / ".gitattributes").write_bytes(b"*.net filter=lfs\n")
        self.source.write_bytes(b"a\r\nb\r\n")
        self.create_map()
        metadata, _ = binding.split_document(self.output.read_bytes())
        sha = metadata["source_binding"]["inputs"][0]["sha256"]
        self.assertEqual(sha, hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.source.write_bytes(b"a\nb\n")
        self.run_cli("check", "--map", self.output_name, expected=1)
        pointer = "version https://git-lfs.github.com/spec/v1\noid sha256:{}\nsize 6\n".format(sha)
        self.source.write_bytes(pointer.encode("ascii"))
        self.assertIn("LFS pointer", self.run_cli("check", "--map", self.output_name, expected=2))
        destination = self.workspace / "unresolved"
        self.capture(snapshot=destination, expected=2)
        self.assertFalse(destination.exists())

    def test_recorded_lfs_mode_survives_attribute_changes_and_missing_git(self):
        subprocess.run(["git", "init", str(self.root)], check=True, capture_output=True)
        attributes = self.root / ".gitattributes"
        attributes.write_bytes(b"*.net filter=lfs\n")
        self.source.write_bytes(b"a\nb\n")
        self.create_map()
        metadata, _ = binding.split_document(self.output.read_bytes())
        self.assertEqual(metadata["source_binding"]["inputs"][0]["hash_mode"], "raw")
        attributes.write_bytes(b"*.net -filter\n")
        with mock.patch.object(binding, "lfs_tracked", side_effect=AssertionError("must not resolve attributes again")):
            self.run_cli("check", "--map", self.output_name)
            self.publish(replace=True)
            attributes.unlink()
            self.source.write_bytes(b"a\r\nb\r\n")
            self.run_cli("check", "--map", self.output_name, expected=1)
            self.publish(replace=True, expected=1)
        env = dict(os.environ, PATH=str(self.workspace / "no-git"))
        result = subprocess.run([sys.executable, str(SCRIPT), "check", "--root", str(self.root), "--map", self.output_name],
                                capture_output=True, env=env, timeout=10)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(b"STALE", result.stdout)

    def test_recorded_text_mode_is_not_changed_by_new_lfs_attributes(self):
        subprocess.run(["git", "init", str(self.root)], check=True, capture_output=True)
        self.source.write_bytes(b"a\nb\n")
        self.create_map()
        (self.root / ".gitattributes").write_bytes(b"*.net filter=lfs\n")
        self.source.write_bytes(b"a\r\nb\r\n")
        self.run_cli("check", "--map", self.output_name)
        self.publish(replace=True)

    def test_capture_git_failure_fails_closed_in_worktree(self):
        subprocess.run(["git", "init", str(self.root)], check=True, capture_output=True)
        with mock.patch.object(binding.subprocess, "run", side_effect=FileNotFoundError("git unavailable")):
            self.assertIn("Git attributes unavailable", self.capture(expected=2))
        self.assertFalse(self.snapshot.exists())

    def test_capture_git_failure_detects_ancestor_worktree(self):
        subprocess.run(["git", "init", str(self.workspace)], check=True, capture_output=True)
        with mock.patch.object(binding.subprocess, "run", side_effect=FileNotFoundError("git unavailable")):
            self.capture(expected=2)
        self.assertFalse(self.snapshot.exists())

    def test_empty_git_directory_is_not_a_worktree(self):
        (self.workspace / ".git").mkdir()
        with mock.patch.object(binding.subprocess, "run", side_effect=FileNotFoundError("git unavailable")):
            self.capture()
            self.publish()
            self.run_cli("check", "--map", self.output_name)

    def test_capture_git_failure_fails_closed_with_attributes_without_git(self):
        (self.root / "hardware" / ".gitattributes").write_bytes(b"*.net filter=lfs\n")
        with mock.patch.object(binding.subprocess, "run", side_effect=FileNotFoundError("git unavailable")):
            self.capture(expected=2)
        self.assertFalse(self.snapshot.exists())

    def test_capture_non_git_files_without_attributes_can_use_heuristic(self):
        with mock.patch.object(binding.subprocess, "run", side_effect=FileNotFoundError("git unavailable")):
            self.capture()
            self.publish()
            self.run_cli("check", "--map", self.output_name)

    def test_multiple_sources_report_each(self):
        second_name = "hardware/手册.pdf"
        second = self.root / second_name
        second.write_bytes(b"pdf\0data")
        self.capture(sources=[self.name, second_name])
        self.publish()
        self.source.write_bytes(b"changed")
        second.unlink()
        log = self.run_cli("check", "--map", self.output_name, expected=2)
        self.assertIn("STALE " + self.name, log)
        self.assertIn("UNVERIFIABLE " + second_name, log)

    def test_malformed_metadata_fails_closed(self):
        self.create_map()
        original, _ = binding.split_document(self.output.read_bytes())
        changes = [
            lambda d: d.update(schema="mcu-pin-map/v2"),
            lambda d: d.update(current=True),
            lambda d: d["target"].update(revision=""),
            lambda d: d["source_binding"].update(hash_policy="unknown"),
            lambda d: d["source_binding"].update(inputs=[]),
            lambda d: d["source_binding"].update(inputs={}),
            lambda d: d["source_binding"]["inputs"][0].update(sha256="fake"),
            lambda d: d["source_binding"]["inputs"][0].update(hash_mode="auto"),
            lambda d: d["source_binding"]["inputs"][0].pop("hash_mode"),
            lambda d: d["source_binding"]["inputs"].append(dict(d["source_binding"]["inputs"][0])),
            lambda d: d["source_binding"]["inputs"][0].update(path="../outside"),
        ]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                metadata = json.loads(json.dumps(original))
                change(metadata)
                self.rewrite_metadata(metadata)
                self.run_cli("check", "--map", self.output_name, expected=2)

    def test_duplicate_json_keys_and_arbitrary_yaml_rejected(self):
        raw = self.create_map()
        duplicated = raw.replace(b'"schema": "mcu-pin-map/v1"', b'"schema": "mcu-pin-map/v1", "schema": "mcu-pin-map/v1"')
        self.output.write_bytes(duplicated)
        self.assertIn("duplicate JSON key", self.run_cli("check", "--map", self.output_name, expected=2))
        self.output.write_bytes(b"---\nschema: mcu-pin-map/v1\n---\n")
        self.run_cli("check", "--map", self.output_name, expected=2)
        self.output.write_bytes(b"---\n{\"schema\": NaN}\n---\n")
        self.run_cli("check", "--map", self.output_name, expected=2)

    def test_unsafe_source_paths(self):
        names = ["../secret", "/etc/passwd", "C:/file", "C:\\file", "https://example.com/a",
                 "./hardware/a.net", "hardware//a.net", "hardware/../a.net", "hardware/a.net/", "a\nb"]
        for name in names:
            with self.subTest(name=name):
                self.capture(sources=[name], expected=2)
                self.assertFalse(self.snapshot.exists())

    def test_duplicate_sources(self):
        self.capture(sources=[self.name, self.name], expected=2)
        self.assertFalse(self.snapshot.exists())

    def test_symlink_escape_and_output_symlink(self):
        outside = self.workspace / "outside.net"
        outside.write_bytes(b"outside")
        link = self.root / "link.net"
        try:
            link.symlink_to(outside)
        except OSError:
            self.skipTest("symlinks unavailable for this user")
        self.capture(sources=["link.net"], expected=2)
        self.capture()
        self.publish(output="link.net", expected=2)
        self.assertEqual(outside.read_bytes(), b"outside")
        internal = self.root / "internal.net"
        internal.symlink_to(self.source)
        self.publish(output="internal.net", expected=2)
        self.assertTrue(internal.is_symlink())

    def test_output_cannot_alias_source_body_or_snapshot(self):
        self.capture()
        source_bytes = self.source.read_bytes()
        self.publish(output=self.name, expected=2)
        self.assertEqual(self.source.read_bytes(), source_bytes)
        alias = self.root / "alias.md"
        os.link(str(self.source), str(alias))
        self.publish(output="alias.md", expected=2)
        self.body = self.root / "body.md"
        self.body.write_bytes(BODY.encode("utf-8"))
        self.publish(output="body.md", expected=2)
        in_repo = self.root / "scratch-snapshot"
        self.capture(snapshot=in_repo)
        self.publish(snapshot=in_repo, output="scratch-snapshot/map.md", expected=2)

    def test_changes_after_capture_preserve_previous_output(self):
        old = self.create_map()
        self.source.write_bytes(b"changed input\n")
        self.publish(replace=True, expected=1)
        self.assertEqual(self.output.read_bytes(), old)
        self.source.unlink()
        self.publish(replace=True, expected=2)
        self.assertEqual(self.output.read_bytes(), old)

    def test_snapshot_tampering_preserves_previous_output(self):
        old = self.create_map()
        (self.snapshot / "sources" / self.name).write_bytes(b"tampered")
        self.publish(replace=True, expected=2)
        self.assertEqual(self.output.read_bytes(), old)

    def test_snapshot_manifest_mismatch(self):
        self.capture()
        path = self.snapshot / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["files"][0]["path"] = "wrong.net"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        self.publish(expected=2)
        self.assertFalse(self.output.exists())

    def test_snapshot_mode_must_match_captured_selection(self):
        self.capture()
        path = self.snapshot / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["metadata"]["source_binding"]["inputs"][0]["hash_mode"] = "raw"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        self.assertIn("hash mode selection changed", self.publish(expected=2))
        self.assertFalse(self.output.exists())

    def test_replace_is_explicit_and_notes_are_preserved(self):
        old = self.create_map()
        self.publish(expected=2)
        self.assertEqual(self.output.read_bytes(), old)
        self.output.write_bytes(old.replace("原有人工备注。\n".encode("utf-8"), "手工备注\r\n第二行\r\n".encode("utf-8")))
        self.body.write_bytes(BODY.replace("原有人工备注。", "应被忽略的新备注。").replace("U1.1", "U1.2").encode("utf-8"))
        self.publish(replace=True)
        result = self.output.read_bytes()
        self.assertIn("手工备注\r\n第二行\r\n".encode("utf-8"), result)
        self.assertNotIn("应被忽略".encode("utf-8"), result)
        self.assertIn(b"U1.2", result)

    def test_target_mismatch_preserves_previous_output(self):
        old = self.create_map()
        other = self.workspace / "other-snapshot"
        self.capture(snapshot=other, revision="rev-b")
        self.publish(snapshot=other, replace=True, expected=2)
        self.assertEqual(self.output.read_bytes(), old)

    @unittest.skipIf(os.name == "nt", "POSIX permission bits are not supported on Windows")
    def test_replace_preserves_permissions(self):
        self.create_map()
        self.output.chmod(0o640)
        self.publish(replace=True)
        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o640)

    @unittest.skipIf(os.name == "nt", "POSIX permission bits are not supported on Windows")
    def test_replacement_staging_never_exposes_private_notes(self):
        self.create_map()
        self.output.chmod(0o600)
        code = """
import os, runpy, stat, sys
from pathlib import Path
os.umask(0o022)
namespace = runpy.run_path(sys.argv[1])
original_chmod = os.chmod
seen = []
def inspect_before_chmod(path, mode):
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600, 'staging exposed private content'
    assert b'manual-notes:start' in Path(path).read_bytes(), 'inspect populated staging'
    seen.append(path)
    original_chmod(path, mode)
os.chmod = inspect_before_chmod
result = namespace['main'](sys.argv[2:])
assert seen, 'staging was not inspected'
sys.exit(result)
"""
        result = subprocess.run([sys.executable, "-c", code, str(SCRIPT), "publish", "--root", str(self.root),
                                 "--snapshot", str(self.snapshot), "--body", str(self.body),
                                 "--output", self.output_name, "--replace"], capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o600)

    @unittest.skipIf(os.name == "nt", "POSIX umask permission assertion")
    def test_new_output_obeys_umask(self):
        self.capture()
        # Use a separate process so the test never changes its own global umask.
        code = "import os, runpy, sys; os.umask(0o027); sys.argv = sys.argv[1:]; runpy.run_path(sys.argv[0], run_name='__main__')"
        result = subprocess.run([sys.executable, "-c", code, str(SCRIPT), "publish", "--root", str(self.root),
                                 "--snapshot", str(self.snapshot), "--body", str(self.body), "--output", self.output_name],
                                capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o640)

    def test_invalid_body_does_not_create_output(self):
        self.capture()
        invalid = ["", "# Missing notes", BODY + binding.NOTES_START,
                   binding.NOTES_END + binding.NOTES_START, "---\n{}\n---\n" + BODY]
        for body in invalid:
            with self.subTest(body=body):
                self.body.write_bytes(body.encode("utf-8"))
                self.publish(expected=2)
                self.assertFalse(self.output.exists())

    def test_existing_snapshot_is_not_overwritten(self):
        self.capture()
        manifest = (self.snapshot / "manifest.json").read_bytes()
        self.capture(expected=2)
        self.assertEqual((self.snapshot / "manifest.json").read_bytes(), manifest)

    def test_late_source_change_aborts_atomic_replacement(self):
        old = self.create_map()
        original = binding.ensure_sources
        calls = [0]

        def change_source(*args, **kwargs):
            calls[0] += 1
            if calls[0] == 2:
                self.source.write_bytes(b"changed at final check")
            return original(*args, **kwargs)

        with mock.patch.object(binding, "ensure_sources", side_effect=change_source):
            self.publish(replace=True, expected=1)
        self.assertEqual(self.output.read_bytes(), old)
        self.assertFalse(list(self.output.parent.glob(".pin-map-*.tmp")))

    def test_concurrent_output_edit_is_preserved(self):
        self.create_map()
        original = binding.ensure_sources
        calls = [0]

        def edit_output(*args, **kwargs):
            calls[0] += 1
            if calls[0] == 2:
                self.output.write_bytes(b"concurrent user edit")
            return original(*args, **kwargs)

        with mock.patch.object(binding, "ensure_sources", side_effect=edit_output):
            self.publish(replace=True, expected=2)
        self.assertEqual(self.output.read_bytes(), b"concurrent user edit")

    def test_concurrent_output_creation_is_not_overwritten(self):
        self.capture()
        original = binding.ensure_sources
        calls = [0]

        def create_output(*args, **kwargs):
            calls[0] += 1
            if calls[0] == 2:
                self.output.write_bytes(b"concurrently created")
            return original(*args, **kwargs)

        with mock.patch.object(binding, "ensure_sources", side_effect=create_output):
            self.publish(expected=2)
        self.assertEqual(self.output.read_bytes(), b"concurrently created")

    def test_registry_hash_parity(self):
        registry_path = SCRIPT.parents[2] / "artifact-conventions" / "scripts" / "registry_check.py"
        registry_spec = importlib.util.spec_from_file_location("registry_check", registry_path)
        registry = importlib.util.module_from_spec(registry_spec)
        registry_spec.loader.exec_module(registry)
        for data in (b"a\r\nb\r", b"a\0\r\n", b"\xff\r\n"):
            self.assertEqual(binding.source_digest(data, binding.selected_mode(data, False)), registry.data_hash(str(self.root), self.name, data))
        subprocess.run(["git", "init", str(self.root)], check=True, capture_output=True)
        (self.root / ".gitattributes").write_bytes(b"*.net filter=lfs\n")
        self.assertEqual(binding.source_digest(b"a\r\n", "raw"), registry.data_hash(str(self.root), self.name, b"a\r\n"))

    def test_real_cli_exit_and_utf8_pipe(self):
        self.create_map()
        env = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONUTF8="0")
        result = subprocess.run([sys.executable, str(SCRIPT), "check", "--root", str(self.root), "--map", self.output_name],
                                capture_output=True, env=env, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(self.name, result.stdout.decode("utf-8"))


def main():
    binding.utf8_output()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SourceBindingTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    for test, error in result.failures + result.errors:
        print("FAIL {}: {}".format(test.id(), error.splitlines()[-1]))
    if result.wasSuccessful():
        print("PASS mcu-pin-map source binding: {} deterministic tests".format(result.testsRun))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
