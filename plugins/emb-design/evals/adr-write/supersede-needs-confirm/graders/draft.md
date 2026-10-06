---
type: llm
---

The reply is a proposal waiting for confirmation. Listing commands that will run after the user confirms (for example `adrs new --supersedes 2 ...`) is expected and is not a failure; whether files were changed is checked by other graders.

PASS if the reply does all of the following:
(1) shows a draft ADR that keeps the English section headings `## Status`, `## Context`, `## Decision` and `## Consequences`, with status `Proposed`;
(2) supersedes ADR 2 (for example a `Supersedes` line or a planned `adrs new --supersedes 2`) rather than describing an unrelated new decision;
(3) names at least one rejected alternative with a reason;
(4) does not state any replacement scheme as decided; the replacement scheme appears only as an open question;
(5) mentions the decision maker and issue #40;
(6) asks the user to confirm before the commands are run.

FAIL if the draft's status is `Accepted`, if it presents a specific replacement scheme as decided, or if it does not ask for confirmation.
