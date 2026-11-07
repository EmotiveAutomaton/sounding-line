# AT execution and follow-up specification

Prospective implementation supplement, November 7, 2026. Read with [AT](AT.md)
and the curator's [packet](PACKET.md). No human effect has been inspected to
choose these rules. Existing source/scoring-v1 imports stay frozen while live.

## DESIGN CHECK

Method LESSONS sections 3–5 and CONTROLS sections 1–6 were read for this build.
Fixture-only native receipts test real CPU cached/direct forwards, sealed block
replay, identical-reader gain, signed own-minus-donor regression, entropy and
stop-prediction plants. Exact engine-function tests run the original pinned
code with constructed token scores and verify name/number/code holdouts. Those
tests validate implementation; they supply no human scientific finding.

## Execution contracts

Every module exports `execute(output, inputs, config)` and an independent
`verify` with the same arguments. Native runtime controls ownership, counted
slots, resource limits and actual combined execute/verify CPU accounting.

| Module suffix under `runners.drive.cards` | Input contract | Output / dependency |
|---|---|---|
| `week5_at_source` | P6 root, timing root, raw roster, repo root | Private source sessions and fixed final/frozen-20% batches |
| `week5_at_covariates` | P6 root, raw roster, repo root | Existing D33 raw-screen/session controls, replayed for the full population |
| `week5_at_scoring_v2` | One batch and pinned model manifest | Eight-word sealed blocks; cold load included in default 1,200-second elapsed quantum; seeded 2% fresh forwards |
| `week5_at_collect` | Source root, complete model-bank manifest, covariates root | Complete paired analysis rows; AT2/AT3 refuse absent timing controls |
| `week5_at_analysis` | Complete paired rows and declared card/config | Primary/refitted AT2–AT4 aggregate |
| `week5_at_remaining` | Verified source and AT2 selection roots | Remaining at-typing batches for selected reader and engine pair |
| `week5_at_history` | Verified D33/P6 roots and timing roster; intervals for alternate pause outcomes | AT1 fixed global bootstrap blocks, then complete reduction |
| `week5_at_shared` | Same retained D33/P6 inputs | Conditional AT1.s genre-population reader comparison |
| `week5_at_engine` | Frozen source / final document / model manifest | Original certified product attention marks |
| `week5_at_engine_analysis` | Complete exact product exports and timing rows | AT2.e or AT4 engine secondary |

AT1 uses global draw indices with independent `SeedSequence([20261107,index,1])`
streams. Each block has at most 100 refits. Full uncertainty uses all indices
0–1999 exactly once; screening uses 0–199. The first 100 draws are the 5% pilot
when the cost projection calls for it. Each block is independently verified,
including donor draws and recalibration; the final reduction refuses missing,
duplicated or mixed-estimand indices. This keeps fresh verification inside the
native quantum. A failed draw remains in the complete reduction as invalid.

Both own and donor mixture weights are calibrated from the frozen calibration
sessions when a prompt or representation texture changes. Random matching
draws a fixed donor set for each recipient/genre across that draw's sessions.
Same-prompt matching preserves the recipient history's prompt-specific session
counts and exact overall token budget. Below twenty writers, AT1 runs a pooled
descriptive regression; AT2 likewise uses a pooled training fit below forty.
AT3 computes exact per-writer sufficient statistics before each cluster refit,
preserving the full estimator without repeatedly allocating the whole corpus.
Alternate hesitancy and stop outcomes require exact onset joins to the retained
timing intervals. AT4 keeps only final-text features in its classifier.

`selection_admissible` in AT2's result is true only for all ten commissioned
readers (explicit permitted cached Pythia substitutions), 2,000 draws, final
1,024-token context, unfiltered genre and the log-pause primary. Downstream
cards require this flag and verified completion. A texture winner cannot
release the dependency. `week5_at_grid.grid(genres)` enumerates declared cells,
conditional descendants and dependencies; it is not automatic dispatch authority.

## Conditional branches

AT1.p compares the calibrated vocabulary-only and bigram-only history caches.
AT1.s uses a genre-adapted population cache built only from other writers'
earlier completed same-genre sessions, excluding the target prompt. It tunes
the population/cache mixture on calibration token loss and evaluates pause-fit
gain on held-out writers. The analyst-declared comparison uses AT2's 0.002
nats/word practical scale and cannot retroactively promote AT1's primary.

AT2.e and AT4's engine secondary run unmodified ToMpathy modules from
`certified-fit-1`, resolved commit `5f3ad0a304727fff5e1a6beca592e786ee71b181`.
The MIT source snapshot and model aliases remain private. Models use the
original CPU dynamic-int8 reader and the original 2,048-token/512-token-block
scoring function, including byte-overlap allocation and product holdouts.
An original product attention span marks a word only when it contains that
whole exact surviving occurrence. AT4 compares those binary marks' AUC with
the held-out final-text baseline; AT2.e uses the maximum returned span departure
covering that word, zero when unmarked. Names, numbers, code and noncontent
words are counted as unsupported. These are explicit export mappings of the
exact product function, not ordinary token surprisal relabelled as product
marks. Full-document context includes the final observed document; no held-out
pause is read by the engine. Original recipient source files are never edited.

The first 5% of each long scoring workload is an in-slot pilot. It must include
model load, measured score work and independent verification in its projection.
The remaining packet ceilings, sample/doubling routes, idle-slot continuation,
texture stops and two-level re-read rules are enforced by the owner runtime.

## Complete scopes and resource checkpoints

`week5_at_scope` accepts the verified full source and an optional whole-writer
count selected from the cost pilot. It uses seed 20261102 and Hamilton
allocation by each writer's majority session genre, reading no scores or
pause outcomes. Its source-shaped output is consumed by the ordinary complete
bank collector. Record the selected count, full count and share as sample
scope in every downstream landing. Below twenty writers is descriptive only;
the pilot should retain the declared twenty-writer floor whenever possible.

With `typing_population='full'`, this adapter supplies a complete at-typing
union, preserving original batch keys for the first twenty percent so their
verified scores are reused. The remaining source batches and the original
twenty percent must both exist for each selected/engine reader before
collection; no partial remainder is interpreted. The ordinary collector can
also consume a complete ten-reader scope for the original model-selection
primary. Frozen sample choice does not license comparing mismatched scopes.

The v3 scoring successor checks the runtime's `YIELD_REQUEST.json` before
loading and after each sealed eight-word block. Its numerical and statistical
primitive is unchanged from v2. The native checkpoint fixture interrupts at
eight words, resumes all eighteen and replays in a fresh process. Original
v1/v2 source closures stay immutable. The scheduler includes cold load and
verification cost in the first five-percent pilot.
