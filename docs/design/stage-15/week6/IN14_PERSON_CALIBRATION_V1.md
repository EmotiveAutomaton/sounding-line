# IN14 person correction: prospective constructed qualification

This is a candidate instrument, not an admitted human secondary. Owner review
approved this specification and its fixed gates before the constructed run.
The main IN14 primary and other packet secondaries have independent readiness.

## DESIGN CHECK

LESSONS sections 2/3 and CONTROLS sections 6/7 apply. The case is estimation of
writer-specific prompt carry-over from overlapping adjacent surveys. The check
is nine complete constructed worlds and a hand-known shared-boundary sentinel.
A failure leaves this correction held; neither a changed noise family nor a
relaxed tolerance can admit it. The smaller route is the already prepared
uncorrected descriptive coefficients, without a corrected person claim.

## Authority and population

Week 6 PACKET.md line 69: “The person: for writers with four or more pairs, TR1's
recipe on her own coefficient, and its relation to the two emotional-stability
items. Lowercase evidence.” The primary at line 63 uses under-ten-minute pairs.
Use that same under-ten-minute population, at least four retained pairs per
writer, raw chronological pair order established before exclusions. Do not
compress missing raw pair ordinals. Long-lag reach stays separate. Split halves
are a within-session diagnostic (where session membership is unobserved), never
consecutive-play or longitudinal replication.

TR1's source is week5/TR1_BACK_HALF.md and week5_tr1_math.py: residual_noise,
play_table, stability and choose_calibration. Its sampling correction subtracts
mean coefficient sampling variance from observed between-person variance;
reliability is corrected variance divided by observed variance. Original TR1
then divides a consecutive-play correlation by the square root of the two
reliabilities. Its three correlation plants are 0, 0.5 and 1 with tolerance 0.1.
Its scalar numerator assumes no cross-play sampling covariance. Adjacent IN14
pairs can share a survey, so that assumption is not imported.

## Exact candidate

Fit full and chronological left/right halves separately per writer: intercept,
baseline, first-prompt, other-same-valence and second-prompt indicators. A
rank-deficient full or half fit refuses the correction, not a silently dropped
writer. Pool full-fit residual lag-one products across consecutive raw pair
ordinals and feelings, dividing by the corresponding preceding squared
residuals. Record raw phi and truncate only nuisance phi to [-0.95,0.95], as TR1
does. The pooled eleven-feeling residual correlation matrix is obtained from
the weighted residual cross-product with its diagonal standardized to one.

For writer i, R_i is phi raised to raw pair-ordinal distance, Kronecker-multiplied
by the pooled feeling correlation. Estimate sigma_i squared by residual SSE /
trace((I-H_i) R_i). The full and embedded half prompt-coefficient linear maps
form W_i; joint sampling covariance is sigma_i squared W_i R_i W_i transpose.
Production uses Kronecker contractions; an independent reference forms the
full matrix, pseudoinverse and projection matrix explicitly.

Full reliability is (Var(full coefficient) - mean sampling variance) /
Var(full coefficient). The half diagnostic is
(Cov(left,right) - mean sampling covariance(left,right)) divided by the square
root of the two corrected half variances. All corrected ratios are unclipped.
Nonpositive observed or corrected variance refuses the affected correction.
At least two independent writers are necessary. Failure of any included writer
fit is visible and refuses aggregate correction. With missing inventory pairs,
the trait relation uses the complete, unique-inventory writer subset and its
own full reliability. It divides observed coefficient/N correlation by the
square root of coefficient reliability only. It assumes no invented inventory
reliability. N is the already declared IN12 low-emotional-stability composite
(anxious + 8 - calm)/2; high N means lower emotional stability.

If qualified, every one of 2,000 whole-writer bootstrap draws must recompute
pooled nuisance parameters and all corrected moments. No independent feeling
or pair resampling; no failed-draw replacement. Until qualification and complete
run/replay integration, the human handler emits an explicit instrument hold.

## Frozen worlds and gates

Seed 20261115. At each correlation 0, 0.5 and 1, construct 600 writers, with
4/8/12 adjacent pairs equally represented, eleven feelings, six-minute gaps.
Within each pair-count stratum construct centered orthogonal coefficient
vectors so half coefficients have SD 0.6 and exactly the stated correlation;
their mean is the planted full coefficient. Construct an observed inventory
composite correlated 0.4 with that full coefficient. No inventory measurement
error is posited. The full fit may see differing half coefficients; its recovery
must pass without replacing the target after viewing its output.

Generate whole survey trajectories first, then derive the adjacent pair rows.
Prompts cycle through a seeded permutation of all eleven feelings, with no
consecutive repeat. The latent recurrence has baseline coefficient 0.6,
other-same-valence coefficient 0.2 and next-prompt coefficient 0.15. Noise has
unit marginal variance and within-survey common-feeling correlation 0.35.
The three noise families at every target are: IID recurrence innovations;
stationary AR(1)=0.4 recurrence innovations; and deterministic latent recurrence
with independent unit-variance survey measurement noise. The last induces
eta[t+1] - 0.6 eta[t] residuals and shared-boundary dependence that is not AR(1).
Initial latent survey ratings are independent unit normals; these constructed
ratings are unbounded, not clipped or passed off as source-scale observations.

Every one of the nine corrected half correlations must be within 0.1 of its
plant and every adjusted coefficient/N relation within 0.1 of 0.4. A refusal or
nonfinite value fails its world. Preserve all worlds even after the first
failure. There is one candidate; no estimator selection after seeing results.

The exact sentinel has observed half variances 2/2 and covariance 1, sampling
variances 1/1 and sampling covariance 1: corrected half correlation is zero
(the independent-error numerator would give one). Full variance is 1.5,
sampling variance 1, true variance 0.5 and reliability 1/3. Its raw trait
correlation is 0.4/sqrt(3), and corrected relation 0.4. A zero corrected-variance
case must refuse. Dense-reference covariance and coefficient parity tolerance
is 1e-8, including the actual shared boundary. A fixture with an excluded middle
survey verifies that raw ordinal distances do not collapse.

Estimated first suite cost before measurement: 30-90 wall seconds, two numerical
threads, hard 180-second bound on the complete identified test process tree.
All source bytes, command, world reports, exits, failed gates and resource
receipts remain retained. This is the packet fixture under Q/U/AA, not a separate
mandatory native qualification campaign or a source requalification.
