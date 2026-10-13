#!/usr/bin/env bash
set -euo pipefail
mkdir -p docs/protocols
cat > docs/engineering-artifacts.yaml <<'YAML'
schema_version: 1
types:
  specification:
    purpose: "正式协议和跨板通信行为规范"
artifacts:
  - id: SPEC-LINK-001
    type: specification
    path: docs/protocols/link-v1.md
    status: active
    scope: ["project"]
YAML
cat > docs/protocols/link-v1.md <<'MD'
# 链路协议 v1
手套与主机之间的帧格式说明。
MD
