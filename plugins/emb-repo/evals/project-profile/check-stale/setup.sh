#!/usr/bin/env bash
# 构造一个画像已过期的仓库：preset old_board-v1 与目录 boards/old_board_v1 已被删除。
set -euo pipefail
mkdir -p docs boards/new_board_v2
cat > CMakePresets.json <<'JSON'
{"version": 6, "configurePresets": [{"name": "new_board-v2", "generator": "Ninja", "binaryDir": "out"}]}
JSON
echo "# New board V2" > boards/new_board_v2/README.md
cat > docs/embedded-profile.md <<'MD'
---
profile_version: 1
project: demo
updated: 2025-01-01
---

# 项目画像：demo

## 1. 项目概述
- 产品：演示固件（README.md）

## 4. 构建与烧录
| 板 / 版本 | 构建命令 |
| --- | --- |
| old board v1 | `cmake --workflow --preset old_board-v1` |

## 5. 目录约定
| 目录 | 职责 |
| --- | --- |
| `boards/old_board_v1/` | 旧板支持 |
MD
