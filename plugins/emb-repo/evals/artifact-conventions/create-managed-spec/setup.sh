#!/usr/bin/env bash
set -euo pipefail
mkdir -p docs/protocols docs/adr tools
cat > docs/README.md <<'EOF'
# Documentation
项目受管理文件入口：docs/engineering-artifacts.yaml
EOF
cat > docs/engineering-artifacts.yaml <<'EOF'
schema_version: 1
types:
  specification:
    purpose: "正式协议和跨板通信行为规范"
  decision:
    purpose: "重大架构决定和取舍记录"
  calibration-record:
    purpose: "实板标定记录；项目扩展的受管理类型"
artifacts:
  - id: SPEC-LINK-001
    type: specification
    path: docs/protocols/link-v1.md
    status: active
    scope: ["project"]
  - id: ADR-0001
    type: decision
    path: docs/adr/0001-transport.md
    status: active
    scope: ["project"]
EOF
cat > docs/protocols/link-v1.md <<'EOF'
# 链路协议 v1
已批准的 v1 帧格式说明，尚未规定新的超时释放行为。
EOF
cat > docs/adr/0001-transport.md <<'EOF'
# ADR-0001 Transport
## Status
Accepted
## Decision
使用 v1 链路作为当前共享接口
EOF
cat > tools/parse_uart_log.py <<'EOF'
# Temporary debug helper; not an engineering artifact type
print("placeholder")
EOF
