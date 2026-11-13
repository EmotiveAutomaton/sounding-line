# SG1: complete session-game source and carried consumers

Prepared November 13, 2026 for owner review under the November 12 two-day
packet, sections 3A and 4. This is an unadmitted implementation, not a scientific
result or a claim that the design is committed. Original packet and all previous
CH source, selector, fixture, candidate and production bytes remain unchanged.

## DESIGN CHECK

The case is a complete selected player's game followed by another observed
game, an observed session break, or an unobserved month tail. Source clocks,
opponent identity, final position and tournament membership must be retained
without changing the old CH7 values. The packet's five hand-written games,
both player colours, a timeout, checkmate, unknown termination and an actual
malformed PGN exercise the case. A deliberately shared wrong execute/replay
projection must fail independent expected answers. A rating and a next action
do not identify SHAME, RAGE, pride or social standing.

The smaller route is an outcome-blind checkpoint at the first transaction
crossing 5% of the complete selected source-game count, inside this card's
counted attempt. It measures traversal/setup only; session construction and
whole-source verification remain charged. No prefix is called the population,
no clock availability selects players, and no failed parser silently removes a
previously admitted player-game. Existing source-level exclusions and parse
failure counts remain separately visible in the source index.

Relevant extractor, instrument and runtime lessons were reloaded. Independent
answers, complete source joins, unchanged inputs, failed-gate retention and
sealed new-attempt continuation are binding. The Round 13–15 handoffs were not
found locally at this preparation point; theory attribution follows the
self-contained controlling packet and is not represented as a full handoff read.

## Original population and one source traversal

The source is the complete April, May and June 2017 census's original 2% salted
player history sample. This is distinct from CH1's 10,000-player scoring roster.
No Stockfish score is required. All three original raw files, the completed
history database and original salt are pinned. Their checkpoint month, raw hash,
last ordinal and salt must agree before work. Input snapshots open with
`mode=ro&immutable=1`, query-only mode, and refusal of every WAL, SHM or journal
sidecar, including empty sidecars. Owner admission authenticates stopped,
checkpointed source ownership and complete native execution/replay receipts.

Raw PGN is streamed once per execute pass. Only originally selected source
ordinals are parsed, while the traversal still verifies each month's complete
raw-record count. The raw header, all retained own-move rows, first-clock array
and dispositions must equal the original payload. A raw parse or equality
failure is counted in a durable aggregate failure receipt and refuses completion;
it cannot silently change the previously valid source population. The original
game identity must equal SHA-256 of its raw-file pin and ordinal.

Every original CH7 column retains its exact name and value. In particular its
result is loss/draw/win = -1/0/1; the explicitly new `score` is 0/0.5/1. Unknown
results remain missing. Opponents and tournament IDs use the existing private
campaign salt, never URLs or queries containing those identities. Event text
is reduced to a tournament flag and salted ID. Unknown Termination strings
remain private as found, with an aggregate unknown count.

Opponent clocks, final material and mate are calculated while both sides' move
rows remain in memory. Material uses 1/3/3/5/9; the last move is replayed from
its stored pre-move FEN. First-move choices are UCI; Black also carries White's
opening move. Original CH7 own-move timing dictionaries are unchanged.

## Duration and session qualification

Duration is a clock-based estimate, not wall-clock truth. It sums successive
same-side clock differences plus increment, beginning with the second move on
each side. Each first clock is the observed initial bank; its difference from
nominal initial time is not counted as thinking, since that would charge a
berserk reduction as elapsed time. The two first-move latencies are unmeasured.
Missing or negative clocks and an increment control with a subinitial first
clock make duration missing with an explicit reason. For a decisive Time
forfeit, the losing side's last recorded clock is added. This definition is
submitted for owner review before admission; it does not change CH6's older
direct-end/start-gap fallback or CH7's start-gap session definition.

Within each player/control/month, consecutive starts less than 1,800 seconds
apart form a session; ties use the old stable game-ID order. The final observed
game is censored with missing STOP/REMATCH, never a voluntary stop. A subsequent
game after a session break gives STOP true and REMATCH false. Any absolute
rating change above 25 flags the entire session. Missing starts retain source
rows and explicit missing session fields. The complete player is the atomic
session-finalization unit; its maximum memory and latency require measurement.

SG1.v records 20 fixed bins of first-clock/initial on [0,1], with the last bin
including 1, separately for zero-increment tournament and other games. Missing,
out-of-range and exact [0.45,0.55] counts are explicit. BERSERK is a candidate
flag only. The two-mode criterion and non-tournament rate below 0.2% require
owner review of this full histogram; CH10 cannot use the flag before that
admission. Nothing else depends on that flag passing.

The official [arena help](https://lichess.org/tournament/help), read November
13, confirms halved clock, cancelled increment, extra point, unavailable zero
initial-time berserk, and doubled scoring after two wins. It also requires seven
moves for a berserk bonus. These rules qualify the inferred flag; they do not
authenticate it in these historical game records. The public database is
released under CC0 ([database](https://database.lichess.org/)).

## Complete replay, bounded work and accounting

The output is one private SQLite player-history table, with exact original CH7
fields plus SG1 fields and chronological session labels. Source writes commit
every 100 selected games; session writes commit each complete player. Only the
runtime's fully hashed new-attempt copied checkpoint may resume. Owner requests
are checked during file hashing, every 100 raw records and between players.
Decompression to a resumed raw ordinal is repeated and fully charged.

Verification traverses all three raw files afresh, recomputes every original
and added field, compares the complete table and refuses extra/missing rows.
It then reconstructs every player's sessions from the already raw-verified
columns, reproduces counts and histogram, and hashes the full output. It does
not create a second complete output database. A verification interruption
restarts from zero; no copied execution prefix receives independent credit.
Raw verification is not claimed to be a second independent parser: independent
hand-written fixture truth is the guard against common parser defects.

SG1 adds 40,000 CPU-seconds beyond CH7's 60,000 envelope. All setup, fixture,
traversal, failed work, repeated decompression and fresh replay remain charged
to CH and the campaign. The first proposed source attempt uses a 7,200-CPU
ceiling and the selected-row pilot boundary; full cost is unmeasured. Candidate
output cap is 8 GiB and peak memory 2 GiB, both provisional bounds requiring
actual measurement with current floors. Preserve all old archives and outputs.

## Carried CH6 and CH7

The separate carried adapter binds SG1's sealed complete table and pins native
completion and replay receipts. It uses immutable source access for every read.
CH6's original stopping mathematics, thresholds, resampling and source timing
fallback remain untouched. CH7's original equations, full-history null and all
2,000/20 draws remain untouched. Original CH7-column parity and constructed
consumer equivalence qualify only the interface. Complete numerical review,
full native qualification, actual cost/memory and owner admission remain gates;
the source repair alone never clears them.

## Forecast split correction for subsequent cards

The original source function selects `int(player[:16],16) < 0.02 * 2**64`.
Consequently every selected history key begins with 0. The packet's original
first-digit 0/1/2 calibration rule would allocate every player to calibration
and leave no analysis population. The curator explicitly answered: “Use a
separate fixed hash (recommended)”. The frozen successor split is SHA-256 of
`SG1-forecast|20261112|` plus the existing salted key: first hex 0/1/2 calibrates,
all others analyze. No new identity, sample or raw-source change is introduced.
The supplied packet remains verbatim. CH6 and CH7 do not use this split.

Source outputs carry run tags and no scientific verdict. All CH8–CH12 records
will state that a public game rating is not standing in a room. Final-packet,
activation and full internal write-through duties remain the owner's.
