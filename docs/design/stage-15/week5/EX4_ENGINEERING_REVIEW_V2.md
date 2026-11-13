# EX4 continuation and bundle-record correction

Prospective engineering successor, November 11, 2026. The original
`EX4_BACK_HALF.md`, `week5_ex4`, `week5_ex4_words`, original fixture and original
tests remain immutable. This note does not admit a corpus run or an export copy.
The source, nullable timing and surviving-word conventions in the original
design still require the owner's mapping review.

## DESIGN CHECK

Packet EX4/Q/T requires an export of the exact replayed final essay, typed-word
offsets and stop labels, source exclusions, attribution and a local-only handoff.
The original extractor distinguishes UTF-16 edit coordinates from Unicode
code-point output spans, preserves moved origins and never invents a pause for
an unsupported word. This successor does not change those definitions, the
2-second threshold, the essay's supported-pause 80th percentile, row order,
writer-ID prohibition or source denominator.

The original exporter has three concrete engineering gaps:

1. Its existence-only yield check treats the exact predecessor request copied
   into every new attempt as a new request. A source prefix can therefore remain
   paused forever even though its complete checkpoint was authenticated.
2. The generic local checkpoint seal is sufficient for same-directory resumption
   without proving that a new runtime attempt copied those bytes. It also does
   not distinguish an execution cache from a prior native verifier prefix.
3. The bundle README points to count files but does not itself give the counts
   and source ledger row required by the packet's export preamble.

`week5_ex4_v2` preserves the original computation and supplies isolated repairs.
No shared runtime, checkpoint primitive, source parser or original design is
edited. Its source identity binds the successor's bytes, so an old-module
checkpoint cannot silently cross into this version.

## Native continuation boundary

A saved execution or independent-replay checkpoint requires the new attempt's
`RESUMED_FROM.json`, the exact module, a pinned predecessor `PAUSED.json`, and
matching copied hashes for the checkpoint, its seal and every retained complete
session projection. The runtime still owns predecessor native-exit, owner,
source/config/pin equality and full-copy validation. These child checks do not
replace those runtime checks.

The checkpoint includes its operation. Execution values cannot count as an
independent-verification prefix. Reusing a saved verifier prefix additionally
requires the predecessor pause to name `paused_operation=verify`. The prefix
already reconstructed the original records in that independent native operation;
no executed-session projection is relabelled as verification. All remaining
records are replayed and every complete bundle byte and aggregate must match.

An owner request is current unless its exact bytes match the request entry in
the runtime's copied manifest. Both the execution output and the independent
replay subtree are checked. A changed request interrupts again. A copied request
is preserved as evidence, not deleted to resume.

Complete sessions remain the work unit. The first source boundary is
`ceil(source sessions / 20)`, namely 250 of the fixed 4,992-session roster. The
receipt's `first_fraction` names the 0.05 target; its actual completed and total
counts define the achieved fraction. In a tiny constructed two-session case the
first complete unit is necessarily one of two, not five percent of work or CPU.
The same full-source replay and all retries continue to charge the 60,000 CPU-
second EX4 ceiling and 100,000 CPU-second EX family envelope.

## Bundle record

The README now contains actual original-session count, session dispositions,
word/provenance/timing counts and the source ledger identifier
`OPS-S15-W5-KLICKE-SOURCE-COMPLETE-20261107`, pointing to
`WEEK5/KLICKE_SOURCE_COMPLETE.md`. The existing authorship acknowledgement,
CC BY 4.0 attribution, derivative notice, exact-text/offset definition and
local-only restriction remain. No writer identifier is introduced.

## Qualification and limits

The focused run passed the original nine checks and thirteen successor checks
serially, using 2.125 native Job CPU seconds and 3.068 seconds wall time. It
retains exact before/after source pins. Checks include exact Unicode spans, moves, deleted
starts, bulk/mixed provenance, timing ties, parse/integrity separation, full
aggregate replay, unchanged earlier outputs, actual README counts, stale/new
request distinction, checkpoint-mutation refusal, wrong-operation refusal and
an explicit reproduction of the original copied-request failure.

The constructed source-authentication and native resume receipts are deliberately
substituted in this small handler fixture. Real source replay/export computation
and the session state machine execute, but the tests are not a claim of an actual
whole-corpus or native campaign qualification. No real source session, raw archive,
model, materialization or destination copy is loaded or performed by these checks.

Before production the owner must review this successor and the original mapping,
bind a committed design and actual source/runtime closure, authenticate the
completed original intake, and admit the counted 250-session prefix. Whole-source
authentication and the largest session are indivisible operations; their latency
and peak memory are not priced by the tiny fixture. The 2-GiB declared peak must
be measured, and all source setup plus complete execution and independent replay
must fit the remaining card/family/campaign limits and current resource floors.
Preserve every parse exclusion and unsupported pause. Only the complete
independently verified bundle may later enter the separate owner-controlled
materialization and named ToMpathy copy procedure.
