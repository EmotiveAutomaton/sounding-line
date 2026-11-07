# GO2 same-document Git history correction

The original source pilot failed after two sealed documents. Git's `--follow`
reported a copy from a different proposal; the source handled renames but kept
the target filename while following the origin's earlier commit. The target did
not exist there. This is a source-engineering failure, not a scientific result.
The original attempt and every source pin remain unchanged.

**DESIGN CHECK.** LESSONS 2–5 reread November 7. A copied document starts at its
copy-target version. The unrelated origin is not an earlier draft of this
document. Follow renames as before; stop history at copy creation, retain that
target version, and count both copy boundaries and earlier origin revisions
excluded. A deletion has no document text and explicitly breaks adjacency.
Missing objects at ordinary versions still fail; no network fallback is added.

The parser and all anchor rules remain frozen: licensed Motivation-bearing
versions, at least 20% goal-token change, lexical added text, bulk commits
excluded, and the before/after windows. The same salted identities, repository
heads and current inventory bind the new source. Old source modules stay intact.

**Case and check.** Constructed actual Git history must expose a copy-origin
record and retain the new document's first version only. Full source projection
then independently replays in a fresh process. Separate tests cover deletion
gaps, missing ordinary objects, unchanged rename behavior and sealed output
tampering. No preference scores enter this diagnosis or repair.

**Cost and smaller route.** Use the same 72-of-1,440-document first stage under
GO2's 100,000 CPU-second ceiling and GO's 600,000 family allowance. Old failed
work remains charged. Document seals and cooperative CPU/yield limits remain;
the whole source and fresh replay remain required before any scientific result.
No old seal is imported under the successor's changed code binding. The owner
reviews the measured complete-source forecast before continuation.
