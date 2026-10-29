---
type: regex
target: { source: file, path: docs/hardware/demo-board/rev-a/U1-pin-map.md }
pattern: '(?s)"inputs"\s*:\s*\[.*?\{(?=[^}]*"path"\s*:\s*"hardware/demo-board/rev-a\.net")(?=[^}]*"hash_mode"\s*:\s*"text-lf")(?=[^}]*"sha256"\s*:\s*"d0b33df0215ea8a1a7c45b73d68e173fc7f868105b1eddba6da294141a16974c")[^}]*\}'
---

此 SHA 对应 setup.sh 生成的 LF 网表。必须把正确摘要绑定在该网表条目上，不能只在正文出现一个任意 64 位值。
