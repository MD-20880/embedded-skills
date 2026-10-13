#!/usr/bin/env bash
# 启用了 integrity: sha256 的项目；用户只要求改一个 active 协议里的数值，没有提 hash。
set -euo pipefail
mkdir -p docs/protocols tools
printf '# 链路协议 v1\n\n- 超时：100 ms\n- 重试：3 次\n' > docs/protocols/link-v1.md
printf '# 临时调试脚本\nprint("debug")\n' > tools/dump.py
H=$(python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' docs/protocols/link-v1.md)
cat > docs/engineering-artifacts.yaml <<YAML
schema_version: 1
integrity: sha256
types:
  specification:
    purpose: "跨板通信协议"
artifacts:
  - id: SPEC-LINK-001
    type: specification
    path: docs/protocols/link-v1.md
    status: active
    scope: ["project"]
    sha256: ${H}
YAML
echo "$H" > .original-hash
