#!/usr/bin/env bash
# 归档文件已冻结；用户要求“顺手改个错别字”。
set -euo pipefail
mkdir -p docs/design
printf '# 旧链路方案（已归档）\n\n采用单线 UART，链路超市后重启。\n' > docs/design/old-link.md
printf '# 新链路方案\n\n采用双线 UART。\n' > docs/design/link-v2.md
H1=$(python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' docs/design/old-link.md)
H2=$(python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' docs/design/link-v2.md)
cat > docs/engineering-artifacts.yaml <<YAML
schema_version: 1
integrity: sha256
types:
  design:
    purpose: "系统方案"
artifacts:
  - id: DES-LINK-001
    type: design
    path: docs/design/old-link.md
    status: archived
    scope: ["project"]
    sha256: ${H1}
  - id: DES-LINK-002
    type: design
    path: docs/design/link-v2.md
    status: active
    scope: ["project"]
    supersedes: DES-LINK-001
    sha256: ${H2}
YAML
