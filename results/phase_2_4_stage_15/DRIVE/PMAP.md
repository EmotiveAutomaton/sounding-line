# Where the writer shows in the logs

**Hypothesis.** A writer is more recognizable from the words and punctuation she produces than from how she handles model offers.
**METHOD.** Reconstruct seven channels from the human writing logs, put each writer's whole prompts into alternating chronological halves, and identify each half-A writer against the fixed complete half-B gallery. Pair 2,000 real-writer bootstrap draws across channels and compare with 200 fixed whole-session reassignments that rebuild every profile; an exact nearest-neighbour program reads the profiles, while the content channel uses saved MiniLM vectors.
**Found.** Style identification exceeds handling identification by 0.311111, with a paired 95% interval [0.111111, 0.488889]. **Means.** Production features provide a stronger observed identity signal on this corpus; the biased reassignment control and incomplete content-channel controls limit the route. This does not establish automaticity, values, taste or a psychological component.

The table reports the fraction of writers correctly identified from each channel, average fake-writer accuracy, supported reassignments, and the paired real-minus-fake accuracy difference with its 95% percentile interval. Probabilities are descriptive two-sided normal-reference values from the bootstrap standard error. Chance is 1/45 for the first six channels and 1/42 for content. Fake content accuracy describes only the supported subset; it is not an inferential control pass.

| Channel | Writers | Real accuracy | Fake mean | Valid reassignments | Paired difference [95% interval] | Probability | Paired state |
|---|---:|---:|---:|---:|---|---:|---|
| Handling rates | 45 | 0.155556 | 0.033000 | 200/200 | +0.122556 [+0.030937, +0.233056] | 0.025718997 | positive |
| Typed words and punctuation | 45 | 0.466667 | 0.007000 | 200/200 | +0.459667 [+0.306108, +0.613114] | 1.8475488e-09 | positive |
| Logged production rhythm | 45 | 0.977778 | 0.034111 | 200/200 | +0.943667 [+0.897889, +0.971667] | underflow | positive |
| Revision rates | 45 | 0.311111 | 0.034111 | 200/200 | +0.277000 [+0.148553, +0.409225] | 2.9492719e-05 | positive |
| Request frequency | 45 | 0.111111 | 0.027667 | 200/200 | +0.083444 [-0.004000, +0.193781] | 0.074003152 | marginal |
| Prompt-relative final length | 45 | 0.200000 | 0.030333 | 200/200 | +0.169667 [+0.057664, +0.303003] | 0.0058529259 | positive |
| Accepted-minus-dismissed content | 42 | 0.047619 | 0.014943 | 145/200 | invalid; fixed support fails | not defined | invalid |

The primary style-minus-handling contrast has descriptive normal-reference probability 0.0012194267. Its complete session-reassignment distribution has mean -0.026000, standard deviation 0.0295853 and 95% range [-0.088889, 0.022222]; the one-sided permutation probability is 0.0049751244. Its mean exceeds one quarter of its standard deviation in absolute size, so the frozen bias flag fires. All six complete channel controls also retain their distributions and chance-centered checks: handling, style, rhythm, revision and length flag; requests does not. These are session-reassignment controls, not within-writer outcome shuffles. Paired bootstrap intervals condition on the fixed gallery and fixed reassignment ensemble.

Content has 55 unsupported assignments out of the fixed 200. The runner refuses own-minus-fake inference instead of redrawing or treating the 145 supported assignments as complete. Its real accuracy alone does not license the packet's at-chance taste route. The rhythm probability underflows to machine zero; zero is not an exact probability claim. The JSON preserves the raw value with an explicit underflow flag.

The next table summarizes Spearman-Brown corrected split-half reliability, derived from each feature's Pearson correlation. A larger positive value means stronger cross-half consistency. The median is a descriptive summary of defined features, not a channel-level inferential statistic; negative values and constants remain visible. The accompanying JSON contains every real feature reliability and every fake reliability distribution, including missing/constant reasons and draw counts. Style and rhythm feature labels are indexed in the public file; the exact dictionary and original labels remain pinned privately.

| Channel | Defined / total features | Median reliability | Minimum to maximum |
|---|---:|---:|---|
| Handling rates | 4/4 | 0.812400 | [-0.079316, 0.905529] |
| Typed words and punctuation | 121/122 | 0.475518 | [-1.112058, 0.965834] |
| Logged production rhythm | 22/22 | 0.985157 | [0.927094, 0.997615] |
| Revision rates | 3/3 | 0.952677 | [0.877672, 0.958800] |
| Request frequency | 1/1 | 0.981581 | [0.981581, 0.981581] |
| Prompt-relative final length | 1/1 | 0.950827 | [0.950827, 0.950827] |
| Accepted-minus-dismissed content | 382/384 | 0.044314 | [-1.543872, 0.775792] |

The source roster contains 1,399 sessions from 61 writers; 45 satisfy at least four sessions on two prompts, and content retains 42. The real profiles have no missing half-A/half-B cells and no nearest-neighbour ties. One style feature and two content dimensions lack defined reliability; constants are not replaced with zero. The full typed-corpus dictionary is transductive: its 100 most frequent words and 22 punctuation marks are fixed without identity/outcome optimization, and it includes later-deleted typed text. It is not a part-of-speech-filtered function-word list. Rhythm uses logged text-delta intervals, which may retain recording or device context; it is not a direct keypress-speed or automaticity measure.

Revision counts content/housekeeping edits and the share of originally accepted canonical characters later deleted by the writer. Insertion-only additions are counted separately and are not mislabeled as deletion. Content compares accepted vectors with equally weighted dismissed-menu means; ignored menus and unselected options in accepted menus are excluded, and individual examination is unknown. Canonical source replay corrects 2,510 prepared-choice disagreements. The original preflight failure is preserved: 46 extra raw sessions caused the source namespace mismatch, while all 1,399 intended sessions were present. The separate recovery changes only that source join.

All 53 source/input pins and 3,214 completion artifacts verify. Full fresh-source/statistical replay, exact native exits and released CPU slot pass. Targeted known-answer, null, reversed-direction, constant and source-refusal tests and the monitored native fixture preceded production. Cumulative execution and verification took 3,191.018 seconds including the charged original failure, within the unchanged 5,400-second ceiling.

The primary is positive for ordered Family E accounting; it adds no family null. The predefined rhythm-minus-handling extension is eligible but has not run as a separate paired contrast. The observed production signal is recorded with the control warnings; there is no clean person-specific causal or taste admission. Channel reliabilities and that qualified route go to the companion interfaces at the next digest. Theory rows, afterwords and TODO integrate at 20:00 PDT, as required by the active packet.

[Complete aggregate and feature reliabilities](PMAP.json).
