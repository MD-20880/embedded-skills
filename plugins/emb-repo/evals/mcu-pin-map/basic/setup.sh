#!/usr/bin/env bash
# Synthetic exported netlist: no real board or chip facts are embedded here.
set -euo pipefail
mkdir -p hardware/demo-board docs
cat > hardware/demo-board/rev-a.net <<'XML'
<?xml version="1.0" encoding="UTF-8"?>
<export version="E">
  <design><source>demo-board.kicad_sch</source><date>fixture</date><tool>synthetic-netlist-export</tool></design>
  <components>
    <comp ref="U1"><value>DEMO_MCU_A</value><footprint>DEMO_QFP</footprint></comp>
    <comp ref="U2"><value>DEMO_MCU_B</value><footprint>DEMO_QFP</footprint></comp>
    <comp ref="U3"><value>DEMO_SENSOR</value></comp>
    <comp ref="R1"><value>33R</value></comp>
    <comp ref="J2"><value>DEBUG</value></comp>
  </components>
  <nets>
    <net code="1" name="SPI2_SCK"><node ref="U1" pin="7" pinfunction="PA5"/><node ref="R1" pin="1"/></net>
    <net code="2" name="SENSOR_SCK"><node ref="R1" pin="2"/><node ref="U3" pin="1" pinfunction="SCK"/></net>
    <net code="3" name="SPI2_MISO"><node ref="U1" pin="8" pinfunction="PA6"/><node ref="U3" pin="2" pinfunction="SDO"/></net>
    <net code="4" name="SPI2_MOSI"><node ref="U1" pin="9" pinfunction="PA7"/><node ref="U3" pin="3" pinfunction="SDI"/></net>
    <net code="5" name="SENSOR_CS"><node ref="U1" pin="10" pinfunction="PB0"/><node ref="U3" pin="4" pinfunction="CS"/></net>
    <net code="6" name="SENSOR_RESET"><node ref="U1" pin="11" pinfunction="PB1"/><node ref="U3" pin="5" pinfunction="RESET"/></net>
    <net code="7" name="SENSOR_IRQ"><node ref="U1" pin="12" pinfunction="PB2"/><node ref="U3" pin="6" pinfunction="IRQ"/></net>
    <net code="8" name="DEBUG_TX"><node ref="U2" pin="7" pinfunction="PA5"/><node ref="J2" pin="1"/></net>
  </nets>
</export>
XML
cat > docs/embedded-profile.md <<'MD'
---
profile_version: 1
project: demo-board
updated: 2026-10-30
---

# 项目画像：demo-board

## 2. 硬件清单
- 板卡：demo-board，硬件 rev-a；本次整理 U1，U2 是独立 MCU（用户确认）。
- 输入：hardware/demo-board/rev-a.net；没有原理图原件或芯片手册。

## 5. 目录约定
- 硬件导出文件在 hardware/demo-board/；派生引脚资料放 docs/hardware/demo-board/rev-a/。

## 8. 文档约定
- 使用中文；保留原始网络名和器件位号；该项目尚未启用工程文件登记表。

## 9. 已知约束与坑
- 无实物验证记录。

## 10. 待确认
- MCU 复用选择、传感器复位极性与 IRQ 触发方式没有数据手册依据。
MD
