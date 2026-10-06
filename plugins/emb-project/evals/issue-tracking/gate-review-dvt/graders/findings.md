---
type: llm
---

PASS if the reply gives exactly one of the three verdicts (可以进入 / 有条件进入 / 不能进入) AND: (1) flags V12 as having insufficient evidence (L2 on one dev board while L3 is required), so its "pass" is only preliminary; (2) flags D7 as not closable because a board-revision fix must be retested on the target hardware (rev C) and that has not happened; (3) lists Q4 as open and blocked externally with a deadline before DVT tooling; (4) lists D3 as a known accepted limitation; (5) presents the go/no-go decision items for the decision maker instead of making the decision on their behalf.
FAIL if it treats V12 as a solid pass, treats D7 as done, or omits any of points (1)–(5).
