# TD5 IC SENSITIVITY

**Hypothesis.** Can the entire registered six-pair disagreement rule distinguish uniform independent labels from a planted within-channel advantage and its reversal at the declared practical scale?

**METHOD.** Generate 100 independent constructed worlds at each of four frozen contrasts, each containing 37,335 comments with three distinct single-label raters. Use balanced marginal probabilities over the original fourteen assigned labels and a declared mixture that analytically produces all six within-minus-strongest-rival contrasts. Recompute the original expected-count eligibility, canonical strongest-rival selection and 2,000 whole-comment bootstrap draws in every world. Retain the original fixed-rival interval and the maximum-reselected companion, the 0.1 point threshold, and the full six-pair rule. Grouping identical comment patterns preserves the empirical whole-comment bootstrap law, with a prospectively declared change of random stream. Full fresh-process replay and an independent recount of every retained world validate the record.

**Found.** The complete disagreement rule has limited sensitivity and poor interval coverage in the balanced constructed worlds; the human comparison remains inconclusive.

The table gives the true constructed lift contrast, the rival rule and the full packet's decisions. Every rate is a count out of 100 worlds with a Wilson 95% interval. Supports requires all six pair wins; against requires at least three pair losses. Either decisive verdict is their sum. Fixed chooses the full-world rival once; reselected recomputes the maximum within the same eligible pool on every bootstrap draw.

| True contrast | Rival rule | Supports | Against | Inconclusive | Either decisive verdict |
|---|---|---|---|---|---|
| +0 | fixed | 0/100 [0.00%, 3.70%] | 1/100 [0.18%, 5.45%] | 99/100 [94.55%, 99.82%] | 1/100 [0.18%, 5.45%] |
| +0 | reselected | 0/100 [0.00%, 3.70%] | 1/100 [0.18%, 5.45%] | 99/100 [94.55%, 99.82%] | 1/100 [0.18%, 5.45%] |
| +0.1 | fixed | 0/100 [0.00%, 3.70%] | 0/100 [0.00%, 3.70%] | 100/100 [96.30%, 100.00%] | 0/100 [0.00%, 3.70%] |
| +0.1 | reselected | 0/100 [0.00%, 3.70%] | 0/100 [0.00%, 3.70%] | 100/100 [96.30%, 100.00%] | 0/100 [0.00%, 3.70%] |
| +0.2 | fixed | 68/100 [58.34%, 76.33%] | 0/100 [0.00%, 3.70%] | 32/100 [23.67%, 41.66%] | 68/100 [58.34%, 76.33%] |
| +0.2 | reselected | 64/100 [54.24%, 72.73%] | 0/100 [0.00%, 3.70%] | 36/100 [27.27%, 45.76%] | 64/100 [54.24%, 72.73%] |
| -0.2 | fixed | 0/100 [0.00%, 3.70%] | 100/100 [96.30%, 100.00%] | 0/100 [0.00%, 3.70%] | 100/100 [96.30%, 100.00%] |
| -0.2 | reselected | 0/100 [0.00%, 3.70%] | 100/100 [96.30%, 100.00%] | 0/100 [0.00%, 3.70%] | 100/100 [96.30%, 100.00%] |

Both rules meet the predeclared null-error requirement: one decisive result in 100 at zero has upper Wilson bound 5.45%, below 10%. Both detect the -0.2 reversal in all 100 worlds, with lower bound 96.30%, above 80%. Neither meets the positive-sensitivity requirement at +0.2: fixed supports in 68/100, lower bound 58.34%, and reselected in 64/100, lower bound 54.24%, both below 80%. All three requirements must pass, so both are limited in this construction. At the +0.1 boundary neither yields full-packet support; this dose had no high-power requirement.

The following complete pair diagnostics use the same 100 worlds per row. Wins, losses and inconclusive are counts; coverage is the count of nominal 95% intervals containing the known population contrast with Wilson uncertainty. Bias is mean estimated contrast minus that truth in lift units. All pair uncertainties are finite and all assigned rivals supported in every world: invalid, undefined and unsupported counts are zero throughout. The aggregate JSON retains Wilson intervals for every decision and diagnostic count, including these zeros. Unassigned labels are absent by construction and their separate comparison is explicitly unsupported, never imputed as zero.

| True contrast | Rival rule | Emotion pair | Wins | Losses | Inconclusive | Coverage | Mean point bias |
|---|---|---|---:|---:|---:|---|---:|
| +0 | fixed | anger / annoyance | 0 | 11 | 89 | 74/100 [64.63%, 81.60%] | -0.059631 |
| +0 | fixed | fear / nervousness | 0 | 9 | 91 | 76/100 [66.77%, 83.31%] | -0.057376 |
| +0 | fixed | grief / sadness | 0 | 5 | 95 | 74/100 [64.63%, 81.60%] | -0.054995 |
| +0 | fixed | amusement / joy | 0 | 13 | 87 | 69/100 [59.37%, 77.22%] | -0.062129 |
| +0 | fixed | curiosity / excitement | 0 | 5 | 95 | 77/100 [67.85%, 84.16%] | -0.055198 |
| +0 | fixed | caring / love | 0 | 5 | 95 | 76/100 [66.77%, 83.31%] | -0.051512 |
| +0 | reselected | anger / annoyance | 0 | 11 | 89 | 29/100 [21.01%, 38.54%] | -0.059631 |
| +0 | reselected | fear / nervousness | 0 | 9 | 91 | 35/100 [26.36%, 44.75%] | -0.057376 |
| +0 | reselected | grief / sadness | 0 | 5 | 95 | 33/100 [24.56%, 42.69%] | -0.054995 |
| +0 | reselected | amusement / joy | 0 | 13 | 87 | 31/100 [22.78%, 40.63%] | -0.062129 |
| +0 | reselected | curiosity / excitement | 0 | 5 | 95 | 35/100 [26.36%, 44.75%] | -0.055198 |
| +0 | reselected | caring / love | 0 | 5 | 95 | 37/100 [28.18%, 46.78%] | -0.051512 |
| +0.1 | fixed | anger / annoyance | 3 | 0 | 97 | 82/100 [73.33%, 88.30%] | -0.052296 |
| +0.1 | fixed | fear / nervousness | 1 | 0 | 99 | 78/100 [68.93%, 85.00%] | -0.057850 |
| +0.1 | fixed | grief / sadness | 6 | 0 | 94 | 76/100 [66.77%, 83.31%] | -0.055912 |
| +0.1 | fixed | amusement / joy | 5 | 0 | 95 | 76/100 [66.77%, 83.31%] | -0.060549 |
| +0.1 | fixed | curiosity / excitement | 8 | 0 | 92 | 78/100 [68.93%, 85.00%] | -0.052456 |
| +0.1 | fixed | caring / love | 3 | 0 | 97 | 75/100 [65.70%, 82.45%] | -0.059062 |
| +0.1 | reselected | anger / annoyance | 3 | 0 | 97 | 43/100 [33.73%, 52.78%] | -0.052296 |
| +0.1 | reselected | fear / nervousness | 1 | 0 | 99 | 38/100 [29.10%, 47.79%] | -0.057850 |
| +0.1 | reselected | grief / sadness | 6 | 0 | 94 | 36/100 [27.27%, 45.76%] | -0.055912 |
| +0.1 | reselected | amusement / joy | 5 | 0 | 95 | 30/100 [21.89%, 39.58%] | -0.060549 |
| +0.1 | reselected | curiosity / excitement | 8 | 0 | 92 | 46/100 [36.56%, 55.74%] | -0.052456 |
| +0.1 | reselected | caring / love | 3 | 0 | 97 | 38/100 [29.10%, 47.79%] | -0.059062 |
| +0.2 | fixed | anger / annoyance | 90 | 0 | 10 | 76/100 [66.77%, 83.31%] | -0.057596 |
| +0.2 | fixed | fear / nervousness | 93 | 0 | 7 | 82/100 [73.33%, 88.30%] | -0.055666 |
| +0.2 | fixed | grief / sadness | 95 | 0 | 5 | 85/100 [76.72%, 90.69%] | -0.053003 |
| +0.2 | fixed | amusement / joy | 85 | 0 | 15 | 76/100 [66.77%, 83.31%] | -0.060188 |
| +0.2 | fixed | curiosity / excitement | 94 | 0 | 6 | 86/100 [77.86%, 91.47%] | -0.046537 |
| +0.2 | fixed | caring / love | 96 | 0 | 4 | 81/100 [72.22%, 87.49%] | -0.057894 |
| +0.2 | reselected | anger / annoyance | 89 | 0 | 11 | 40/100 [30.94%, 49.80%] | -0.057596 |
| +0.2 | reselected | fear / nervousness | 90 | 0 | 10 | 45/100 [35.61%, 54.76%] | -0.055666 |
| +0.2 | reselected | grief / sadness | 95 | 0 | 5 | 42/100 [32.80%, 51.79%] | -0.053003 |
| +0.2 | reselected | amusement / joy | 84 | 0 | 16 | 40/100 [30.94%, 49.80%] | -0.060188 |
| +0.2 | reselected | curiosity / excitement | 94 | 0 | 6 | 51/100 [41.35%, 60.58%] | -0.046537 |
| +0.2 | reselected | caring / love | 96 | 0 | 4 | 34/100 [25.46%, 43.72%] | -0.057894 |
| -0.2 | fixed | anger / annoyance | 0 | 100 | 0 | 94/100 [87.52%, 97.22%] | -0.012127 |
| -0.2 | fixed | fear / nervousness | 0 | 100 | 0 | 92/100 [85.00%, 95.89%] | -0.017209 |
| -0.2 | fixed | grief / sadness | 0 | 100 | 0 | 97/100 [91.55%, 98.97%] | -0.019167 |
| -0.2 | fixed | amusement / joy | 0 | 100 | 0 | 98/100 [93.00%, 99.45%] | -0.019018 |
| -0.2 | fixed | curiosity / excitement | 0 | 99 | 1 | 91/100 [83.77%, 95.19%] | -0.017857 |
| -0.2 | fixed | caring / love | 0 | 100 | 0 | 96/100 [90.16%, 98.43%] | -0.017711 |
| -0.2 | reselected | anger / annoyance | 0 | 100 | 0 | 94/100 [87.52%, 97.22%] | -0.012127 |
| -0.2 | reselected | fear / nervousness | 0 | 100 | 0 | 90/100 [82.56%, 94.48%] | -0.017209 |
| -0.2 | reselected | grief / sadness | 0 | 100 | 0 | 93/100 [86.25%, 96.57%] | -0.019167 |
| -0.2 | reselected | amusement / joy | 0 | 100 | 0 | 93/100 [86.25%, 96.57%] | -0.019018 |
| -0.2 | reselected | curiosity / excitement | 0 | 99 | 1 | 91/100 [83.77%, 95.19%] | -0.017857 |
| -0.2 | reselected | caring / love | 0 | 100 | 0 | 94/100 [87.52%, 97.22%] | -0.017711 |

The positive and zero constructions contain tied population rivals. At zero, pair interval coverage is only 69% to 77% for fixed rivals and 29% to 37% for reselected rivals. Mean null point bias ranges from -0.062129 to -0.051512. Thus passing the packet's null-decision threshold does not establish nominal interval coverage. Maximum reselection does not repair coverage in this construction. These diagnostics support the original warning that the strongest-rival bootstrap is not guaranteed valid near tied maxima. At +0.2, fixed-pair wins range from 85 to 96 while the conjunction wins only 68 times; individual-pair recovery does not substitute for the registered full rule.

The worlds omit actual label imbalance, multilabel annotation, reused raters, comment heterogeneity and adaptive additional ratings. They calibrate the rule on a simple declared population, not the power of either human cohort. The comment count matches the original exactly-three-rater companion; no real author field or new human text is read. All worlds and pairs remain in the denominators. The original human points, intervals and outcomes remain unchanged. This is a scientific instrument limitation, not a crash or arithmetic failure to heal; no estimator or mapping is changed after outcomes.

**Means.** Replace the untested-sensitivity qualifier with this limited constructed calibration while retaining the human inconclusive result and its scope. Retain the human comparison and the complete constructed calibration; no descendants. Reconcile the remaining source-held primary and backlog cards inside the existing campaign bounds. No new tests were harvested from this wake. No p-value is added. Scientific reporting remains in the final packet at drain.

Design commit `396c0c3e531c0c70be771c584c8356aea0047790`. Full execution and independent replay used 124.1875 CPU seconds; all TD5.ic rungs total 131.828125 against 900. Every output hash, source pin and native exit verifies. All aggregate decisions, biases, intervals and adequacy flags were independently checked against the retained complete-world records. The original pinned receipt stays byte-identical.
