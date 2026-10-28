#!/usr/bin/env bash
set -euo pipefail
mkdir -p docs
cat > docs/audio-design.md <<'EOF'
# 音频模块设计
## 3 缓冲
取块间隔 5 ms。因为显示整帧刷新要 8.3 ms，NFC 一次事务 4 ms，主循环最长阻塞取 8.3 ms，所以缓冲取 N_BLK=4。
## 5 带宽
| 业务 | 上行 |
| --- | --- |
| 音频 | 34.6 kB/s |
| 显示回执 | 1.2 kB/s |
| 输入事件 | 2.1 kB/s |
| 合计 | 37.9 kB/s，链路上限 49 kB/s |
## 6 发送优先级
链路控制 > 响应 > 事件 > 音频流。
EOF
cat > docs/display-design.md <<'EOF'
# 显示模块设计
## 6 帧
整帧刷新 8.3 ms。
## 9 链路占用
显示回执约 1.2 kB/s。与音频、输入合计约 38 kB/s。请求窗口以显示为主，其他服务排在显示之后。
EOF
cat > docs/link-protocol.md <<'EOF'
# 板间链路协议
## 4 线格式
帧头 4 字节，CRC16。
## 8 CPU 估算
按上行合计约 45 kB/s 估算，接收侧 CPU 占用约 12%。
EOF
