# PP1: can logged writing intervals distinguish process boundaries?

The instrument asks whether the middle-component hesitation probability is
higher before a sentence than before a word after controlling mechanics and
typing speed. A pass licenses the timing instrument in its genre; it is not a
new finding about the process pyramid or a personal identification badge.

## Frozen measurement

`week3_pause_inputs` authenticates the complete WB1 input recovery, including
all original source hashes, and joins genre from the original roster's `domain`.
All canonical sessions remain in its census. Its source already excludes
intervals touching suggestions, multi-character insertions, non-user endpoints
and nonpositive intervals. Separators are not sentence boundaries. Deletion
targets remain tagged separately under before-revision; other targets are single
character insertions. Session order is chronological within the original writer,
across genres. Missing within-word support stays explicit.

`week3_pause_model` analyzes each genre separately. It subtracts each writer's
within-word median log interval. The mechanical coefficient is estimated only
from mid-sentence within-word and before-word intervals, using writer and prompt
random intercepts, word location, minutes on task and session order. It removes
that global coefficient from log intervals, then fits exactly three Gaussian
components on log time. Component means order fast, hesitation and disengagement.
There is no duration cutoff or selection of the component count.

The mixture uses a fixed seed of 20261026, initial means at quantiles .2, .65 and
.95, one initialization, a 500-iteration ceiling, tolerance .0001 and covariance
regularization .000001. Nonconvergence or component collapse refuses the result.
The same fixed settings apply in every reference fit.

The primary crossed Gaussian model regresses the middle-component posterior on
categorical boundary location (before-word baseline), the mechanical indicator,
minutes on task and session order, with writer and prompt random intercepts.
The existing certified exact REML solver and original numerical tolerances are
reused. The primary is sentence minus word. Paragraph minus sentence and revision
minus sentence are secondary contrasts from the same fitted model. Location
tables retain hesitation and disengagement probabilities, posterior-weighted
slow durations in original seconds, and skill-adjusted relative durations.

Uncertainty uses 2,000 whole-writer bootstrap draws. Each draw refits typing
normalization, mechanics, mixture and crossed regression. No failed draw is
discarded or redrawn. The primary passes only when the 95% interval lies above
zero. A genre that fails does not license its downstream CoAuthor timing claims.
The packet's ScholaWrite/KLiCKe within-writer fallbacks remain as specified.

## Descriptive hierarchy and identification

The secondary hierarchy profile is the equal-session mean of log geometric
duration ratios between each higher boundary and within-word intervals, after
the frozen global mechanical adjustment. It is distinct from the mixture-based
primary. Subtracting writer typing speed cancels algebraically in every ratio,
so an individual's other half cannot enter its features through a shared speed
baseline. Missing levels remain missing; imputation is gallery-only.

Prompt-disjoint dated halves, split-half Pearson and Spearman-Brown reliability,
fractional ties and the fixed gallery are retained. The corrected WA0.h1 context
reference supplies three disjoint writer roles: context donors, probes and
additional gallery writers. Each original eligible writer is scored once. The
1,000 null assignments shuffle session writer labels within prompt and role,
then rebuild the half profiles. No failed-support draw is replaced. Identity
requires empirical one-sided p below .05 and a positive paired writer interval
for real minus context. A passing timing gradient alone cannot license identity.

## Execution and limits

The ready chain is `week3_pause_inputs`, then `week3_pause_pilot`, then
`week3_pause_instrument` only after counted cost admission. The pilot measures
both genres, five complete bootstrap refits and 100 profile permutations per
genre. It records only workload digests and timings, not pilot scientific scores.
Its projection uses the slowest measured complete bootstrap fit, the unchanged
2,000/1,000 main counts, and full fresh replay. Prior preparation, failures and
pilot charges must be added by the owner under the single **one CPU-hour** cap.

The implementation checks positive and null boundary worlds, exact speed-ratio
invariance, a known mechanical coefficient, missing-mixture/mechanical refusal,
source mutation, corpus count guards, complete native replay and cost-only
replay. All nine focused checks pass, including the absolute-duration output
and explicit refusal to treat a constructed fixture as corpus. Constructed
validation is not a full-corpus result or permission to exceed the cap.

Fresh verification reconstructs all source joins, nuisance fits, mixture fits,
bootstrap contrasts and empirical profile references. Yield/stop checks occur
at completed fit/reference boundaries; an interrupted run recomputes rather
than silently trusting a partial numerical bank. The owner must charge repeated
work and must not restart a cost-held or scientifically failed card.
