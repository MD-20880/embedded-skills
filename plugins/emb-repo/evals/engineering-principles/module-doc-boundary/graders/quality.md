---
type: llm
---

PASS if the answer:
1. Says each module document should describe only its own business: purpose, internal flow, provided and required interfaces, and its own resource needs (e.g. audio may state "I use 34.6 kB/s" or "my block interval must be under X").
2. Says link totals and headroom, send/request priorities, and parameters chosen because of another module (audio N_BLK derived from display frame time) belong in a joint/system-level document, with module documents only referencing it.
3. States that a number should have one authoritative place, and that modules should not reference each other's parameters.
4. Points out the concrete inconsistency (about 38 kB/s in audio/display vs about 45 kB/s in the link protocol) as something to reconcile and confirm, without silently declaring one value correct.
5. Does not claim to have edited any file.
FAIL if it recommends keeping a copy of the totals in every module document, or merges everything into one all-purpose document without separating module and joint concerns.
