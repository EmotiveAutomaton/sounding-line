# CH1 checkpointed scoring queue and April-only collection

Prospective November 11 preparation under back-half amendments N and R2.
Prepared for owner review; no claim of commitment, native qualification or
scientific admission. The unchanged scorer, earlier fixtures and failed attempts
remain intact. The three-month frame is specified in `CH_BACK_HALF_FRAME.md`.

## DESIGN CHECK

LESSONS §§2–5: every selected position retains its complete source row, original
order, fixed node count and original scoring code. A compute checkpoint cannot
stand in for independent verification. Native identities, exit codes, closed
Windows Jobs and actual all-descendant CPU must accompany each replayed unit.
Null and positive boards use identical engine settings. Known-answer controls
include one legal move and a unique mate in one. Missing/changed score files,
roster gaps, duplicate intervals, changed engine pins and copied unverified
prefixes refuse. The complete constructed native chain is still required.

## Queue unit and accounting

`week5_ch_queue_backhalf_v1` is one counted runtime handler. It reads the frozen
roster sequentially, buffering at most 64 positions. Each unit freezes a private
gzip slice and the exact original full-roster hash/global interval. It runs the
unchanged `week5_ch_engine_bounded` scorer on the slice, with two single-thread
Stockfish processes, 64 MiB hash each, fixed 1,000,000 nodes (the predeclared
300,000/3,000,000 node textures remain distinct input plans).

Each unit has a separately started native execute child followed by a separately
started native replay child. Replay loads the same original score/engine/input
pins and recomputes every scored position from its first row, comparing full
values. Both children are held in nested kill-on-close Windows Jobs inside the
already counted queue Job. Their exact Job usage includes exited descendants;
the outer queue Job remains the accounting authority and is charged once.
Nested receipts are diagnostic subdivisions, never added to the outer charge.
All interrupted invocation receipts and charges remain inside the unit.

The scorer's ordinary 600-second boundary may close a shorter prefix of the
64-position slice. Only that prefix enters the seal; its unused tail remains in
the sequential buffer for the next unit. No position is dropped or reselected.
The original scorer resets Stockfish for every position, so slicing changes no
score state. Full source ordinals are rechecked by the final verifier.

A unit closes only after exact independent replay, native exit and descendant
accounting. Its immutable seal hashes every score, local input, configuration,
native identity, environment, invocation result, usage receipt and log. The
global cursor advances only after this seal. An interrupted execution resumes
its saved prefix; an interrupted unclosed replay starts that unit from row zero.
Previously closed units retain their actual independent replay evidence.

## Time, pause and final verification

The nested execute supervisor requests yield at 650 seconds and the replay
supervisor at 1,000 seconds, with at most 55 seconds of cooperative grace each.
A timeout closes only its contained descendants, preserves every artifact and
fails for owner review; it does not automatically retry forever. Their combined
worst-case supervised duration is 1,760 seconds. Qualification must measure
the remaining unit input/seal overhead within the forty-second margin, proving
the complete indivisible checkpoint unit is at most 30 minutes. That margin
is a proposed bound, not an existing measurement.

A queue reserves at least 30 minutes for final authentication within its
12-hour outer wall cap. Its execute/replay queue setting is at most 41,400
seconds and no new unit begins within its final 1,800 seconds. Owner requests
are checked by the nested supervisor and both scorer directions; current
score-pair work has the existing 20-second engine transport timeout.
Only a new counted attempt with a complete runtime-authenticated output copy
can resume. Neither historical owner requests nor copied unclosed replay
progress become new admission or verification evidence.

Final runtime verification independently traverses original roster ordinals,
authenticates every closed native unit and checks exact contiguous interval
coverage, original engine/node bindings and all sealed bytes. It does not run a
second whole queue of Stockfish: every score already has a separate native
recomputation. This explicit queue verification protocol is the implementation
of amendment N's bounded complete checkpoints.

Final authentication checkpoints after each closed unit. On a new verified
runtime copy, only previously authenticated units may use the copier's complete
destination-hash manifest; all newly authenticated units are read fully. The
original full-roster row traversal is repeated. No copied in-progress score or
replay cursor receives independent-engine credit. A `max_new_draws` boundary
counts completed positions in closed units in execute and final verification.
Its first-five-percent marker is a position-roster fraction, not a CPU fraction.

`week5_ch_queue_manifest_v1` accepts only complete counted queues with final
native verification. All intervals together must cover the entire original
roster exactly once at one node setting. It emits the existing bounded collector
batch schema, retaining each native queue and unit seal. Partial queues are
useful checkpoints but are never a complete scientific population.

## April calibration and output parity

`week5_ch_collection_backhalf_v1` is an isolated copy of the bounded collector,
with only R2's calibration change. For each original rating band the same
optimizer, scalar summation order and support floor use April positions only.
May and June cannot influence their fitted temperature. April's fitted and
fixed-100 policy entropy fields are unavailable, so every policy-entropy
analysis excludes April; other April measurements remain. The 20-supported-
position floor, mating exclusion and descriptive fixed-temperature fallback
remain. All three months must be present in the source roster.

The collector still requires every expected score key exactly once and fully
recalculates the scientific gzip, temperature JSON and aggregate receipt from
the frozen source and score files. This post-score collection has its own
bounded source-row/fit pilot and native qualification gates; an initial roster
pilot is not whole-card cost evidence. A fit or gzip member interrupted in
progress restarts that bounded unit, as recorded in the prior collector design.

## Required proofs and remaining gates

The focused test file uses only constructed rows and mocked scorers; it proves
protocol logic, not native engines or Job containment. Run serially after the
owner grants the test token. The separate constructed fixture includes actual
original PGN parsing, all three censuses, original collector byte parity and
fresh full raw-source sampling replay. The independent list oracle checks the
new disk-backed proportional roster.

The actual native queue fixture uses eight legal boards from the previous
qualified engine fixture, now tagged across April/May/June. It has three
one-at-a-time counted attempts: execute pause after six closed positions,
continuation with an actual final-verifier pause after six positions, then
complete continuation. Required inspection: unchanged predecessor bytes;
exact scores/known answers; distinct execute/replay identities for each unit;
all native processes exited; all leases released; watcher terminal schema;
outer Job CPU at least the nested CPU subdivisions; no double charge. Preserve
any failed attempt before an isolated repair. There is no automatic launcher.

Before production: owner design/source review, committed-design binding under
the applicable admission policy, targeted checks, actual counted source and
queue fixtures, measured complete-unit overhead, actual sample/support/source
denominators, current CH/campaign charges, and the unchanged RAM/commit/disk
guards. The CH ceiling remains 2.5 million CPU seconds. The full 10,000-player
collection remains a >60,000-CPU workstream until measured otherwise and does
not inherit amendment Q's small-new-card shortcut. Six long queues at most may
occupy slots; the owner retains the two short-card/filler lanes.

July work and the two 2017-versus-2026 texture comparisons are withdrawn. Every
other original analysis grid and resampling control remains prospective. CH7
and subsequent analysis dispatch are separate owner restart assignments.
