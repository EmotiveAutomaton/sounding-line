# Canonical choices: content, position and length diagnostics

**Hypothesis.** Authenticated choice labels reveal whether the original content-feature reader predicts later selections better than uniform choice and simple position or length baselines.
**METHOD.** Refit the unchanged content model and separate position-only and length-only models on the original chronological partitions, using canonical actual selections and all original options. Compare their writer-averaged held-out log scores on 2,543 menus from 41 writers, with 2,000 paired writer resamples and a complete independently generated uniform-choice control for each model.
**Found.** Content and length beat uniform; content beats position, but its advantage over length remains unresolved. **Means.** The corrected source supports predictive signal in these features, while this diagnostic does not isolate a semantic or personal-taste contribution. The original extreme-quintile contrast remains marginal and its uniform-choice control remains positive; original D2 inference and the taste-gated extension stay held.

Each row below is one fitted reader and target. Gain is the equal-writer mean improvement in natural-log probability per held-out menu over a uniform distribution across that menu's options; positive is better. The 95% intervals resample writers, pairing the same draws across readers. The probability column is a descriptive two-sided normal-reference probability computed from bootstrap standard error, not a preregistered confirmatory test. A uniform-control row refits the whole pipeline on independently generated per-menu uniform targets.

| Reader and target | Gain over uniform | 95% interval | Descriptive probability | Frozen state |
|---|---:|---|---:|---|
| Content features, observed choices | 0.0287461376 | [0.0156144862, 0.0418037565] | 2.16244539e-05 | positive |
| Content features, uniform control | 0.00147816246 | [-0.00278743881, 0.00581098878] | 0.503342504 | marginal |
| Position only, observed choices | 0.00261911321 | [-0.00199787438, 0.0072899978] | 0.262559318 | marginal |
| Position only, uniform control | 0.000654540681 | [-0.0011236201, 0.00206398496] | 0.421239793 | marginal |
| Length only, observed choices | 0.0201447939 | [0.011422118, 0.0292047206] | 1.13311051e-05 | positive |
| Length only, uniform control | 0.000350516932 | [-1.2740923e-05, 0.000780174648] | 0.0774951379 | marginal |

The paired differences below use exactly the same held-out menus and writers. They compare the complete content model, which already includes lexical and mechanical covariates, with the indicated reduced baseline; they are not isolated semantic-feature ablations.

| Paired comparison | Difference in log gain | 95% interval | Descriptive probability | Frozen state |
|---|---:|---|---:|---|
| Content minus position | 0.0261270244 | [0.0139038568, 0.0392566546] | 5.76629719e-05 | positive |
| Content minus length | 0.0086013437 | [-0.00135632261, 0.0186264325] | 0.0942102541 | marginal |

The original D2 contrast is repeated separately on training-defined dissimilarity quintiles. It is the highest-minus-lowest quintile log gain within each writer, averaged across the 33 writers represented in both extremes, covering 1,000 extreme-quintile menus. Eight test writers lack both extremes. Its observed contrast is unresolved and the uniform-target control is positive, so it still does not support the old dissimilarity interpretation.

| Original extreme-quintile replication | Difference in log gain | 95% interval | Descriptive probability | Frozen state |
|---|---:|---|---:|---|
| Observed choices | 0.00038656459 | [-0.0379444094, 0.0336061439] | 0.982891467 | marginal |
| Uniform-choice control | 0.0135671044 | [0.00386298811, 0.0257370383] | 0.0154738389 | positive |

Canonical source preparation preserves all 16,855 menus and 69,109 offered options. No offered option was filtered or truncated by this feature input; 9,036 contexts retain the original last-254-token embedding window. Suggestion embeddings retain the original first-254-token policy, with no truncations observed. Full text still supplies lexical and length covariates. Hidden producer-internal candidate filtering is not observed. The original 12,196 eligible menus remain: 4,174 menus have no observed selection and 485 contain only one option. Twenty writers lack the original minimum chronological session support. Canonical source choices differ from the prepared index on 2,510 eligible menus across the source census; there is no outcome-selected exclusion.

All original training/calibration/test memberships, chronological cutoffs, dissimilarity boundaries, training PCA and scaling are retained. Penalties are selected from the original four values on the original calibration sessions. Intervals condition on these fitted forecasts, transformations and penalty choices; they do not cover training-refit uncertainty. The uniform-control comparison uses the original independent per-menu seed, not a substitute for a repeated outcome shuffle or a fake-writer control. Its aggregate intervals crossing zero do not certify the separate quintile contrast, whose control warning survives.

Five focused checks, serialized pilot/full replay and counted native validation preceded the measured corpus timing pilot. All 51 full-run source/input pins and 95 final artifacts verify. Complete fresh source reconstruction refits all three models and three controls for every recipient. The pilot recipient and its metadata are reused byte-for-byte and included in fresh verification. Native workers exited and the counted CPU lease was released.

Controller time was 265.062517 seconds; including the 52.904994-second pilot gives 317.967511 seconds within the 900-second combined ceiling.

This is a separately commissioned diagnostic on exposed human CoAuthor process records, read by fitted programs. It does not reopen the original held inference, admit the failed taste instrument, create a new family-routing result or launch an extension. All ten reported descriptive probabilities enter the multiplicity ledger as diagnostics. Theory rows, afterwords and TODO integrate at 20:00 PDT.

Curator roll-up: reader diagnostics; do corrected choices support content prediction beyond simple baselines?; **Infrastructure**; content beats uniform and position but its advantage over length is unresolved; project meaning: predictive source recovery is useful while semantic and personal-taste claims remain unestablished; next engineering obligation: preserve the original-source and taste holds and integrate the complete diagnostic at the daily digest; public claim unchanged; curator decision required: No; detail: D2-diagnostics-canonical.md/json.
