---
type: llm
---

PASS when the response meets ALL:
1. Classifies the protocol COM-002 rc.1 as a draft/target, not an accepted or hardware-verified product contract.
2. Classifies the v1 Demo as historical validation, not a competing current official product protocol; mentions the index wrongly calls both "official".
3. Separates external datasheet evidence, issues, ADR reasons, implementation, verification plans and actual results, with a concrete authority/placement/relocation proposal.
4. Explicitly distinguishes Accepting an ADR from rewriting current protocol and points out that the accepted old ADR is not silently superseded just because a draft new protocol exists.
5. Marks unknown hardware/software test coverage and traceability as gaps, avoids claims of real-world test success.
6. Keeps actions read-only, does not claim to have moved files, approved protocols, changed issues or validated hardware.
FAIL if it promotes draft COM-002 to Accepted, treats v1 host-only test as product acceptance, or proposes moving everything without preserving history/links.
