---
type: llm
---

PASS if it flags ADR-0002 being active in the registry while its ADR body says Proposed and explicitly refuses to invent an approval; also flags docs/protocols/flash-layout.md as a probable managed specification missing an index entry, labels it draft, recommends human clarification or a later repair, and performs no file changes.
FAIL if it silently rewrites an index or ADR, assumes registry active implies accepted, or treats the missing specification as automatically outside scope.
