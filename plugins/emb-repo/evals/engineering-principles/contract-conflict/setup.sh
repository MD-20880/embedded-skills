#!/usr/bin/env bash
set -euo pipefail
mkdir -p docs/adr docs/records components/uart tests/host
cat > docs/README.md <<'EOF'
# 文档索引
- [正式通信协议](link-v2.md)
- [正式通信协议](legacy-demo.md)
EOF
cat > docs/link-v2.md <<'EOF'
# 通信协议 2.0
编号：LINK-002
状态：Draft/RC；尚未获决策人批准，尚未在设备上验证。
希望使用带重传和会话身份的新版报文。
EOF
cat > docs/legacy-demo.md <<'EOF'
# 旧 UART Demo
v1 Demo，用于一次板级演示。通过主机单元测试。
并非已批准的产品链路，不支持新版的会话身份。
EOF
cat > docs/adr/0001-use-legacy-transport.md <<'EOF'
# 1. 使用旧 UART demo 进行探索
Date: 2025-05-02

## Status
Accepted

## Context
当时需要最小通信验证。

## Decision
仅实验阶段使用旧传输。

## Consequences
产品正式协议另行评审。
EOF
cat > docs/records/test.md <<'EOF'
# 旧通信试验
使用主机模拟，不包含真实板卡、固件 SHA 或线缆测量。
EOF
cat > components/uart/README.md <<'EOF'
# UART Transport
代码仍实现实验版本 v1，未实现 Draft 的 LINK-002。
EOF
cat > tests/host/README.md <<'EOF'
# Tests
仅对旧 Demo 报文进行 Host Test。
EOF
