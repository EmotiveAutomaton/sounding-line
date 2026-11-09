# Cooperative census merge, position sample and history index

This prospective adapter family preserves [CH_PIPELINE](CH_PIPELINE.md) and
[CH_ANALYSIS](CH_ANALYSIS.md). The running census and recovery modules stay
immutable. These preparations have not passed their native fixtures and do not
admit a human source, a partial census, scoring or any of the 44 analysis cells.

## DESIGN CHECK

LESSONS 2–5 apply: whole source denominators precede selection; transaction data
and cursors must commit together; native reentry must preserve saved bytes; a
copied prefix is not independent verification. Every source selector, emitted
position and history field must agree with the original implementation. Under
null and alternative clocks the same records and eligibility rules apply.
Changed sources, incomplete months, duplicate months, missing/extra rows and
salt disagreement refuse. A source gap is not replaced by a smaller sample.

## Merge adapter

`week5_ch_merge_bounded` accepts the original salt and month-frame input slots.
It requires complete, disjoint months and the common campaign salt. It copies
at most 1,000 rows per transaction, in original primary-key order. The current
source, table and last key commit in a private operational table in that same
database. This table is not a scientific field; the six original scientific
tables and their schemas remain exact. Keeping it after completion makes an
interruption between the last commit and final receipt safely recognizable.

The verifier restarts at the first source row and compares every original row
against the merged primary key, plus exact total row counts, schemas and salt
settings. It creates no second large database and gives no credit to an
execution or old verification cursor. This is content equality; physical
SQLite page layout is not an identity criterion. `SOURCE.json` stays identical
to the original merge receipt.

## Fixed sample adapter

`week5_ch_sample_bounded` retains the original `choose_players` function, its
strata, hash order, quotas, 20-game threshold and single-stratum assignment.
It requires the entire raw-source roster to match the complete merged census.
Selection is frozen before any move's availability or engine score is used.

The complete raw stream updates one private candidate list per chosen player.
Each list retains the original ten game hashes, stable order and four move
hashes per game; final round-robin emission preserves the original 40-move rule
and its short-game/missingness counts. Candidate changes, source ordinal and
counts commit together. A partial raw prefix never becomes a scientific sample.
Source-row transactions occur at most every 1,000 records; owner checks also
occur while skipping already parsed source ordinals.

The raw compressed stream must be decompressed through its earlier prefix on
continuation; there is no invented random access to a single Zstandard frame.
This overhead remains charged. Verification independently rebuilds all
candidates from raw ordinal zero. Only a copied private verification scratch
table is reset in the new attempt; the predecessor and executed sample remain
unchanged. Final selected-player JSON, position gzip bytes and counts must
match exactly, using the original serialization and fixed gzip header.

## History-index adapter

`week5_ch_history_index_bounded` preserves every original projected field and
canonical payload bytes. A source-game primary-key cursor commits together
with both players' projected rows, avoiding a half-game checkpoint. The index
uses the same scientific tables and settings, plus private operational state.
It can resume directly after its last source-game key without reparsing the
prior source prefix.

Verification rederives every projected player-game from source ordinal zero,
checks the exact key and payload, requires the total row count and original
settings, and recomputes the original content hash. No copied cursor receives
verification credit. Fingerprinting and final gzip emission check owner
requests; partial outputs remain unsealed until completed.

## Bounds and pending evidence

All three adapters use the existing counted runtime, sealed output-copy
continuation and top-level owner request. Only `max_new_draws`, interpreted as
new source rows at transactional boundaries, changes across attempts. Exact
copied predecessor requests are historical; new requests interrupt. Actual
5% source-row timing records are phase-specific and exclude restored rows from
their new-work denominator. They do not stand in for whole-card or replay cost.
Source and output checksum validation observes owner requests before each
eight-MiB read and never accepts a partial digest. An interrupted hash restarts
from byte zero. The helper itself is part of the checkpoint binding. Unchanged
player selection and SQLite aggregate queries remain setup units: their actual
duration and memory must be measured before a full source scale is admitted.
A setup or solver unit exceeding native grace requires a separate exact
decomposition; no timeout is waived.

Before admission, a counted constructed fixture must build complete synthetic
2017 and 2026 months through the original parser, including short games,
missing/zero clock observations and players eligible in multiple strata.
Compare the six merged scientific tables, exact original position gzip,
selection JSON, source counts, history payloads and `INDEX.json`. Exercise
owner pauses during execution and verification, transactional continuation,
predecessor byte preservation and refusal of incomplete/tampered sources.
Use source and adapter pins and actual native process, lease, watcher and
descendant CPU evidence. Full input sizes remain a later in-slot cost question.

The aggregate equivalence fixture is a bounded restart unit. If it yields,
restart the whole fixture in a fresh empty attempt; copying its nested outputs
does not create valid nested runtime continuation records. Separate direct
adapter plans exercise the actual sealed pause/continue/replay chains. Original
reference calls inside the constructed fixture still require a measured bounded
runtime; they are never substituted for the cooperative human source adapter.

The original 2,500,000 CPU-second CH family ceiling, two numerical threads,
CPU-only allocation, complete write-through and final-packet policy remain.
No native run is authorized merely by this draft.
