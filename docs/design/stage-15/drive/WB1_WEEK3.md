# WB1: repeated writing-process pieces beyond first-order grammar

Authority: the October 25 Week 3 packet, family WB, first-dispatch rank 2.
This is an implementation card. It contains no corpus score or scientific verdict.

**Hypothesis.** Writers reuse short process sequences more often than their
session's first-order transition statistics predict, and those pieces recur in
held-out writers.

**METHOD.** Reconstruct the complete canonical P2 session population from its
authenticated original raw logs. Split writers once, stratified by session count.
Discover length-three-through-six sequences on discovery writers against 200
exact-transition conditional surrogates per session. Measure held-out event
coverage with a whole-writer interval and repeat with local time-third controls.
Reconstruct each discovered occurrence's four requested future effects from the
original logs; fit up to ten effect classes on discovery writers only.

## DESIGN CHECK

LESSONS sections 3–5, CONTROLS sections 1–7 and READER_HEURISTICS sections 3/7,
including their afterwords, were reread October 25. A first-order deterministic
chain cannot exceed its unchanged null counts. Higher-order planted sequences
can exceed those counts. Both first/last states, exact transition multiplicities
and length are retained; violation invalidates the instrument. An artificial
edit-of-accepted-text sequence may be discovered but cannot enter the primary,
because its acceptance link reaches up to sixty seconds into the past. Discovery
never selects from held-out writers. The positive routing gate requires at least
twenty primary-eligible pieces and both whole-session and time-third coverage
intervals strictly above zero. All other outcomes route to the separately frozen
WB1b; a failed WB1b routes to single events.

## Frozen implementation choices

- Population: all 1,399 completed P2 sessions; no outcome-based subset.
- Split: sort writers by session count, break ties using seed 20261026, pair
  adjacent writers, and randomly place one of each pair on each side. An odd
  singleton goes to the smaller side. All downstream discovery choices reuse it.
- Units are recorded text changes, not inferred physical keypresses. A typing
  burst aggregates adjacent insertions with gaps strictly below two seconds;
  an explicit pause represents a gap of at least two seconds between meaningful
  changes/menu actions. Menu events interrupt a burst. Deletion runs aggregate
  adjacent deletions. Length is Unicode codepoints; time is seconds.
- A revision move marks an edit away from the document end when the edit cursor
  changes from the prior edit's endpoint. The terminal Quill newline is excluded
  from the end position. Repeated adjacent editing at that cursor is one move.
- A delta with multiple actions orders revision, deletion, insertion, then an
  accepted-text-edit annotation. Every symbol retains its original ordinals.
  P2 supplies acceptance/ignore resolution and censor flags. Dismissed menus and
  canonical ignores both mean closed without a choice; censor status remains
  separate. Accepted-text edits use P2's origin links and the inclusive sixty-
  second boundary. Neither actual reading nor awareness is inferred.
- Burst/pause/deletion terciles use the full corpus as the packet requests.
  Equal lengths always occupy one bin; empty tied bins remain visible. WB1b uses
  the frozen median cuts and drops revision-move symbols.
- Conditional surrogates use a Wilson loop-erased last-exit tree rooted at the
  fixed final state, with independently shuffled remaining outgoing edges. This
  samples the uniform Euler-trail law conditional on exact transition counts.
  Merely randomizing a Hierholzer traversal would not establish that law.
- Sensitivity divides each full session's recorded elapsed time into three equal
  intervals. It preserves each segment's first/last states, so cross-third
  transitions are also unchanged. It does not split by outcome-dependent drift.
- Candidates need at least thirty overlapping occurrences and ten discovery
  writers. Counts must be at least twice their null mean and exceed every one of
  the 200 draw totals. Pairs never qualify.
- Primary coverage places globally longest matches first, then earlier start
  position, with lexical ties deterministic. Events cannot be double covered.
  The contrast is event weighted; all of a real writer's sessions are resampled
  together in 2,000 draws. Both coverage conditions must pass.
- Occurrence effects retain overlapping occurrences, independently of the
  nonoverlapping coverage tokenization. A truncated sixty-second window is
  censored, not a zero effect. Accepted retention is undefined when no accepted
  characters arrive in that window. All missing support is reported.
- Net characters count all-origin Unicode document change. Sentence completion
  is a punctuation-bounded proxy. Retention uses original accepted UTF-16 units
  and final surviving provenance. Prompt similarity uses the exact CONTENT_V2
  MiniLM revision, first 254 prompt tokens and last 254 document-context tokens;
  every truncation is recorded. No raw text leaves the local process.
- Effect consistency is held-out variance explained by piece identity, compared
  with 200 piece-label shuffles within writer. It is descriptive grouping, not
  out-of-sample effect prediction. Classes use discovery piece mean vectors only;
  per-effect missing support and constant dimensions remain explicit.

## Components and admission

1. `week3_pieces_input` was the original source-only preparation handler. Its
   first corpus attempt stopped on epoch-clock cancellation before producing a
   session. Preserve that original source and failure.
2. `week3_pieces_input_recovery` changes only elapsed-clock operation order to
   match P2: subtract epoch milliseconds before dividing by 1,000. It keeps the
   original tolerance and definitions. This is engineering healing attempt 1.
3. `week3_pieces_stats` provides the controlled kernels;
   `week3_pieces_coverage` authenticates completed inputs and regenerates the
   complete conditional reference banks in fresh verification.
4. `week3_pieces_effects` reconstructs original occurrence effects and labels.
   Coverage completion by itself does not license downstream dispatch. A whole
   card needs its complete effects receipt and original sources.

The preparation tests cover independent native replay, Unicode, exact boundary
values, split stability, both timing-interval endpoints and mutation refusal.
The recovery tests cover large epoch clocks, changed P2 clocks and full serialized
fresh-process reconstruction. Kernel tests cover an enumerated conditional
uniformity calibration, exact counts, time thirds, future-linked exclusions,
nonoverlap and positive/null/negative coverage directions. The coverage handler
passes serialized execution, fresh replay, input/reference mutation and yield
checks. Four effects checks cover exact replay, known future windows, held-out
consistency references, discovery-only grouping, and a fresh native verifier.
The cost probe has two checks; the combined coverage/effects/pilot run passes
ten checks. These are constructed validation, not a corpus scientific result.

`week3_pieces_pilot` measures twenty complete reference draws on both halves and
both null scopes. Its test coverage uses every candidate as an upper-work
approximation. The projection includes full coverage replay, but excludes the
effects/encoder, final bootstrap overhead, and prior charges. The owner must add
those costs before admitting the complete card.

Total parent-card ceiling: three CPU-hours including preparation, reference
generation, occurrence effects and fresh verification. The counted owner must
measure the first tenth and apply its unchanged forecast/resource policy; this
document supplies no new cap or retry authority. Source checkpoints, failed
attempts and original charge remain in the cumulative account.
