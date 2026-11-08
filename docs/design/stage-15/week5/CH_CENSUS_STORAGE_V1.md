# Exact history storage for the complete CH census

**DESIGN CHECK — 2026-11-08.** Read LESSONS sections 2–5, especially immutable
receipts, complete native qualification and the distinction between admission
ceilings and actual measurements. This is a representation-only successor to
CH0 and its already commissioned downstream pipeline. The scientific question,
full month population, source pins, salt, sampling hashes, clocks, models,
grids, resamples and original outputs remain unchanged. No result or participant
row was inspected while preparing this successor.

**The case and its check.** July's completed first 4,464,422 source records have
an independently rebuilt database of the same logical contents. Each database
occupies about 3.837841 GiB. Scaling both copies to 89,288,421 records gives
about 153.51 GiB before WAL, retained predecessors, other jobs and downstream
outputs. The reported 161 GiB free space with a 20 GiB floor cannot safely hold
that incremental footprint. This is an environmental storage constraint, not
permission to shrink the source population. All earlier CPU charges remain.

**The smaller route.** Encode only the existing history JSON strings with
lossless zlib level 1, retaining exact decoded text and every other database
value. Admit only after actual ratio, peak disk, CPU and memory measurements
support complete execution, complete fresh replay and downstream consumers.
If that still does not fit, hold this representation for owner review; do not
choose an unregistered subset or assume compression always saves enough space.

## Why this representation

Transparent NTFS compression was considered first because it could preserve
all logical SQLite bytes. Microsoft's fetched `FSCTL_SET_COMPRESSION` reference
states support up to 30 GB uncompressed per file, below the projected single
July database. The successor therefore does not use it. Read level: complete
API page, including remarks and size limit; not a dataset query. [Microsoft API
reference](https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ni-winioctl-fsctl_set_compression).

`week5_ch_storage_v1.py` explicitly encodes only `histories.payload`. The
original schema and primary keys stay unchanged; SQLite's payload storage
class is BLOB when compression saves space, and TEXT otherwise. The BLOB
contains a version marker, original UTF-8 length, SHA-256 and zlib stream.
Decoding requires exact length and checksum, a completed stream, no trailing
stream and valid UTF-8. A 64 MiB indivisible payload bound fails explicitly;
it never drops or truncates a row. This bound is an operational refusal and
must be checked against the actual maximum before full admission.

The SQLite application ID identifies this representation. A compressed file
is not advertised as directly interchangeable with an arbitrary reader.
Named consumer adapters restore text through their connection row factory.
Unadapted JSON parsing of compressed BLOBs fails. Payload predicates, SQL JSON
functions, custom cursors, aliases that hide payload columns, unreviewed writes,
and attached-database INSERT-SELECT are outside the qualified contract.
Current commissioned routes use original primary keys and text decoding in
Python; none uses a payload predicate or payload ordering to define the sample.

The adapter changes only named modules' `sqlite3` namespace inside the one
native child and restores it in `finally`. It does not edit frozen sources or
globally replace the Python sqlite module. External paths are allowlisted and
read-only; writable files must resolve beneath the admitted output. A raw
original database is never opened for writing. New output is marked and uses
the original WAL/FULL transaction policy. Every commit and each 100 connection
operations check the unchanged 20 GiB floor; the supervisor's ordinary resource
guard also remains required. Refusal retains all files and costs.

## Prefix conversion and full continuation

`week5_ch_storage_migrate_v1.py` copies the six complete original logical
tables to a fresh marked database. It reads the old standalone checkpoint
read-only, authenticates its SHA-256, validates quick-check and the single
month ordinal/denominator, and preserves the original `complete` flag. A pilot
prefix remains an incomplete population. Source settings and all other values
are unchanged. Operational conversion cursors occupy a separate table.

Every row commits with its table/key cursor at least every 100 rows. A positive
`max_new_draws` is an exact new logical-row boundary in execution and an exact
from-zero logical-row boundary in verification. Taking `ceil(total_rows/20)`
therefore stops at the first 5% of conversion rows, before the next row is
written or compared. It is not 5% of raw games, compression work or CPU time:
the table order reaches history strings late. A whole converted pilot is
needed to measure history compression. The handler does not claim otherwise.
Full conversion independently compares every value and schema against the old
database. That proves representation parity, not raw-source correctness.

Continuation requires the current native runtime's authenticated full output
copy into a new attempt. The migration cursor is checked against the unchanged
input/configuration binding. Whole-file authentication, SQLite quick-check,
COUNT queries, one large row and final checkpoint/truncate remain indivisible
units. Their peak memory and worst yield latency require measured qualification.
The fresh verifier always starts from source-table row zero; a copied verifier
prefix receives no independent credit.

After completed, verified conversion, `week5_ch_census_storage_v1.py` accepts
the marked prefix under the original `resume_frame` input. The frozen census
copies it into another fresh attempt and resumes after the exact saved source
ordinal. Original source parsing, eligibility, book counts, fixed 2% history
selection and serialization all execute unchanged. This extra copy belongs
in the peak forecast and remains preserved; conversion is not performed in
place. A raw unmarked prefix is refused by this handler.

The existing `week5_ch_census_replay.py` still rebuilds a separate complete
database from source ordinal zero, deliberately excluding `resume_frame`.
Both production and independent replay encode their own history values. After
the full raw parse, comparison checks every original table schema and every
logical value, ordered by its original unique key. One row per side bounds
comparison memory. Physical compressed bytes need not match across library
versions; exact original decoded strings and all numeric values must match.
SOURCE counts are unchanged. A rehashed falsified prefix must fail fresh replay.

Original verifier interruption semantics are retained: no trusted partial
verifier resume. Its existing independent database makes repeat verification
in the same output refuse. A new owner-reviewed attempt must retain the old
partial replay and allocate another fresh independent database. No file deletion
or automatic omission from sealed copies is implemented here. Retained old
attempts and a possible new replay copy must fit before any such restart.

## Exact consumer integration

`week5_ch_storage_consumers_v1.py` dispatches the existing bounded handlers by
phase: `merge`, `sample`, or `history_index`. It changes their connections only:

- Merge reads all completed month tables and keeps merged histories encoded.
  Complete source denominators, salts, overlap refusal and full value replay
  remain those of `week5_ch_merge_bounded.py`.
- Sample uses the complete frame and the original raw sources. Selected-player
  JSON, positions gzip, row order, every value and SOURCE counts must be byte
  identical to the uncompressed reference.
- History projection decodes the same full histories into the unchanged
  ordinary-text player-history table. Every projected value and contents hash
  must match the reference. Original CH4/CH6 analysis can read that projection
  directly; book counts used by CH3 remain ordinary unchanged SQLite values.

Only physical input hashes/provenance and operational seals change when source
representation changes. The fixture requires those source hashes to differ
where appropriate; it never forges old provenance to force receipt equality.
Old files and receipts remain unchanged. No new score, fit or model is added.

## Prepared qualification; nothing in this note has run

The counted `week5_ch_storage_fixture_v1.py` handler constructs 48 known games
using the already frozen parser fixture, with a 24-game prefix and authenticated
history support. Execution prepares plain and packed full censuses, a deliberately
falsified-and-rehashed prefix, and complete plain/packed merge, sample and history
projection routes. Its separate native verify handler recomputes original raw
references and both consumer paths. Checks cover exact Unicode/NUL/short-text
round trips, corrupt/truncated/trailing/oversize envelopes, unknown format,
unreviewed mutation, disk-floor refusal, outside-output writes, original-file
write refusal, unadapted-reader refusal, complete logical parity and false-prefix
replay refusal. It runs no engine or scientific fit.

The owner must additionally qualify actual pause/copy/continuation through the
current counted runtime, one stage at a time, using the fixture's saved original
prefix and the migration handler. Start with exactly `ceil(total_rows/20)` new
rows and require a genuine PAUSED terminal. Copy the entire sealed output into
a new attempt and finish conversion. From its complete sealed copy exercise
the verifier with the same 5% row quantum: require a genuine verification pause,
no verified completion and zero reused verifier credit. A final new attempt
must verify every source row from zero. All native exits, whole output-copy
hashes, old-byte preservation, lease releases and watcher compatibility are
part of admission; an in-process copy record is not that proof. This repeat
verification is tiny constructed qualification and all its CPU is charged.

The census owner-yield and recovery fixture from the unchanged replay handler
must also run with compressed outputs: incomplete production checkpoint,
new-attempt suffix continuation, a requested fresh-verifier pause, and final
full fresh replay with no prefix trust. The current wrapper inherits the old
verifier's restart-only scratch contract; owner preparation must use a new
output and the retained execution database as its authenticated resume input.
It must not copy the old verifier scratch into the path the fresh verifier
requires. The old attempt remains intact and charged. This is a source
continuation using a pinned database input, not a partial sealed-output copy.

## Remaining measured gates

No compression ratio, CPU cost or memory improvement is claimed. Before full
July continuation, measure the complete retained pilot's conversion plus full
value verification, its largest payload, physical database/WAL peaks and full
copy cost. Then measure actual source suffix/replay rates under this codec in
the counted slot. The existing source pilot implies roughly 541,000 CPU seconds
for remaining original execution plus whole fresh replay before conversion,
extra hashes, copies and codec overhead; 500,000 is not a safe refreshed bound.
Retain every predecessor, pilot, failed attempt and new qualification charge
under CH's 2,500,000 CPU-second family ceiling and the campaign total.

The admission forecast must include old retained files already on disk,
conversion output, its continuation copy, full production, full independent
replay, possible retained interrupted verifier, SQLite WAL/SHM and journal
peaks, later full merged frame, player-history projection and concurrent jobs.
Projecting only the two July final files is insufficient. Require measured
margin above the 20 GiB floor; a steady-state compression ratio is not a peak
proof. Commit the reviewed design and pass complete counted native qualification
before any human-source compression or continuation. All 44 frozen CH cells
remain dependency-, qualification- and cost-gated.
