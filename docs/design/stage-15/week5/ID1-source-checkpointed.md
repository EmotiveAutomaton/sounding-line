# Resume the complete ID1 source without losing partial response pairs

**DESIGN CHECK, 2026-11-07.** The unchanged archive's completed B2 census contains
70,332,355 CSV records. The exact first-5% work quantum is 3,516,618 records.
The earlier prefix-only ID1 source could measure cost but could not resume; it
must not be mistaken for a completed population. This successor changes source
execution only, preserving every ID1 pairing, chronology and privacy rule.

Read the same pinned archive and exact whitelisted columns. Salt response,
fingerprint and session keys before storing them. Retain the original pairing
UPSERT, including incomplete pairs, duplicates, conflicts, character totals and
first-seen metadata. Commit each source chunk and its cumulative CSV **record**
ordinal together in a fully synchronous SQLite transaction. A pause can split
the two sides of a response; its partial aggregate remains intact for the
successor. Never count physical lines as records: quoted newlines are valid CSV.

The first execution tree stops exactly at record 3,516,618, closes SQLite, and
seals the database hash with its source/configuration/ordinal state. It emits a
pause, never a complete source. The owner reviews measured CPU and disk use
before resuming into a fresh authenticated attempt. `pilot_rows=3516618` is a
fixed semantic setting that fires once in each execution or independent replay
tree. Subsequent resumes change only the existing `max_wall_seconds` operational
bound; no new runtime exception is required.

Compressed-source resume re-parses and discards exactly the already committed
record prefix, then begins new transactions. This avoids unsafe compressed-byte
seeks or physical-line assumptions. All re-reading time counts. A source hash,
database hash, transactional cursor, source-row total or salted-key binding
mismatch refuses. The stopped predecessor remains immutable and is copied only
through the reviewed resume adapter with all its original pins retained.

After the complete exact record census, build the original person/session index
and the original all-pair session counts. SQL index and census steps have a
progress handler that aborts on a resource or wall request. An unfinished SQL
stage is rolled back and restarted later; this cost is retained. Ordered case
projection saves parts only at complete 1,000-fingerprint boundaries, with
sealed rows, counts and last-fingerprint cursor committed together. Partial
in-memory people never become a saved case. The resulting case table retains
the same sort order, complete thirteen-scenario test and all exclusion counts
as the original source. Deterministic final part concatenation restarts if
interrupted; it is not a scientific analysis.

Fresh verification rebuilds the entire archive into a separate database and
projection. Its first 5% also pauses safely. It compares complete source/case
receipts and every field of every paired response, including excluded and
invalid cases. The final all-pair comparison has its own sealed 10,000-response
cursor. `verified=True` is returned only after the entire response census has
been compared. The three-case first-half exposure and 500-case later support
requirements are unchanged and remain downstream of complete source admission.

The native constructed proof spans 26,107 records, a response-side split across
the 5% boundary, quoted CSV newlines, duplicate/orphan/conflicting metadata,
1,000-fingerprint projection pause, separate-process replay, database tamper
refusal, immutable prior snapshots, and exact equality with the original full
source's cases and dispositions. No large human prefix was run by the builder.

The first counted pilot reports current database bytes and two-full-database
projection, plus measured ingestion CPU and extrapolation. Indexes, case parts,
immutable attempt copies and their copy/hash costs are explicitly additional;
the owner must size disk/output limits and remaining wall/CPU before continuation.
Do not treat a partial-source forecast as a forecast for every later phase.
All source preparation, failed attempts, source replay, case census and analysis
remain inside the original 20,000 CPU-second ID1 allocation and the 40,000-second
ID family cap. CPU only; no participant identifiers leave private ignored
storage, and no source demographic columns are loaded.
