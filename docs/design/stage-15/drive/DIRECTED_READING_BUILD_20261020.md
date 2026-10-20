# DR1 full comparison build

This completes the full-comparison implementation left open in the earlier
[preparation snapshot](POST_TALK_PREPARATION_20261020.md). The week packet's
Thursday 07:00 opening and original cost ceiling still apply. No corpus policy
has been evaluated.

**Hypothesis.** Choosing records from their metadata can recover a writer's
full-record profile and identity with fewer reads than uniform random order.
**Method.** Reuse completed, hash-bound PMAP session records and the exact PMAP
dictionary. Retain writers with at least twelve sessions on three prompts and
an available style reference. The fixed reference gallery uses all their
sessions. This is retrospective profile reconstruction with overlapping
reference data, not held-out identification of unseen work.

The metadata acquisition component, four policies and probability ledger retain
the earlier frozen definition. Style, rhythm and handling profiles reproduce
PMAP's formulas. Scaling and partial imputation use only the fixed reference
gallery. A wholly absent prefix cannot identify a writer. Ties do not count
as certain identification, even when the correct writer is tied.

The identity endpoint is the earliest prefix after which identification remains
correct for all later prefixes. The feature endpoint is the first prefix whose
defined features are all within one standard deviation of the complete
reference. Here standard deviation means the sample spread of that writer's
single-session features, fixed across policies. Unsupported features and their
counts are explicit; no absent tolerance is replaced by zero.

A policy that never recovers within the available records is right-censored.
The recorded bounded cost is the writer's session count plus one, with an
explicit censor flag. Therefore the primary is a paired **bounded recovery-cost**
difference, directed minus the mean of 200 uniform random orders. It does not
estimate an uncensored population mean of records needed. The original
unbounded question stays open if censoring matters. Two thousand paired writer
bootstrap draws keep the reference gallery and random-order bank fixed.

A wholly negative interval supports fewer records in this benchmark; a wholly
positive interval supports more. An interval crossing zero is unresolved and
retains the chronological routing default. This does not claim noninferiority.
The other channels and exploratory mixture are descriptive. No population
estimator or inverse-probability weights are emitted.

Nine full-pipeline checks cover PMAP formula parity, original gallery parity,
tie behavior, censoring, fixed eligibility, source/configuration/output
tampering and complete known-answer worlds where selection helps, ties or
hurts. The twelve acquisition checks also pass. Complete contained native
execution and a separate fresh verification process pass on constructed
inputs using all 200 random orders and 2,000 bootstrap draws.

The actual PMAP corpus received source-completion, hash and schema checks only.
Its original records are not regenerated or changed. Output writer identities,
per-record probabilities and recovery paths stay in ignored raw storage.
Public landing reports only aggregates and retained support limits.

**Remaining dispatch requirement:** measured timing admission with the real
dictionary widths and session-length distribution. The small constructed
native run is a correctness check, not a credible corpus runtime forecast.
Build a separately recorded bounded timing pilot for the Thursday window,
charge it and all replay to the original two-CPU-hour allowance, then admit
the full run only if the remaining allowance covers it. No corpus start follows
from this build receipt alone.
