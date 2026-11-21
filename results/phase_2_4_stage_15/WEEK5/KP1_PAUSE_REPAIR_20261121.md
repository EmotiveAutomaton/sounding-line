# KP1 PAUSE REPAIR 20261121

**Question.** Does a longer pause than expected for this writer and word predict a nearby deletion or a less predictable continuation?

**Method.** Subtract the frozen D33 prediction from the observed log pause and standardize the remainder within writer. The primary model asks whether a deletion of at least three characters begins between the focal word’s first keystroke and the sixth following word’s first keystroke. Fit the registered unpenalized writer-intercept logistic model with the original word covariates. For the secondary, regress the mean personal surprisal of the next three typed words on the same predictor and covariates. Resample whole writers 2,000 times. For the primary, require an odds ratio above 1.10, a 95% interval wholly above one, and a point estimate above the 97.5th percentile of 200 within-writer shuffles. The secondary requires a point estimate above 0.02 natural-log units and a 95% interval above zero.

**Sample.** 35 writers in the calibration-supported CoAuthor sample. The deletion analysis covered 36,782 eligible words and the continuation analysis covered 36,075. The original 41 writers contributed 78,602 evaluation words. The frozen calibration rule retained 35 writers, 192 evaluation sessions and 52,127 words. For deletion, the filter removed 8,483 words after suggestions, 3,681 with ambiguous focal onset order, 3,641 with ambiguous sixth-word onset order and 1,127 without a sixth following word. For continuation, it removed the same suggestion and focal-onset groups, 6,793 with ambiguous continuation order and 563 without three following words.

**Result.** The deletion comparison could not estimate an odds ratio. Longer pauses predicted a modest increase in surprise over the next three words, including away from sentence boundaries. The raw pause showed the same pattern. The deletion point fit reported separation or singular information. All 2,000 primary draws and all 200 shuffled controls lacked estimates. The registered control percentile is undefined. The primary verdict is void. For the secondary, each within-writer standard deviation of residual pause corresponded to 0.0255 additional natural-log units of surprise (95% writer interval 0.0087 to 0.0386).

Each deletion row targets an odds ratio. Each continuation row gives the change in mean surprisal of the next three words per within-writer standard deviation of pause. The comparison uses residual pause unless the row specifies raw pause. Boundary checks exclude sentence starts and words following punctuation.

| Comparison | Eligible words | Estimate | 95% writer interval | Valid draws |
|---|---:|---:|---:|---:|
| Any qualifying deletion | 36,782 | Unavailable | Unavailable | 0 |
| Deletion of earlier text | 36,782 | Unavailable | Unavailable | 0 |
| Deletion of word or later text | 36,782 | Unavailable | Unavailable | 0 |
| Deletion, away from boundaries | 33,141 | Unavailable | Unavailable | 0 |
| Deletion, raw pause | 36,782 | Unavailable | Unavailable | 0 |
| Deletion, raw pause away from boundaries | 33,141 | Unavailable | Unavailable | 0 |
| Next three words | 36,075 | 0.0255 | 0.0087 to 0.0386 | 2,000 |
| Next three words, away from boundaries | 32,510 | 0.0330 | 0.0176 to 0.0463 | 2,000 |
| Next three words, raw pause | 36,075 | 0.0290 | 0.0112 to 0.0430 | 2,000 |
| Next three words, raw pause away from boundaries | 32,510 | 0.0364 | 0.0195 to 0.0512 | 2,000 |

**Limit.** The typing log records revisions and word choices. It contains no independent observation of an attention switch. With identical covariates, the adjusted raw-pause and residual-pause models span the same regression space. Their per-standard-deviation coefficients use different scales.

The independent process reproduced every fixed draw and control disposition. The owner verified 8,123 output hashes and 418 pinned inputs. The final continuation and replay used 31,835.22 CPU seconds. The separate KP1b human replication remains held for verified source linkage.

[Continuation figure](KP1_PAUSE_REPAIR_20261121.png) · [Aggregate record](KP1_PAUSE_REPAIR_20261121.json).