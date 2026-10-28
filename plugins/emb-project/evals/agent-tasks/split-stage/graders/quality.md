---
type: llm
---

PASS if the drafted execution issue(s):
1. Split development from the real-board test: the 10-minute frame-loss check on A2 bottom V2.5 + A1 V1.5 is a separate issue (e.g. labelled needs:hw), and host tests are not treated as satisfying it.
2. Are self-contained: the "buffer depth 4 blocks" decision from chat is written into the issue body (with its origin), rather than "see chat"; inputs are repository paths such as docs/link.md section 5.
3. State scope as directories (allowed to change / add, e.g. projects/a2_bottom/, services/audio/, tests/host/) and say everything else is out of scope.
4. Have checkable completion criteria with units and an evidence level (e.g. L1 host test, L2/L3 board), say the PR should use "Refs #" rather than "Closes", and include stop conditions such as unclear protocol fields or needing to change the interface.
5. Are only drafts: the answer does not claim to have created issues on GitHub.
FAIL if development and the board test are one issue, if the body says "as discussed" without the actual value, or if scope is described only as features without directories.
