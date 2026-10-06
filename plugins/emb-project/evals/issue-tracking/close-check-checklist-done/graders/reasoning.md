---
type: llm
---

PASS if the reply concludes the issue cannot be closed AND gives all of these reasons: (1) ticked checkboxes are actions, not a verdict or answer — the real question "whether the antenna trace must change in board rev C" has no recorded answer or decision maker; (2) the RSSI / distance results have no pass criteria (limit, conditions) and no evidence level, so they cannot be judged as passed; (3) the applicable object (board / hardware revision / firmware version) is missing. It should also propose splitting into separate issues (e.g. verification items plus a question about changing the antenna trace).
FAIL if it says the issue can be closed, or omits any of reasons (1)–(3).
