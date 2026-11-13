# CH7 source and known-answer repair

This versioned engineering repair addresses the November 12 owner preflight.
The original adapter, fixtures, evidence and candidate plans remain preserved.
It does not change the source population, projected fields, numerical model,
comparators, effect thresholds or campaign allocation.

DESIGN CHECK: LESSONS sections 3–5 were reread November 13, 2026. With either a
scientific null or alternative, an authenticated stopped and checkpointed source
must produce the exact declared rows without changing source bytes. Missing
files, sidecars, changed hashes, incomplete sources or changed output rows must
fail closed. The gates guard evidence mutation and self-confirming qualification.

The v2 source adapter uses SQLite URI read-only immutable opens, query-only mode,
and refusal of WAL, shared-memory or journal sidecars, including empty ones.
Only its newly created private output writer remains mutable. Immutable opens
require a stopped source under exclusive operational ownership; they are not
a way to read a live database. Source and output hashes remain authenticated by
the existing checkpoint/seal protocol. No global SQLite or legacy adapter state
is patched. Snapshot readers do not delete sidecars or checkpoint evidence.

The v2 source fixture specifies all expected fields independently, covering both
player roles, white wins, black wins, draws and unknown results across the
original three-month frame. Mutation checks deliberately give execution and
replay the same faulty projection: the independently authored answers must
still reject it. Exact replay alone cannot establish a correct projection.

The smaller route is this source-only constructed regression check, under a
bounded native job with two numerical threads. It contains no real records.
The prepared complete numerical fixture remains separate: running the source
check does not qualify the numerical model or admit production work. Remaining
work is numerical owner review, complete native qualification and explicit
versioned consumer/plan integration. Original v1-pinned candidate plans must
not silently be redirected to v2.
