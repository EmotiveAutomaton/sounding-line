# S2 revision source preflight

This implements the commissioned S2 source preparation after R2. It computes
no flow-versus-hesitation contrast, timing label, fitted model or scientific gate.
It does not change the packet's sentence unit, controls or support floor.

DESIGN CHECK: LESSONS sections 2-5 reread November 3. Source instruments must
preserve Unicode coordinates, insertion provenance and full populations. Under
either scientific direction, malformed deltas, backwards clocks or disagreement
with the authenticated R2 final text/provenance refuse the source. Known edits
inside earlier typed sentences must be found; leading-edge continuations,
prompt-only sentences and API edits must not become typed non-local revisions.
No repeated-character text matching or final-survival filter defines a target.

Replay every raw edit in the 1,399-session primary population, keeping per-unit
typed insertion ordinals. Authenticate the full 1,445-session R2 index; require
all primary sessions and retain the 46 archive-only sessions as a separate count.
Each processed session must match its R2 exact replay and final provenance tags.

For every user text-changing event, inspect its actual delta anchors in the
pre-edit document. Retains consume old UTF-16 positions; insertions do not.
Deletion overlaps are half-open. An insertion touches a sentence only strictly
inside its nonspace extent, so extending the leading edge is not a revision of
that sentence. Sentence boundaries use the existing punctuation/newline rule.
Record each affected sentence's pre-edit bounds, text, nonspace typed fraction,
insertion ordinals, completeness, distance in sentence indices from the final
nonempty sentence, and edit extent. A sentence ending at a documented boundary
or terminal punctuation is complete; a trailing fragment is explicitly separate.
Retain both the recorded cursor and delta-based position; this stage uses the
delta as the unambiguous location of the text change, and asserts no mouse or
keyboard action. A delta with several operations retains every affected sentence.
An event is counted once even when it affects several sentences.

The candidate count is an **upper-bound source census**: a complete, wholly
writer-typed pre-edit sentence is changed at least one sentence behind the current
leading edge. It does not yet establish a first-production denominator, valid
onset timing, future revision linkage or the packet's final analytical support.
These source counts cannot license S2, T2 or S3. All discarded/mixed/API cases
remain counted. Later deletions cannot remove an earlier recorded event.

**Case and check.** Exact constructed cases cover typed versus prompt/API text,
interior insertions, leading-edge continuation, multi-sentence deletion, shifts,
surrogate pairs, incomplete tails, immutable snapshots and corrupted replay.
The native constructed source precedes a 140-session timing probe and the full
primary source. Every run independently reconstructs the complete output.

**Smaller route.** Source construction, tests, native checks and costing charge
the original S2 3,600 CPU-second allowance. Reserve at least 1,800 seconds for
the analytical consumer. Admit the full source only from measured execute-plus-
replay cost, using a 1.5 source forecast factor. If it cannot fit, hold that full
source and prepare the packet's separately frozen whole-writer sample before
further source execution; do not choose a prefix as a scientific population.
The timing prefix produces cost/source diagnostics only. One counted CPU slot,
one numerical thread, 3 GiB projected peak memory and 512 MiB output cap.
