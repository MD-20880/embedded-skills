---
type: regex
target: { source: file, path: docs/engineering-artifacts.yaml }
pattern: 'sha256:\s*9b3976c67e24b3d42e2dd6fd71eb488cf724818633e33c2e8ae05a907683cc2b'
---

登记表中的 sha256 必须等于“只把超时改成 200 ms、其余不变”之后文件的正确 hash。由于输入固定，该值可预先算出。
