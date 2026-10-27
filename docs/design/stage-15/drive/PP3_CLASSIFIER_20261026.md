# PP3: frozen complete classifier and references

Implements Week 3 PP3 against the completed `PP3-inputs` preparation, before
looking at predictive scores. The primary population is every released labelled
row; repeated rows from a span are not independent intentions. This does not
reuse the publisher's within-project training split. Previous source exposure
is explicit: this is descriptive, with no untouched confirmation set.

## Models and estimands

Leave each of the five complete projects out. Fit an intercept and ridge
least-squares predictor of the one-hot annotation labels, with penalty 1 on
training-standardized features and no penalty on the intercept. Predict the
three-category labels by projecting their raw regression scores onto the
probability simplex. The projection gives valid probabilities and is the nearest
valid vector under the same squared-error loss. The fifteen-category auxiliary
uses its own simplex projection. All classes remain in macro-F1, with a zero
contribution if a class has no true or predicted instances. Deterministic ties
use the fixed alphabetical class order.

This single fixed linear model is a computationally bounded baseline, not a
model search or claim of an optimal ceiling. Training standardization and ridge
factorizations are reused exactly across reference draws because they contain
no outcomes; every label-dependent coefficient and prediction is rebuilt.

Primary: pooled three-category macro-F1 of process-only predictions minus the
better of (a) training-frequency-prior argmax macro-F1 and (b) the mean macro-F1
of 200 within-project label permutations. The prior's full probability vector
is used for half-Brier. A second bank of 200 within-project-author permutations
preserves author-specific class proportions and implements the inherited
within-writer default. The explicit within-project card comparator remains the
primary; both references and their bands/probabilities are reported.

The same shuffled fifteen-label vector determines its three-label mapping.
All model arms, prior probabilities and labels are evaluated on the same held
project. Reassign both training and held-project labels, preserving each
project's exact class counts. This is an outcome-reassignment reference, not
word shuffling, person identification, or a surrogate for psychological truth.

Report process half-Brier improvement over the prior, fifteen-category macro-F1,
the gain from adding content, and every confusion matrix. The content arm adds
128 nonnegative hashed Unicode word-count bins from the complete before text
and 128 separate bins from the complete after text, each L2-normalized, to the
24 process features. It uses no learned vocabulary, clipping or outcome-dependent
selection. Hash collisions and lexical compression limit this auxiliary. All
word content stays outside the primary. Rebuild its full two reference banks.

## Uncertainty and gates

Use 2,000 paired author-cluster bootstrap resamples of all twelve project-scoped
author identities, retaining row weights and class counts within each sampled
cluster. Also report 2,000 project-cluster resamples, because the split and
source-dependence unit is the project. Five projects provide weak population
uncertainty; neither interval includes model-refit uncertainty. Each resample
recomputes macro-F1 and the better comparator, including the reference mean,
from cached cluster confusion matrices, rather than averaging per-author F1.
All draws use seed 20261026 with separate deterministic streams.

Use the shared descriptive interval state on the primary author-cluster
contrast, and separately report the project-cluster state and one-sided
permutation probability. Do not turn a positive classification contrast into
probability calibration: the half-Brier comparison is reported alongside it.
No cross-corpus goal mapping or public badge is licensed. Empirical references
are not expected to have zero absolute macro-F1; the training prior is a real
competitor, and no chance-centred fake-identity gate is applied to classification.

DESIGN CHECK: LESSONS 1d, 2 and 3–5 and CONTROLS read for this build. A constant
feature world must reproduce the training prior exactly, under either label
assignment. A constructed separable signal must be recovered across projects;
permuting its labels must remove that advantage on average. Future held-project
features must not alter training preprocessing or coefficients. Simplex outputs
must be nonnegative, finite and sum to one. Source mismatches, missing rows,
wrong class mappings, nonfinite solves or replay disagreement fail as invalid,
never as a scientific null. Shared interval bands are exhaustive; source and
known-answer failures stop before any corpus comparison.

## Cost and execution

Original total ceiling 7,200 CPU seconds; preparation charge/reserve 120.96875.
Reserve another 120 CPU seconds for this build and its targeted checks. Run a
constructed native rehearsal before the real-source timing attempt. The timing
attempt uses all rows, all held-project fits, both arms, twenty permutations
per reference and the full bootstrap. It discards all scientific scores and
repeats independently. Forecast the full execution plus independent replay
conservatively at twelve times its measured cost; charge both pilot and full
execution within the remaining original allocation. If that forecast cannot
fit, hold the full card without reducing any bank or population. A main job
uses both complete 200-draw banks, immutable checkpoints, two numerical threads,
one counted CPU slot and the ordinary resource/lease/wake contract.
