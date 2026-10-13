---
type: regex
target: { source: file, path: docs/engineering-artifacts.yaml }
flags: s
pattern: '^(?!.*feishu)(?!.*https?://).*id:\s*SPEC-LINK-001.*$'
---

登记表中不能出现飞书链接或任何 URL，且原有条目 SPEC-LINK-001 必须保留。
