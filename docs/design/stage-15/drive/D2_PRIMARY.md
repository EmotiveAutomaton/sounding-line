# D2: menu similarity and choice prediction

This implements the already ratified D2 primary in wave 1, rank 10, Family B.
It is frozen before any corpus fit. The hierarchical Bayes extension remains
separate and conditional on a positive or marginal complete primary. No P1
dependency is introduced. This is a descriptive comparison, never admission.

**Question:** Does predicting which offered suggestion a writer selects work
better when the options differ more?

**Primary:** the content choice model's gain in log score over uniform in the
most dissimilar quintile minus its gain in the most similar quintile; positive
direction. Gain is in natural-log units per selected menu. Mean pairwise cosine
distance among normalized CONTENT_V2 option vectors defines dissimilarity.

**Population:** accepted or subsequently edited suggestions in menus with at
least two options, with one unique exact match between the inserted original
text and the displayed options. Other handling decisions do not identify a
selected option and are excluded, not assigned a synthetic choice. Missing or
ambiguous selected text is counted explicitly. All menu/content/P8 joins must
match before exclusions. Initial input inspection finds 12,196 selected menus
and 41 writers with nonempty chronological choice partitions. This is an input
census, not a result or a guarantee of final extreme-quintile support.

**Model:** pooled conditional multinomial logit over each complete offer set.
Attributes are log character length, normalized position, first position,
context cosine overlap, lexical overlap with the last 1,200 context characters,
and each option's mean cosine distance from its competitors (within-menu
novelty). P8 supplies its finite raw score and six decoding settings, using
signed log-one-plus transforms and missingness flags. Decoding settings also
interact with context overlap and novelty; common menu-level effects otherwise
cancel in conditional softmax. Sixteen training-fitted principal components of
option vectors add semantic coordinates. Features are centered within menu and
scaled by training root-mean-square values. Zero-variance coordinates use scale
one. There is no writer identifier feature or publication of writer models.

The producer score may exceed one. It is a covariate, not a normalized
probability or model likelihood. Position and producer scores can explain gain;
the primary does not isolate content specificity or individual taste.

**Chronology:** the existing 60/20/20 per-writer session partition is retained,
with at least 3/1/1 sessions. Each recipient's pooled training sessions must end
strictly before their first calibration session starts. Calibration sessions
must end before the first test session starts. Actual usable choice counts are
checked in every partition. PCA, scaling and dissimilarity quintile boundaries
use training alone. Calibration selects L2 penalty from 0.01, 0.1, 1 and 10 by
mean log loss, with smaller penalty as the fixed tie-break. There is no refit
on calibration or test outcomes. L-BFGS must converge and have maximum absolute
gradient no greater than 1e-6 under the fixed penalized objective.

**Quintiles and uncertainty:** training quantiles are the four literal 20/40/60/80
percentile cut points; equal boundary values go to the upper bin. Ties may leave
bins empty. Report all five bins and support. The primary equally weights the
writers with both extreme bins: each writer contributes their mean upper-bin
gain minus mean lower-bin gain. At least three writers are required. Two thousand
fixed-seed writer bootstrap draws provide the percentile interval and descriptive
Wald probability. This interval conditions on fitted forecasts, preprocessing and
quintile edges; it is not full training-refit uncertainty. V5's half-Brier headroom
has different units and cannot be used as a denominator for this log-score gain.

**Control:** rerun the entire choice fitting/calibration/scoring pipeline with
one independent uniform choice per menu, generated from seed and menu identity
and fixed across recipient folds. This checks the method on a choice-independent
target, not a conditional causal intervention. Its result is reported beside
the primary; it does not silently change the registered contrast. Pre-run tests
cover an exact uniform null, a planted larger-distance gain, objective gradients
and probability calculations, reversed effects, chronological exclusion,
future-label invariance, source/option mutation refusal, actual serialization,
saved-boundary yielding, immutable reentry and fresh-process primary replay.

**Resources:** one counted CPU slot, at most two numeric threads, below-normal
priority. Forecast under one CPU-hour; the first tenth of recipients is the
execution pilot. Forecast/resource yields occur at saved recipient boundaries;
the shared runtime retains the original floors, threefold wall cap and one
engineering retry. No GPU or paid call. All source/input/test bindings enter
the dispatch ledger before launch.

**Route:** primary positive or marginal opens exactly the packet's hierarchical
Bayes multinomial-logit between-writer spread extension. It is not replaced by
the older finite-mixture model. Any writer-taste interpretation carries V4's
blind label. A negative follows the prescribed specification texture; a null
increments Family B only when its earlier ladder prefix resolves. Unsupported
or failed work is invalid, never a null. No unfinished score is reported.
