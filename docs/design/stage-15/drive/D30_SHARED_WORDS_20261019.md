# D30.v2: shared-word specificity

Implements mid-run section 2.7 and the week continuation. Use the completed
PMAP shared dictionary, the corpus's 100 most frequent produced words and 22
punctuation tokens, without changing that roster after inspecting timing.
It includes subsequently deleted text. Exclude word bigrams and every word or
symbol outside that frozen roster. Recompute the original prompt-conditioned
marker classes on these selected occurrences. Report every population boundary.

Primary: the original writer-fixed-effect local-minus-pervasive log-pause
coefficient, positive expected, with the original nuisance variables and no
additional marker-count adjustment. Preserve the same positive-pause clock and
original eligibility rules. Resample real writers 2,000 times, seed 20261017.
Retain the original one-per-writer-marker label-shuffle control and its interval.
Use 200 within-real-writer raw-outcome permutations, seed 20261018; report mean,
sample SD, central 95% points, upper-tail probability and the fixed quarter-SD
bias flag. This is a descriptive reference, not conditional causal inference.

Required paired history control: reassign sessions using the original fixed
procedure, classify under both histories, and keep identical supported rows,
outcomes, covariates and real-writer clusters. Report both arm estimates and
their own-minus-reassigned difference with 2,000 paired real-writer draws and
200 paired outcome permutations. Report excluded occurrences explicitly. The
full own-history primary and the paired difference answer separate questions;
neither replaces the other. Every fit must complete; no failed draw is dropped.

Correction texture retains immediate user deletions, later user edits,
within-burst insertions and non-user changes separately, for the full primary
population and both paired arms. These are descriptive occurrence proportions,
with no additional significance tests or psychological attention/flow claim.
Use the completed exact revision labels and original source-row identities.

Freeze inputs, dictionary, original sources, code and validation evidence.
Immutable consecutive blocks permit exact continuation. Fresh native replay
reconstructs selected source, dictionary and labels and refits every draw.
Original earlier full-vocabulary studies and failed attempts remain unchanged.

Forecast 600 seconds including source and full replay, original ceiling 3,600
seconds, with all validation charged before main dispatch. The existing single
cumulative S4 maximum remains 7,200 seconds; no reset. One counted CPU slot,
two numerical threads, BelowNormal priority, 512 MiB output cap. The demo
reservation stays; no GPU or paid reader. Completed shared source preparation
remains separately accounted and is not rerun.

**DESIGN CHECK.** LESSONS 3-5 and CONTROLS 1-7 reread for this implementation.
Known positive and reversed timing preserve their sign; an exact zero outcome
has zero point and interval, and identical paired arms have an exact zero gap.
Independent dummy-variable least squares checks the primary. Selection tests
exclude rare words, symbols and word bigrams while retaining listed punctuation;
source-position and full/paired population checks prevent a changed denominator.
Configuration, dictionary and immutable-block mutation must refuse regardless
of scientific outcome. Whole-handler reentry and fresh replay precede main
dispatch. No scientific admission follows from constructed validation.
