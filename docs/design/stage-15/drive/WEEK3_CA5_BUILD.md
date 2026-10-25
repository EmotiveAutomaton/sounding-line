# CA5: stable harm-topic judgments beyond demographic group and leniency

This is the frozen implementation contract for the October 25 packet's CA5.
The primary population is all 123 released raters and all 350 items. The
sensitivity population removes exactly the 19 raters listed in the
[official pinned codebook](https://raw.githubusercontent.com/google-research-datasets/dices-dataset/b5596d9edd585361967991a591abc7b11fb1f7a3/350/README.md),
leaving 104. No participant is selected using this comparison's outcomes.
The codebook and existing CSV hashes are enforced before scientific execution.

The analysis uses the per-rater overall safety response, encoded No=0,
Unsure=0.5 and Yes=1. Expert `harm_type` supplies topic categories; the source
gold label is not used as an individual value or truth target. Recruitment
strata, gender by race, define demographic groups. Singleton strata are counted
and unsupported for a group-relative profile, rather than silently combined
with another demographic group.

For each rater and item, subtract the other raters' mean in the same group.
Within each odd/even item half, subtract the rater's overall residual mean,
then average the centered residuals by expert harm topic. A topic must occur
in both halves; exclusions are counted and the rule never depends on ratings.
The per-rater recurrence statistic is the Pearson correlation across topic
coordinates. Constant profiles contribute exactly zero and are counted.
The primary is the equal-rater mean recurrence minus its permutation mean.

One thousand null draws independently permute rater labels within group on
each item and rebuild the full adjusted profiles. Two thousand paired rater
bootstrap draws give the interval on the real-minus-null contrast. The report
also retains the null band and one-sided permutation probability. A positive
requires a positive interval lower bound and a probability below .05. Both
raters' denominators run through exactly the same pipeline. The original CSV
is fully crossed; missing or duplicate rater/item pairs fail closed.

A balanced fixed-effects decomposition reports sums of squares for group,
item, rater within group, item by group, and the remaining item-by-rater term.
With one judgment per rater/item, that last interaction cannot be separated
from observation error; the runner does not claim otherwise.

Eight targeted tests pass: exact nuisance cancellation, stable and reversed
directions, decomposition closure, group/item-preserving permutation, planted
signal against rebuilt controls, both fixed populations, complete fresh replay
and source/bank refusals. Corpus execution and native fixture validation remain
owner dispatch steps. No corpus result has been computed by this builder.

Scope: recurrence of perceived harm judgments. Personal values, objective
safety and competence are separate questions. Outputs contain aggregates only.
