# TR3 discovery feature selection

This freezes the remaining feature-selection step of Week 3 TR3 before its
model-versus-human contrast is computed. It uses the exact WB1 discovery half
and the independently reconstructed suggestion and human-production counts.
The October 27 continuation permits this unchanged commissioned preparation
within the original 7,200 CPU-second ceiling, with no further automatic repairs.
The previous breach and failed attempts remain. A new failure stops TR3 for
review; a renamed retry is not authorized.

The feature representation remains literal punctuation and case-folded word
one-, two- and three-grams from the completed counters. Function words and
lexical hedges enter through those same word features, without a separately
chosen dictionary or semantic label. This does not establish their pragmatic
function. Completed later-deleted human production remains in the human bank.

For each of the four feature families separately, form the union of features
in the two discovery banks. Add one half to every feature count in each bank
and normalize within that bank and family. Give the two banks equal prior
weight: the pointwise mutual information for model source is
`log(2 * model_probability / (model_probability + human_probability))`.
High mutual information means at least `log(4/3)`, equivalently model
probability at least twice human probability. Use the probability ratio for
the threshold comparison. Require at least ten model occurrences, five model
sessions and five distinct model writers. These fixed support floors prevent
a rare feature from being selected solely through smoothing or one writer.
Retain every qualifying feature, without a top-k limit. If either family's
unsmoothed bank is empty, mark that family unsupported, rather than use a
smoothed comparison as evidence.

Assign frequency deciles within each selected feature family using pooled
discovery occurrence counts (model plus human). Features with equal counts
remain in the same decile: sort counts ascending, and use the midpoint of
each tied group's cumulative rank interval, times ten and rounded down,
bounded above at nine. This is an exact integer calculation. Counts and
family totals are retained, so neither source frequency nor decile can be
silently redefined in the later matching step. An empty selected bank is
unsupported for carryover, not a null result about people.

All discovery session identities, prompt identities and writer assignments
must match the completed exposure census. Reaggregate every session and
require exact equality to both parent aggregate files, including session
support. Test-half payloads are not opened. Retain the full population census
and bind every input and output hash. Re-entry must leave completed outputs
unchanged. A separate native process must reconstruct the complete selection.

Known-answer checks precede corpus execution: equal banks select nothing;
a planted recurring model-associated feature is selected with the analytic
information value; rare and single-writer features are refused; tied counts
share a bin; a family without both banks is explicitly unsupported; malformed
counts, changed aggregates or identities are rejected; full-handler reentry,
replay and tamper refusal pass. These validate selection, not human carryover.

The subsequent matched exposure construction, all three secondary contrasts,
writer-clustered inference and known-answer calibration remain separate
implementation and admission gates. No test-half outcome is used here and
no Tier 4 holdout is opened. This is an operational specification within TR3,
not a new follow-up or a change to its primary contrast.
