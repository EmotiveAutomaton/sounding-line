# TD6.ic: rare-count sensitivity under the original subreddit bootstrap

DESIGN CHECK: LESSONS sections 3-5 and CONTROLS 6-7 read for this build.
At a zero underlying rate contrast, false support for a reduction beyond 10%
must remain rare. At a 20% reduction, support beyond the 10% bar should be
frequent if this instrument has useful sensitivity. The 10% boundary itself
should not be expected to give high support. Undefined anger denominators and
singleton strata remain visible; no draw or world is discarded or redrawn.

This is the first-generation instrument check registered by TD6, capped at
900 CPU seconds including preparation, validation and independent replay.
Rationale: rare phrase counts and fixed singleton strata can make the original
interval insensitive or misleadingly narrow. The human result is retained.
This is a construction control of the statistic, not a new human hypothesis,
text-generation model, lexical coverage validation or claim of novelty.

Reconstruct the original clear-rating source and strict/fallback matching with
seed 20261106. Reproduce both complete TD6 point estimates, intervals, counts and
support before admission. Retain the actual token lengths, pair memberships,
subreddit strata and the original person-targeted subset. No author field is
read. Never change matching, label thresholds, dictionary or the human outcome.

For the primary and person-targeted populations separately, set a common base
hit probability to their pooled observed hits divided by pooled lexical tokens.
Condition on those token counts and original subreddit allocation. Generate
independent binomial hit counts per comment: anger probability p, disgust
probability p*(1+delta). Freeze delta = 0, -0.10, -0.20, -0.40, +0.20, with
100 worlds per dose per population. Seeds are derived from 20261106, population
index, dose index and world index. These are separate conditional models; their
outputs are not combined as independent evidence or a family claim.

Every world runs the original 2,000-draw matched-pair bootstrap within subreddit
and original three-way rule: supports if the full interval lies below -0.10,
against if above -0.10, otherwise inconclusive. An undefined draw invalidates
that world's interval exactly as in the original; it stays in every denominator.
Also report nominal 95% interval coverage of delta, zero exclusion, collapsed
intervals, undefined points/draws and total realized hits. Keep all world records.

The bootstrap's integer multiplicity bank may be precomputed using the original
random calls in their exact order, then multiplied by each world's sufficient
counts. Prove complete output equality against the original loop on constructed
and actual parent data. This changes execution cost only, including preserving
the singleton pathology. The bank is fixed for all worlds, as the original seed
would be when re-running that pipeline; worlds are independent conditional on it.

Report counts out of 100 with Wilson 95% intervals, including zero/all-success
cells. Separately for each population, sensitivity is adequate in this
construction only if the Wilson upper bound on zero-dose false support is at
most 0.10 and the lower bound on support at delta=-0.20 is at least 0.80.
Otherwise label it limited in construction. This gate is a diagnostic of the
declared model, not a replacement for TD6's frozen rule or a license for a human
negative. At delta=-0.10 report boundary behavior without a power requirement.

The base rates are fitted to the observed sample and held fixed. Independent,
constant-probability token trials omit semantic clustering, subreddit rate
heterogeneity, author dependence, label uncertainty and matching uncertainty.
Counts are not asserted to be realizable grammatical texts. Bootstrap coverage
under this model measures a specific vulnerability or capacity; it does not
prove a human psychological mechanism. Singleton strata are deliberately kept.

Case and check: reconstruct full parent support and output; validate signed,
zero, zero-denominator, singleton, integer-bank equality and immutable native
handler replay before corpus use. Reject absent support or impossible binomial
probabilities. Cost probe uses eight worlds per dose/population with full replay;
forecast the full 100 using total CPU times 100/8 and a 50% margin. No reduced
population or grid: hold if it exceeds the residual 900-second cap. Preserve
all attempts within the original 54,000-second campaign ceiling and freeze/drain.
CPU only, no GPU, paid calls, new source, descendants or early score reporting.
