# D7.m: temporal stability of the novelty coefficient

This implements the separately registered first-generation descriptive probe
after S15-W4-D7-H1-HUMAN-20261104. Does the fitted association between option
novelty and completed menu duration transport from earlier to later sessions?
It may help characterize the parent's prediction reversal; it cannot identify
examination, causal attention or why a writer behaves as she does. This is the
registered estimator diagnostic, with no new literature or novelty claim.

**Case and check.** Preserve the original 61-writer census and its exact 38
supported writers, completed durations, elapsed costs, acceptance covariate,
60/20/20 chronological partitions, equal session weighting and writer weighting.
Use the augmented duration/elapsed model. Standardize and define prompt columns
on training rows only; choose among the original three ridge penalties on the
calibration partition, exactly as in the parent. Fit later-session coefficients
with those SAME columns, transforms and selected penalty. Never reselect on
later outcomes. Compare the last coefficient, in training-standard-deviation
units of novelty: later minus earlier, with its equally weighted writer mean
and 2,000 complete paired writer resamples. Report the signed Pearson correlation
of earlier and later coefficients alongside that difference, with the same
resamples. No absolute-value correlation, new predictive performance estimate
or independent replication claim. Undefined correlations remain undefined;
if any resampled correlation is undefined, its interval is withheld and that
count reported, without dropping draws. The coefficient-difference interval
remains available when its own full denominator is valid.

Retain all 200 original within-writer joint duration/acceptance shuffles and
200 D7.h1 conditional session-owner assignments. Before fitting, every assigned
bank must preserve the exact original supported roster. Rebuild transforms,
penalty selection and both fits for every arm. Report the complete reference
means and two-sided joint-reference tail probability of the mean difference,
using the plus-one rule. The conditional writer bank is descriptive: population
associations can survive reassignment. A joint-reference mean with magnitude
above .005 is flagged as biased; it cannot license a directional call. No
successful-only bank or correlation filtering is allowed. The observed result
is descriptive regardless of its interval or probability and creates no children.

**DESIGN CHECK.** LESSONS sections 3–5 and CONTROLS sections 1–7 reread
2026-11-04, alongside the G215/G225 section and correction history. Constant
responses must give exact zero coefficients and zero change; their correlation
must be undefined. An independently solved augmented least-squares system must
match both fitted coefficient vectors within 1e-10; training coefficients and
selected penalty must equal the parent's augmented fit exactly. Mutating only
later responses must leave training transforms, coefficients and selection
unchanged. Signed coefficient-pair fixtures must return correlations +1 and -1.
Duplicated-writer refits must equal complete fitted-unit resampling. Exercise
actual handler replay, reentry, corrupt checkpoints, changed pins, changed
support and incomplete reference refusal.

Complete constructed calibration uses 30 worlds of 12 writers with ten sessions
and twelve menus per session: ten stationary, ten stationary nuisance-confounded,
five upward and five downward coefficient shifts. Every writer repeats the same
covariate template across sessions, so partition-size and design shifts cannot
manufacture coefficient drift. Earlier slopes vary from -.8 to .8 across writers;
shifted worlds add +.8 or -.8 only in the final two sessions. Nuisance worlds have
novelty correlated with elapsed time but a stable elapsed-time response law.
These are algebraic calibration worlds, not empirical power estimates. Every
world has all 401 fitted arms and 2,000 resamples. Stable worlds must retain a
mean change within 1e-10 and at most one false directional call per ten-world
group. At least four of five worlds in each signed group must have the correct
directional interval and joint-reference probability at most .05, with no
reference-bias flag. Exact coefficient relationships are also tested separately
on unregularized-coordinate fixtures; no human interpretation follows from
passing the constructed gate. Failed calibration holds the entire human probe.

**Cost and smaller route.** Original shared ceiling 1,800 CPU seconds includes
60 seconds reserved for local checks, native validation, both cost probes,
complete calibration, full human execution, failures and independent replay.
No reduced roster, shortened bank or larger allowance. Cost mode replaces
human duration/acceptance with the parent's fixed generated responses before
any fit and includes all 38 supported writers and the two worst original
conditional assignments by maximum writer row count. Time a three-world
calibration prefix. Forecast both passes from the slower complete phase with
factor three and the maximum of whole-work and worst-writer extrapolations;
authentication/support construction is charged once per phase, and the inherited
60-second per-phase overhead margin is retained. Measure retained output bytes.
Admit complete calibration and human forecasts together only when they fit the
remaining allowance. Otherwise retain preparation and record a cost hold.
No GPU, API request, new delegation or locked holdout is used.
