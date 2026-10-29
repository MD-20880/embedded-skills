#!/usr/bin/env bash
set -euo pipefail
mkdir -p hardware/demo-board docs/hardware/demo-board/rev-a
# The map below was made from the following LF-terminated source:
# <export version="E"><nets><net name="CS_OLD"><node ref="U1" pin="10" pinfunction="PB0"/><node ref="U3" pin="4"/></net></nets></export>
# SHA256: 4804407ebe35a76bdd5eeecdcd6b78657f3fa86c7e0ab9a62e1a736d56390aca
cat > hardware/demo-board/rev-a.net <<'XML'
<export version="E"><nets><net name="CS_NEW"><node ref="U1" pin="11" pinfunction="PB1"/><node ref="U3" pin="4"/></net></nets></export>
XML
cat > docs/hardware/demo-board/rev-a/U1-pin-map.md <<'MD'
---
{"schema":"mcu-pin-map/v1","target":{"board":"demo-board","revision":"rev-a","mcu_ref":"U1"},"source_binding":{"hash_policy":"sha256-text-lf-binary-raw-v1","inputs":[{"path":"hardware/demo-board/rev-a.net","hash_mode":"text-lf","sha256":"4804407ebe35a76bdd5eeecdcd6b78657f3fa86c7e0ab9a62e1a736d56390aca"}]}}
---
# MCU pin map fixture

| MCU | Package pin | GPIO | Net | Endpoint |
| --- | --- | --- | --- | --- |
| U1 | 10 | PB0 | CS_OLD | U3.4 |

## 人工备注
<!-- manual-notes:start -->
人工备注：板上可能存在飞线，未核实。
<!-- manual-notes:end -->
MD
cat > docs/embedded-profile.md <<'MD'
---
profile_version: 1
project: demo-board
updated: 2026-10-30
---

# 项目画像：demo-board

## 2. 硬件清单
- demo-board rev-a，目标 U1；网表 hardware/demo-board/rev-a.net。
- 派生资料：docs/hardware/demo-board/rev-a/U1-pin-map.md。

## 5. 目录约定
- 网表在 hardware/demo-board/；派生资料在 docs/hardware/demo-board/rev-a/。

## 8. 文档约定
- 本任务只核查，不写文件。

## 9. 已知约束与坑
- 无实物验证记录。

## 10. 待确认
- 是否需要重新导出网表由维护者决定。
MD
