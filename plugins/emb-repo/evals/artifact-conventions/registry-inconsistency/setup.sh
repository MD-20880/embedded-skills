#!/usr/bin/env bash
set -euo pipefail
mkdir -p docs/adr docs/protocols
cat > docs/engineering-artifacts.yaml <<'EOF'
schema_version: 1
types:
  decision:
    purpose: "重大架构决定"
  specification:
    purpose: "产品协议规范"
artifacts:
  - id: ADR-0002
    type: decision
    path: docs/adr/0002-boot.md
    status: active
    scope: ["project"]
EOF
cat > docs/adr/0002-boot.md <<'EOF'
# ADR-0002: Boot Ownership
## Status
Proposed
## Decision
Proposed only; NOT ACCEPTED.
EOF
cat > docs/protocols/flash-layout.md <<'EOF'
# Flash Layout Contract
Scope: current production boards
Status: Draft
Describes the persistent boot metadata and compatibility interface; the registry has no entry for it.
EOF
