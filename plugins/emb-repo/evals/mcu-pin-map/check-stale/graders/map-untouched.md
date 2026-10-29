---
type: regex
target: { source: file, path: docs/hardware/demo-board/rev-a/U1-pin-map.md }
pattern: "\\A---\\n\\{\"schema\":\"mcu-pin-map/v1\",\"target\":\\{\"board\":\"demo-board\",\"revision\":\"rev-a\",\"mcu_ref\":\"U1\"\\},\"source_binding\":\\{\"hash_policy\":\"sha256-text-lf-binary-raw-v1\",\"inputs\":\\[\\{\"path\":\"hardware/demo-board/rev-a\\.net\",\"hash_mode\":\"text-lf\",\"sha256\":\"4804407ebe35a76bdd5eeecdcd6b78657f3fa86c7e0ab9a62e1a736d56390aca\"\\}\\]\\}\\}\\n---\\n# MCU pin map fixture\\n\\n\\| MCU \\| Package pin \\| GPIO \\| Net \\| Endpoint \\|\\n\\| --- \\| --- \\| --- \\| --- \\| --- \\|\\n\\| U1 \\| 10 \\| PB0 \\| CS_OLD \\| U3\\.4 \\|\\n\\n## 人工备注\\n<!-- manual-notes:start -->\\n人工备注：板上可能存在飞线，未核实。\\n<!-- manual-notes:end -->\\n\\Z"
---

检查后文件必须逐字保持原状；包括旧输入摘要、旧连接和人工备注。
