# CH0/CH1 three-month frame, November 11 amendment

Prospective implementation of `PACKET_BACK_HALF.md` R2, N and O. This note is
prepared for owner review; it does not assert admission, execution or commitment.
The November 11 theory handoff was read in full. This source construction does
not test Standing, which the handoff explicitly leaves under review.

## DESIGN CHECK

LESSONS §§2–5: construct the population before clocks, engine scores or model
outcomes; preserve identifiers privately; authenticate complete source and replay;
distinguish an operational row pilot from a five-percent CPU claim. Known-answer
fixtures must include repeated players across months, quota ties, insufficient
strata, incomplete sources and forbidden fourth months. Full raw-source replay
must reproduce selected players, positions, order and missingness.

## First admission: unchanged bounded merge

Use the already qualified `week5_ch_merge_bounded` implementation over exactly
the independently completed April, May and June 2017 census databases. No new
merge algorithm is needed. The private candidate binds each database through its
existing terminal receipt; those pins were read from metadata, not remeasured by
this builder. Runtime authenticates the actual files before work.

The source counts are 11,348,506, 11,693,919 and 11,512,600 games. The merge retains
all five scientific tables and their original schemas, values and primary-key
order, together with the common salt. It refuses overlapping or partial months.
Verification compares every source row to the merged database, from source row
zero, without making a second full merged database. The completed native
merge qualification is `ch-pipeline-counted-v2-merge-complete`; the original
execute and independent-verification pilot qualifications remain applicable.

The first real merge attempt stops after the first transaction crossing five
percent of the known scientific-table row total, using `max_new_draws`. This is
a source-row boundary; file authentication and setup remain charged. A later
owner-reviewed continuation is needed for the complete merge. The independent
verifier still starts at row zero. No source prefix may define the sample.

The owner must reconcile all CH charges and measured available storage, reserve
the 20-GiB floor, and inspect the merged size at the next wake. The existing
native fixture is not a measured real-source cost or disk forecast. If the
merge cannot stay above the floor, stop chess. Do not revive July or substitute
another month. All July archives, pilots, conversion evidence and costs remain.

## R2 roster and complete raw-source sample

The isolated `week5_ch_backhalf_roster_v1` selector retains the original
eligibility: at least 20 games in a month/time-control/rating-band cell. It
retains the original salted deterministic eligibility rank to assign every
eligible player to exactly one eligible cell across all three months and time
controls. Consequently month proportions use the unique assigned eligible
players in each time control; overlapping appearances cannot be counted twice.
Both pre-assignment appearances and unique assigned denominators are recorded.

Allocate 7,000 blitz and 1,000 each bullet, rapid and classical players. Within
each time control allocate by month proportion with integer largest remainder,
then within each month by rating-band proportion with the same method. Ties use
lexicographic month/band order; within cells retain the original player sample
hash. If eligible unique support is below a quota, retain all support and expose
the shortfall; do not borrow players or time controls. Final player order remains
sorted salted player key. Production permits only the declared 10,000 target;
a reduced target is legal only in a marked constructed fixture.

The isolated raw-sample adapter substitutes this selector into the qualified
transactional full-source sampler in one process and restores its original
callable on exit. It keeps original game/move hashes, ten games, four moves per
game, round-robin maximum 40 positions, all availability exclusions and source
record denominators. It scans all three immutable raw sources. Independent
verification reconstructs all candidates from source ordinal zero.

## Downstream boundary

CH1 uses the original fixed-node Stockfish score definitions and two single-thread
engines. A separate queue design will bind N's complete execute/replay sub-batches
and twelve-hour queue boundary. Policy temperature is fitted on April only and
applied to May/June. April is excluded from every policy-entropy analysis cell;
its other outcomes remain available. The 2017-versus-2026 CH2/CH6 comparisons are
withdrawn. All other original grid controls and support fallbacks remain.

No first scientific claim, CH7 launch, new source scope or sample choice based on
unfinished outcomes is authorized by this preparation. Source, roster, queue and
collection native proofs, actual accounting and owner review are separate gates.
