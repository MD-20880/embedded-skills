---
type: llm
---

PASS if the answer:
1. Gives a verdict of not passed (or conditional with explicit changes required), not a plain pass.
2. Asks for the test image source and host scripts to be moved out of the zip into normal repository directories (with a README) and delivered as mergeable code, because source only inside an archive is not delivered.
3. Asks for raw logs to be removed from the repository (attach as an archive on the issue with file name and SHA-256) and the record cut to about one page, dropping the lease timeline, per-file SHA list and encoding checks.
4. Asks for the image identity: BIN SHA-256 and commit for each image.
5. Flags the "disconnect after 3 CRC errors" guard as an unjustified gate outside the test scope that should be removed or justified with a source, and asks for "Refs #131" instead of "Closes #131".
6. Does not claim to have posted comments or changed labels.
FAIL if it accepts the PR as is, or treats the 0.04% figure alone as sufficient.
