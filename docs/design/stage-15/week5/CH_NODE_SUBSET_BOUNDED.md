# CH node textures: counted shared whole-player subset

**Prepared, not run or admitted.** The original
`week5_ch_batch_planner.node_texture_roster` implements the commissioned shared
subset, but only as an in-memory function without counted execute/verify
handlers. The separate `week5_ch_node_subset_bounded_v1` fills that operational
gap. It does not change either node-count texture, the 44-cell grid or the
original selection. All prior files remain immutable.

## DESIGN CHECK

The case is the fixed subset required by both 300,000- and 3,000,000-node
textures. The check is exact equality with the unchanged original function for
both the compressed roster and `SUBSET.json`, followed by independent complete
parent-roster replay. Constructed interleaved player rows distinguish original
within-player order from a resorted or position-sampled substitute. Both
capacity-constrained and all-player cases must match.

The smaller route is already the packet's at-most-25,000-position whole-player
subset. This adapter never reduces that declared cap to obtain a result,
splits a player to fill spare capacity, reallocates the shared 200,000 CPU
seconds, or reads an engine outcome. If no complete player fits, it retains the
original refusal. Resource interruptions preserve a checkpoint and charge all
work; they do not choose a new roster.

## Exact selection and output

Only the authenticated complete parent position roster is an input. Its
complete denominator is asserted from the qualified sample receipt, with the
original upper bound of 400,000 rows. Selection begins only after every parent
row has been read and that denominator matches. No actual roster or subset was
read or selected during this static build.

The adapter stores rows and per-player counts in a private SQLite database.
Players receive the exact original SHA-256 rank from seed 20261107 and the
original `CH-node-texture` namespace. The stable first-occurrence tie break of
the original Python sort is retained with the player's first source ordinal.
In that order, the adapter greedily includes a complete player if its entire
row count fits the remaining capacity; otherwise it skips that player and
continues. Each selected player's rows retain their parent-source order.

`PRIVATE_POSITIONS.jsonl.gz` keeps the original stable gzip member and JSON
serialization. `SUBSET.json` keeps the exact original fields and values. Both
node counts use that same completed subset and parent-roster binding, followed
by their separately authenticated score banks and complete collections. The
subset is texture-only; it never replaces the primary full roster.

## Checkpoints and verification

Completed parent rows and complete player-capacity decisions are saved every
100 units, at phase transitions and on owner yield. The SQLite database uses
full-synchronous rollback journaling, an eight-MiB page cache and disk-backed
temporary operations. A resumed execution accepts only the runtime's complete
authenticated output copy with unchanged source and semantic configuration.
Earlier attempt bytes remain intact.

An operational `max_new_draws` quantum names one parent row, complete player
decision or exported row. Both execution and independent verification honor it.
It is not a bootstrap draw, total-work fraction or CPU fraction. No automatic
first-five-percent claim or cost extrapolation is made.

Owner requests are checked between rows and player decisions and during input
hashing. For exact gzip bytes, an interrupted publication retains its partial
member and restarts publication from row zero in a new attempt. A full member
can finish at the exact selected-row quantum. Partial gzip work is charged and
never counted as an already published prefix.

Independent verification always begins with the complete parent source at
ordinal zero in a new workspace. It repeats every player decision and compares
both original output files byte-for-byte. Neither copied execution selection
nor copied verifier progress earns independent replay credit. Constructed
scope is bound by the producing plan and seal; the original `SUBSET.json`
schema is preserved, and that file alone does not establish source admission.

## Prepared qualification and remaining bounds

The separate `week5_ch_node_subset_fixture_v1` builds only literal constructed
rows. It prepares original-function parity, whole-player/order checks, actual
execute and verifier quanta, authenticated constructed-copy continuation,
owner interruption during gzip, exact final-row-quantum completion and full
fresh replay. Negative cases cover no fitting player, false parent count,
changed source pin, an excessive cap, damaged copied checkpoint and a
self-consistently resealed false subset. It has not been executed.

The constructed copy helper proves no native runtime behavior by itself.
Actual counted pause/continue/replay, complete checkpoint copying, native exits,
lease release, watcher delivery and cumulative accounting remain owner gates.
An interrupted aggregate fixture must restart in a fresh empty output.

Measure indivisible SQLite commits/queries, one at-most-four-MiB JSON decode,
one hash block, gzip finalization and atomic publication under the actual source
scale. The bounded row storage is not a measured peak-RAM or full-cost receipt.
The owner must bind complete source scope, full source-based parity, resource
limits, any required in-slot pilot and remaining CH/campaign room before start.
The original family ceiling and shared node-rescore allowance are unchanged.

This is the last identified missing CH0–CH6 execution component. The existing
numerical consumers, registered grid, source adapters and other bounded
successors now have implementations; their pending native qualifications and
source/cost admission are not additional scientific designs.
