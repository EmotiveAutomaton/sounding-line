# PLAN exact UTF-16 implementation

The original source timing projects too much work to retain its registered
900 CPU-second downstream reserve within T5's original allowance. Preserve that
timing and cost disposition. This separately registered `.h1` implementation
changes only UTF-16 list/byte conversion in the canonical replay: the same
unsigned 16-bit integers are converted using Python's array module rather than
one Python loop per character. Endianness is explicit. The canonical replay and
edit algorithms, strict UTF-16 checks, midpoint, raw inputs, menu support, hashes,
comparators, selection and private/public boundaries stay unchanged.

DESIGN CHECK: LESSONS 2–5 reread November 4. Known Unicode conversion and complete
canonical histories must agree with the original implementation; malformed edits
must still refuse. Every original source test runs against this successor too.
Full native execution/verification and a separate timing prefix remain mandatory.
Fresh full-source replay still compares the independent byte implementation,
canonical replay and frozen source snapshots. No passing threshold is relaxed.

Case and check and smaller route are exactly [the original source plan](PLAN_SOURCE.md).
Charge all original attempts and both versions' validation (120 CPU seconds total
reserved) to the same 3,600-second allowance. Full admission still requires the
3x measured execution envelope, retained-byte forecast, and 900 CPU seconds for
later local work. No paid call or scientific comparison is admitted by conversion
parity. All original evidence remains retained, and no live source is edited.
