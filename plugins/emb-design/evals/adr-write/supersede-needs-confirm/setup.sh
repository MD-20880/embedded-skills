#!/usr/bin/env bash
# 构造一个已有 ADR 的仓库：ADR 2 已决定采用供应方 V 的协议栈，将被新决定推翻。
set -euo pipefail
mkdir -p docs/adr
printf 'docs/adr' > .adr-dir
cat > docs/adr/0001-record-architecture-decisions.md <<'MD'
# 1. 用 ADR 记录架构决定

Date: 2025-11-01

## Status

Accepted

## Context

需要记录项目中的架构决定。

## Decision

采用 Nygard 格式的 ADR，与 adrs 兼容，放在 docs/adr。

## Consequences

重要决定都有可追溯的记录。
MD
cat > docs/adr/0002-use-vendor-stack.md <<'MD'
# 2. 无线链路采用供应方 V 的协议栈

Date: 2025-12-01

## Status

Accepted

## Context

无线链路需要组网协议，供应方 V 有现成的私有协议栈。

## Decision

我们采用供应方 V 的私有协议栈。

## Consequences

依赖 V 交付协议栈和技术支持（#40）。

## 决策信息

- 决策人：项目负责人
- 确认：项目负责人，2025-12-01，周会
- 关联 issue：#40
MD
