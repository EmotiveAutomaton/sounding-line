# Checkpoint both GO3 source passes and ordered projection

**DESIGN CHECK, before admission.** Five whole-site projections must not rely
on an unmeasured small-source forecast. This successor preserves every source
column, exclusion, salted join, reason label, sorted row and before/after state.
The original whole-site and extraction-integrity modules remain immutable.

Declared ingestion work is the sum of the authenticated uncompressed byte
sizes of Posts.xml and PostHistory.xml. The first counted stage stops exactly
at `ceil(0.05 * total bytes)` consumed by the XML parser. This is a byte-work
pilot, not a 5% sample of people, posts or edits. Archive decode, authentication,
prefix reconstruction, indexing, output projection and all verification cost
are charged in addition; ingestion extrapolation does not estimate those
other phases. The owner reviews measured CPU/disk and later-phase uncertainty
before admitting continuation.

XML feeds end at the exact byte boundary even inside a row. SQLite commits
every completed row, both per-member byte and record cursors, and counts in
the same fully synchronous transaction. Resume reconstructs parser state by
re-reading the saved prefix and verifying its completed-row count; it does
not discard or duplicate the partially read row. Completed XML row elements
are removed from the parser tree to bound retained memory. Source bytes and
archive/member provenance are checked before every reentry. The first-5%
pause fires once in the execution tree and once in independent replay.

The sorted index is transactional and can roll back on a resource request.
Projection follows post, timestamp, history ordinal and insertion-order tie
break, the latter making the old index's order for equal keys explicit.
Each complete history batch saves a sealed parquet part and, transactionally,
its cursor, counts and the current post's three previous channel bodies.
A pause inside a long post therefore preserves title/body/tag predecessor
state. Text and salted keys remain private. Empty output parts are valid
support accounting; a completely empty final edit table retains the original
source failure. Concatenation preserves all row order and can restart from
sealed parts without redoing source ingestion.

Every pause closes SQLite and seals its entire byte snapshot and saved state.
The reviewed runtime copies an authentic stopped predecessor into a new
attempt. The original is immutable, and changing a database, seal, part,
source, salt or code refuses. The only adjustable producer bound is the
already recognized `max_wall_seconds`; first-5% arithmetic is fixed in code.

Independent verification rebuilds both full XML passes and the complete
projection into a separate database. It repeats the source pilot safely,
then compares the full source receipt and every final row. The final row
comparison has a hash-bound checkpoint cursor and explicit verified-false
yield; verified-true requires the complete row census.

Archive extraction remains an atomic setup unit using the separately reviewed
strict guard. An interrupted decode has no valid extraction seal and refuses
reuse; its files and cost are retained for a fresh attempt. It is not claimed
as a resumable decoder checkpoint. Subsequent parsing/index/projection/replay
are resumable. Setup can still be interrupted by the outer containment guard;
the pilot must expose that cost before an unsafe long setup is repeated.

Native fixtures use an actual tiny 7z archive, byte-boundary pause inside XML,
copied immutable continuation, a second pause inside one post, independent
native replay and exact equality to every original whole-site projected row
and disposition. Corrupted stopped databases and parts refuse. No human
source prefix is launched by the builder. The smaller route remains the
packet's whole-editor sample after complete source support, within the
250,000 CPU-second GO3 and 600,000-second GO family allowances. All source
work is charged; no separate source sub-allocation blocks authorized work.
