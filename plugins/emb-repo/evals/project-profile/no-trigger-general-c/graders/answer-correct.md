---
type: llm
---

PASS if the reply says volatile forces each access to be re-read from / written to memory (prevents the compiler from caching or optimizing away accesses) AND states that volatile does NOT guarantee atomicity (critical sections / disabling interrupts / atomic types are needed for read-modify-write or multi-word data).
FAIL if it claims volatile makes accesses atomic or thread-safe, or omits the atomicity point.
