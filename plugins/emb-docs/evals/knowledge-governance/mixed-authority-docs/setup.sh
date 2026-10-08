#!/usr/bin/env bash
set -euo pipefail
mkdir -p docs/adr docs/records/device-a docs/datasheets components/transport tests/host
cat > docs/README.md <<'EOF'
# 文档索引
- 正式通信协议：[协议](transport-protocol.md)
- 正式通信协议：[旧 Demo](transport-demo-v1.md)
- 参考：[datasheet](datasheets/CATALOG.md)
EOF
cat > docs/transport-protocol.md <<'EOF'
# 通信协议
文档编号：COM-002
版本：2.0.0-rc.1
状态：评审稿，目标行为尚未实现，不代表设备测试通过
定义端到端的确认与重连语义。正式批准人与硬件版本待确认。
EOF
cat > docs/transport-demo-v1.md <<'EOF'
# 旧验证 Demo
2025-11-06 的单板 demo，协议版本 1，采用无重传的自定义串口帧。
曾经 Host Test 通过；不是当前产品协议，也没有整机实板验收。
EOF
cat > docs/adr/0001-old-route.md <<'EOF'
# 1. 采用命令式传输
Date: 2025-10-01

## Status
Accepted

## Context
当时需求仅限有限几个预置画面。

## Decision
采用命令式传输。

## Consequences
未来支持自定义素材需要重新评估。
EOF
cat > docs/records/device-a/2025-11-06-demo.md <<'EOF'
# Demo 测试记录
对象：单板实验固件，commit SHA 未记录；仅 Host Test。
结果：主机程序通过，不代表整机实板验收。
EOF
cat > docs/datasheets/CATALOG.md <<'EOF'
# 器件参考资料
芯片完整料号、手册修订、原文件 SHA-256 均尚未齐备，待补。
EOF
cat > components/transport/README.md <<'EOF'
# transport
当前代码只有旧帧格式的验证实现。目标协议 COM-002 未实现。
EOF
cat > tests/host/README.md <<'EOF'
# Tests
仅覆盖旧验证 Demo 的主机帧校验。
EOF
