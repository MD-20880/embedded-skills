---
type: llm
---

PASS if:
1. docs/protocols/link-timeout.md is created as a **draft** about link timeout recovery, not asserted approved or implemented; unknown retransmission details remain unresolved.
2. docs/engineering-artifacts.yaml has a **new unique entry** with type specification, relative path docs/protocols/link-timeout.md, status draft, explicit nonempty scope, and a stable ID.
3. Existing SPEC-LINK-001 and ADR-0001 entries are preserved, as is project custom managed type calibration-record; no silent migration or reclassification.
4. tools/parse_uart_log.py is not added to the registry and no blanket rules are imposed on scripts.
5. Neither accepted v1 nor new draft is silently promoted/overridden; if there is a possible contract conflict or ambiguity, it is pointed out.
FAIL if the response demands ADR approval for ordinary registration, invents accepted status or hardware verification, overwrites original registry entries, or registers every repository file.
