#!/usr/bin/env bash
# 构造一个最小的双板固件仓库，用于 project-profile 的 init 评测。
set -euo pipefail
mkdir -p boards/board_a_v1 boards/board_b_v2 cmake drivers/bmi270 docs tests
cat > README.md <<'MD'
# Demo Firmware

手环固件仓库，当前处于硬件调试阶段。

| 板 | preset | MCU |
| --- | --- | --- |
| A 主板 V1 | `board_a-v1` | GD32F303RCT6（256 KB Flash / 48 KB RAM） |
| B 传感板 V2 | `board_b-v2` | CH32V203G6U6（32 KB Flash / 20 KB RAM） |

构建：`cmake --workflow --preset <preset>`；主机测试：`cmake --workflow --preset host-tests`。
MD
cat > CMakePresets.json <<'JSON'
{
  "version": 6,
  "configurePresets": [
    {"name": "base", "hidden": true, "generator": "Ninja", "binaryDir": "${sourceDir}/out/${presetName}"},
    {"name": "board_a-v1", "inherits": "base", "toolchainFile": "cmake/toolchain-arm-none-eabi.cmake", "displayName": "A V1 (GD32F303)"},
    {"name": "board_b-v2", "inherits": "base", "toolchainFile": "cmake/toolchain-riscv.cmake", "displayName": "B V2 (CH32V203)"},
    {"name": "host-tests", "inherits": "base", "displayName": "PC unit tests"}
  ]
}
JSON
cat > cmake/toolchain-arm-none-eabi.cmake <<'CM'
set(CMAKE_C_COMPILER arm-none-eabi-gcc)
add_compile_options(-mcpu=cortex-m4 -mthumb)
CM
cat > cmake/toolchain-riscv.cmake <<'CM'
set(CMAKE_C_COMPILER riscv-none-elf-gcc)
add_compile_options(-march=rv32imac -mabi=ilp32)
CM
cat > boards/board_a_v1/gd32f303.ld <<'LD'
MEMORY
{
  FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 256K
  RAM   (xrw) : ORIGIN = 0x20000000, LENGTH = 48K
}
LD
cat > boards/board_b_v2/ch32v203.ld <<'LD'
MEMORY
{
  FLASH (rx)  : ORIGIN = 0x00000000, LENGTH = 32K
  RAM   (xrw) : ORIGIN = 0x20000000, LENGTH = 10K
}
LD
echo "# A 主板 V1：GD32F303RCT6，外设 BMI270 (I2C0)" > boards/board_a_v1/README.md
echo "# B 传感板 V2：CH32V203G6U6" > boards/board_b_v2/README.md
echo "/* BMI270 IMU driver */" > drivers/bmi270/bmi270.c
echo "# Host tests (Unity)" > tests/README.md
