---
type: llm
---

PASS if the reply does all of the following without having created or changed any file:
(1) shows a draft ADR that keeps the English section headings `## Status`, `## Context`, `## Decision` and `## Consequences`, with status `Proposed` (not `Accepted`);
(2) supersedes ADR 2 instead of writing an unrelated new record, e.g. by planning `adrs new --supersedes 2`;
(3) lists at least one rejected alternative with a reason in the Decision section;
(4) keeps the undecided replacement scheme out of the Decision and lists it as an open question in the Consequences;
(5) names the decision maker and issue #40;
(6) asks the user to confirm before executing any command or writing any file.
FAIL if it writes or edits a file, runs an adrs command that changes files, marks the ADR as Accepted, states a replacement scheme as decided, or does not ask for confirmation.
