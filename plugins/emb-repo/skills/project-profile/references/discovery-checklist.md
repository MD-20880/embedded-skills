# 画像证据清单（Discovery Checklist）

按画像章节列出“去哪里找证据”。`scripts/scan_repo.py` 会自动收集其中能机械识别的部分，剩下的由 Claude 阅读文件确认。
**原则**：先读项目自己的说明（README、docs 索引、CLAUDE.md），再用配置文件核实，最后才从源码推断。

## 通用入口（最先读）

- 根目录 `README*`、`CLAUDE.md`、`AGENTS.md`、`CONTRIBUTING*`
- 文档索引：`docs/README.md`、`docs/index.md`、`doc/`
- 每个板 / 应用目录下的 `README*`

## 1. 项目概述

- 根 README 的第一段、“当前阶段 / 状态”相关段落
- `git log --oneline -20` 与最近活跃目录：判断阶段（大量 validation / bringup 提交 → 硬件调试期）

## 2. 硬件清单

| 线索 | 能得到什么 |
| --- | --- |
| `boards/`、`bsp/`、`board/`、`targets/` 目录名 | 板与版本列表 |
| 链接脚本 `*.ld`、`*.lds`、`*.icf`、`*.sct` 中的 `MEMORY` | Flash / RAM 起址与容量 |
| 启动文件 `startup_*.s/.S/.c` 文件名 | MCU 系列（如 `startup_gd32f30x_hd.s`） |
| 厂商头文件 `*_conf.h`、`system_*.c`、`stm32*xx_hal_conf.h` | MCU 系列与主频（`SystemCoreClock`、`HSE_VALUE`） |
| STM32CubeMX `*.ioc` | 精确型号、时钟树、引脚分配 |
| ESP-IDF `sdkconfig`、`CONFIG_IDF_TARGET` | 芯片型号 |
| Zephyr `boards/*/*.dts`、`prj.conf`、`west.yml` | 板、SoC、外设 |
| CMake 变量（`-mcpu=`、`MCU`、`CHIP`、`BOARD`） | 内核与型号 |
| `drivers/` 下的芯片名目录 | 关键外设芯片 |
| `docs/hardware/`、`docs/datasheets/`、`*.pdf` | 原理图、芯片手册位置 |

## 3. 软件栈

| 线索 | 能得到什么 |
| --- | --- |
| `FreeRTOSConfig.h` / `rtconfig.h`（RT-Thread）/ `prj.conf`（Zephyr）/ `tx_user.h`（ThreadX） | RTOS 种类与关键配置 |
| `vendor/`、`third_party/`、`lib/`、`Drivers/`、`components/` | SDK、HAL、第三方库 |
| `CMAKE_C_STANDARD`、`-std=` | 语言标准 |
| 子模块 `.gitmodules`、`west.yml`、`idf_component.yml` | 依赖与版本 |

## 4. 构建与烧录

| 线索 | 能得到什么 |
| --- | --- |
| `CMakePresets.json` | preset 名（常一板一个）、工具链文件 |
| `CMakeLists.txt` 中的自定义 target（`*-flash`、`*-debug`） | 烧录 / 调试命令 |
| `Makefile`、`*.mk` | make 目标 |
| `platformio.ini` | env 列表、`upload_protocol` |
| Keil `*.uvprojx`、IAR `*.ewp`、MounRiver `*.wvproj` | IDE 工程（构建需人工 / IDE） |
| `cmake/toolchain-*.cmake`、`tools/setup*`、`toolchains.json` | 工具链与版本 |
| `*.jlink`、`openocd*.cfg`、`*.launch`、`.vscode/launch.json` | 调试器类型 |
| `.github/workflows/`、`.gitlab-ci.yml`、`Jenkinsfile` | CI 中实际运行的构建与测试命令（最可靠） |

## 5. 目录约定

- 顶层目录列表 + 各目录 README 的第一句
- 文档中“目录分工”“放新文件”“新增一块板”等章节（如 `docs/build-layout.md`）

## 6. 编码约定

- `.clang-format`、`.clang-tidy`、`.editorconfig`、`cppcheck` 配置、MISRA 偏离记录
- 文档中的“编码规范 / 风格”章节
- 从代码抽样核实：错误码类型、日志宏、是否出现 `malloc`、ISR 函数写法

## 7. 测试与验证

- `tests/`、`test/`、`unity`、`cmocka`、`googletest` 等测试框架痕迹
- CTest preset（如 `host-tests`）、CI 中的测试步骤
- `validation/`、`records/`、`bringup/` 等目录及其 README

## 8. 文档约定

- `docs/README.md` 中的“放新文档”规则
- 已有协议文档的位置（`docs/interfaces/`、`components/*/docs/`）

## 9. 已知约束与坑

- README / 文档中的“注意”“已知问题”“勘误”“限制”段落
- `docs/records/`、`errata`、`known-issues`
- 代码中的 `HACK`、`WORKAROUND`、`ERRATA` 注释（只摘与硬件相关的）

## 无法确定时

写入第 10 节“待确认”，注明扫描到的线索，交给用户确认。**不要猜测型号、主频、容量等数值。**
