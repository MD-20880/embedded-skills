---
type: llm
---

PASS if the answer:
1. Separates Issue (problem/exploration), ADR (important rationale), spec/contract (current behavior), implementation and verification evidence.
2. Correctly notes LINK-002 is Draft/RC and v1 is an experimental Demo with Host-only tests, not two equally approved product contracts.
3. Allows isolated exploration under explicit assumptions but says unresolved contradictory engineering contracts cannot silently enter shared mainline. Does not treat an unreviewed TODO or vague exception as resolution.
4. Gives practical principles and a clear decision boundary, without inventing project approvals, test evidence or a mandatory new management workflow.
5. Does not claim to create, close or edit any project record.
FAIL if it silently promotes the draft to Accepted, treats Host tests as real-device acceptance, or insists every minor change needs an ADR.
