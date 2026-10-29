---
type: regex
target: { source: file, path: docs/hardware/demo-board/rev-a/U1-pin-map.md }
pattern: '(?s)\A---\n(?=.*"schema"\s*:\s*"mcu-pin-map/v1")(?=.*"hash_policy"\s*:\s*"sha256-text-lf-binary-raw-v1")(?=.*"board"\s*:\s*"demo-board")(?=.*"revision"\s*:\s*"rev-a")(?=.*"mcu_ref"\s*:\s*"U1")(?=.*"hash_mode"\s*:\s*"text-lf")'
---
