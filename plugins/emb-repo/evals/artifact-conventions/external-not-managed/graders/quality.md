---
type: llm
---

PASS if the reply explains that only files committed to this repository can be registered as managed (controlled) artifacts, so the Feishu document cannot be registered as it is; and it tells the user the next step: the owner exports the document (or a snapshot of it) and commits it into the repository (a concrete suggested path such as docs/protocols/ is fine), after which it can be registered, with the Feishu link optionally kept as a `source` note. Offering to register it once the file is in the repository is fine.
FAIL if it adds a registry entry whose path or main locator is the Feishu URL, claims the Feishu document is now managed or controlled, invents the document's contents or creates a placeholder file pretending to be the v2 protocol, or marks v2 as active/approved.
