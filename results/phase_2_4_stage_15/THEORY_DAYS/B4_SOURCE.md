# B4 SOURCE

**Hypothesis.** Can the complete named chess month supply the annotated move histories needed to compare skill, deliberation time and their interaction?

**METHOD.** Download the complete April 2017 standard rated Lichess file, check its declared byte size and retain its full hash. Select games independently at probability 0.01 with seed 20261106 before inspecting annotation availability. Keep usable clocks and adjacent non-mate engine evaluations, verify mover sign and increment arithmetic, and exclude missing or nonpositive elapsed times. Reprocess the entire file in a fresh native process and compare source counts, selected-game hashes and feature arrays. This preparation fits no effect model.

**Found.** The complete named-month chess sample passes its frozen source-support checks and independent replay; model inference remains uncomputed.

The source table separates the random game draw from the annotation-dependent analysis sample. It does not represent all chess players or all games as annotation-complete.

| Source or disposition | Count |
|---|---:|
| Complete-month games | 11348506 |
| Selected before annotation filtering | 113257 |
| Selected games lacking both required annotation types | 103345 |
| Selected games with both annotation types | 9912 |
| Usable games | 9912 |
| Parsed moves in annotated games | 628573 |
| Moves missing a required adjacent evaluation or clock | 66230 |
| Moves with nonpositive elapsed seconds | 47556 |
| Usable moves | 514787 |

The frozen floors are 1,000 usable games and 10,000 moves. The source reports no invalid-control, missing-rating or unsupported-move-token rejection among these annotated games; absent disposition keys are zero for this parser, not proof of a general chess parser's completeness. No reduced population or early-file prefix replaces the named-month sample. Missing annotation is selective, and one-second clock precision excludes otherwise legal moves with no positive measured elapsed time. Mate scores do not become invented centipawn values.

The full compressed source is 3,481,200,992 bytes, SHA-256 `559222b0e933bc02281643724fbd9bd46690074b10d784c4f264e0bff6c5992c`. Its selected-game and feature outputs are private; public records contain aggregates and hashes, no usernames or game identifiers. The source is [Lichess's CC0 database](https://database.lichess.org/). No player profile is created.

Complete download, extraction and independent replay used 293.796875 native CPU seconds and 6826.2897042999975 wall seconds. Total recorded B4 native charges, including the retained first wrapper failure, are 298.890625 CPU seconds, below the original 7,200-second ceiling. Network waiting occupied the counted slot but did not consume equivalent CPU time. All output hashes, source pins and coordinator/child exits verify.

**Means.** Run the frozen B4 full-sample cost probe, then admit complete model uncertainty only after its source, instrument/rank and cumulative-cost gates. Clock pressure is not established as an exogenous cause, and passing numerical checks cannot establish the exclusion restriction. The original observational scope and final-packet reporting policy remain. No new tests were harvested from this operational wake.
