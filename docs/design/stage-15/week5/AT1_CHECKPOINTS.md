# AT1 immutable checkpoint successor

The `week5_at_history_v2` successor changes execution partitioning only.
Its input loader, own/donor history construction, budget matching, prompt
exclusion, calibrated mixture, original joint fit and every random seed remain
the frozen AT1 implementation. Original source and result bytes remain intact.

## DESIGN CHECK

Method LESSONS sections 3–5 and CONTROLS sections 1–6 informed the original
design. The new native fixture runs all 2,000 constructed writer resamples
through the actual successor block handler and repeats them in a fresh process.
Its point and first three draw outputs must exactly equal the frozen original
block. The fixture interrupts before loading and after one sealed draw, resumes
the remaining draws, and refuses an altered checksum. This checks interrupted
execution without changing the signed/null statistical rulers already passed.

Every point and global draw receives a source/science binding and checksum
seal. An execute resume reuses only validated bytes. The independent verifier
recreates all fitted draws with `SeedSequence([20261107, global_index, 1])`,
including whole-writer selection and fresh donor matching, and compares exact
saved records. Undefined donor support and numerical fits remain invalid or
unsupported in the original final reduction; no failed draw is discarded.

Blocks contain at most one hundred draws. A runtime resource request is honored
before source loading and after a complete point or donor draw. A bounded
elapsed quantum of at most 1,500 seconds yields at the same sealed boundaries.
Individual fitted draws remain indivisible; the first count-one cost timing
must establish that a single fit respects the runtime limit. Accumulate the
first hundred global indices as the five-percent in-slot pilot, using smaller
blocks when the measured fit duration requires it. Both phases and all resumed
segments count toward AT1's 40,000 CPU seconds and AT's family ceiling.

The smaller-route and descriptive support rules are unchanged. The new module
accepts explicit blocks and the original complete-block reducer only; it does
not expose an uncheckpointed monolithic run. This source successor does not
change any donor, scientific threshold, history budget or population scope.
