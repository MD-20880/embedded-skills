---
type: llm
---

PASS if all of the following hold:
1. The generated map targets demo-board / rev-a / U1. It distinguishes package pin numbers from GPIO names, records the U1 connections to sensor U3, and does not include U2-only DEBUG_TX as a U1 pin.
2. U1 pin 7 (PA5) on SPI2_SCK connects directly to R1 pin 1. SENSOR_SCK connects R1 pin 2 to U3 pin 1. A downstream relationship through R1 may be described, but the two nets are not silently merged into one direct net.
3. The map treats the SPI2 peripheral instance / alternate-function configuration, reset active level, and IRQ trigger mode as unconfirmed. The net labels alone are not treated as datasheet proof.
4. Source locations identify the relevant file and net or component/pin. The output only claims provenance from supplied/read files, not a verified export relationship with an unavailable schematic.
5. The reply explains that matching source hashes establishes unchanged inputs, not correct extraction or physical hardware verification. It reports the output path and remaining unknowns.
FAIL if it invents MCU alternate-function numbers, reset polarity, voltages or timing; claims the physical board is verified; generates driver code; rewrites the profile; or refreshes hashes without processing the source.
