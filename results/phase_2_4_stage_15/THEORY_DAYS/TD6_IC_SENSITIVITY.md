# TD6 IC SENSITIVITY

**Hypothesis.** Could the original rare-phrase statistic reliably detect a reduction beyond its practical bar, while avoiding false support under equal underlying rates?

**METHOD.** Reconstruct the original matching and both full human outputs exactly. Condition separately on each population's token counts, matched pairs, subreddit strata and pooled hit probability. Generate independent binomial hit counts with anger probability fixed and disgust probability changed by each registered relative dose. Run 100 worlds at each of five doses for both populations, retaining the original 2,000-draw within-subreddit paired bootstrap and three-way decision rule. Precompute exactly the original resampling multiplicities in the same random-call order; complete original-loop parity and independent native replay verify the implementation. No world or undefined draw is removed.

**Found.** The rare-count calibration has limited sensitivity, and the sparse companion bootstrap is unreliable in these constructed worlds; the human comparison remains inconclusive.

Every cell below reports a count out of 100 constructed worlds and a Wilson 95% interval for that rate. Supports and against mechanically apply the original interval rule relative to a 10% reduction; inconclusive includes invalid intervals. Coverage means that the interval contains the underlying ratio of expected rates used by the generator, not the realized sample ratio. A dose of -10% is the decision boundary and has no high-power requirement.

| Population | Underlying relative rate change | Supports | Against | Inconclusive | Interval coverage |
|---|---:|---|---|---|---|
| Primary matched pairs | +0% | 1/100 [0.18%, 5.45%] | 11/100 [6.25%, 18.63%] | 88/100 [80.19%, 93.00%] | 91/100 [83.77%, 95.19%] |
| Primary matched pairs | -10% | 5/100 [2.15%, 11.18%] | 5/100 [2.15%, 11.18%] | 90/100 [82.56%, 94.48%] | 90/100 [82.56%, 94.48%] |
| Primary matched pairs | -20% | 10/100 [5.52%, 17.44%] | 2/100 [0.55%, 7.00%] | 88/100 [80.19%, 93.00%] | 87/100 [79.02%, 92.24%] |
| Primary matched pairs | -40% | 37/100 [28.18%, 46.78%] | 1/100 [0.18%, 5.45%] | 62/100 [52.21%, 70.90%] | 92/100 [85.00%, 95.89%] |
| Primary matched pairs | +20% | 0/100 [0.00%, 3.70%] | 36/100 [27.27%, 45.76%] | 64/100 [54.24%, 72.73%] | 94/100 [87.52%, 97.22%] |
| Person-targeted companion | +0% | 22/100 [15.00%, 31.07%] | 27/100 [19.27%, 36.43%] | 51/100 [41.35%, 60.58%] | 43/100 [33.73%, 52.78%] |
| Person-targeted companion | -10% | 26/100 [18.40%, 35.37%] | 26/100 [18.40%, 35.37%] | 48/100 [38.46%, 57.68%] | 44/100 [34.67%, 53.77%] |
| Person-targeted companion | -20% | 32/100 [23.67%, 41.66%] | 15/100 [9.31%, 23.28%] | 53/100 [43.29%, 62.49%] | 44/100 [34.67%, 53.77%] |
| Person-targeted companion | -40% | 49/100 [39.42%, 58.65%] | 16/100 [10.10%, 24.42%] | 35/100 [26.36%, 44.75%] | 35/100 [26.36%, 44.75%] |
| Person-targeted companion | +20% | 22/100 [15.00%, 31.07%] | 34/100 [25.46%, 43.72%] | 44/100 [34.67%, 53.77%] | 43/100 [33.73%, 52.78%] |

The primary has 1,437 pairs in 412 subreddits, 94 of them singleton strata. Its pooled construction probability is 0.00174628913559 per lexical token. At a 20% reduction it supports in 10/100 worlds, with rate interval [5.52%, 17.44%], failing the required lower bound of 80%. At equal rates it falsely supports in 1/100, with interval [0.18%, 5.45%], meeting the required upper bound of 10%. Limited sensitivity follows from failed power under this construction, not a claim that the human effect is absent.

The person-targeted companion has 49 pairs in 41 subreddits, 35 singleton strata, and construction probability 0.00363825363825. At equal rates it falsely supports in 22/100 worlds, with interval [15.00%, 31.07%]; at a 20% reduction it supports in 32/100, with interval [23.67%, 41.66%]. Both adequacy criteria fail. At equal rates its nominal interval covers truth in only 43/100 worlds. This demonstrates poor calibration under the declared model and reinforces the original warning against treating the companion's narrow human interval as precise population evidence.

The diagnostics below are counts out of 100 at each dose and population. Zero excluded means an interval lies wholly on either side of zero. A collapsed interval has identical endpoints. Undefined interval includes any nonfinite bootstrap draw; undefined point means the realized anger denominator is zero. All remain in denominators; the companion JSON gives Wilson uncertainty for every diagnostic as well.

| Population | Underlying relative rate change | Zero excluded | Collapsed interval | Undefined interval | Undefined point |
|---|---:|---:|---:|---:|---:|
| Primary matched pairs | +0% | 9/100 | 0/100 | 0/100 | 0/100 |
| Primary matched pairs | -10% | 17/100 | 0/100 | 0/100 | 0/100 |
| Primary matched pairs | -20% | 23/100 | 0/100 | 0/100 | 0/100 |
| Primary matched pairs | -40% | 56/100 | 0/100 | 0/100 | 0/100 |
| Primary matched pairs | +20% | 22/100 | 0/100 | 0/100 | 0/100 |
| Person-targeted companion | +0% | 49/100 | 0/100 | 8/100 | 3/100 |
| Person-targeted companion | -10% | 52/100 | 4/100 | 4/100 | 0/100 |
| Person-targeted companion | -20% | 47/100 | 4/100 | 6/100 | 2/100 |
| Person-targeted companion | -40% | 65/100 | 22/100 | 6/100 | 2/100 |
| Person-targeted companion | +20% | 55/100 | 0/100 | 4/100 | 3/100 |

These conditional worlds hold estimated base rates fixed and assume independent constant-probability token trials. They omit semantic clustering, subreddit rate heterogeneity, author and label dependence, uncertainty in matching and lexical construct coverage. Counts are not asserted to be grammatical texts. The same fixed bootstrap bank is reused as the original seeded procedure would do; world outcomes are independent conditional on that bank. Singleton strata deliberately cannot vary their pair under resampling. The completed human effect estimates, intervals and verdicts remain unchanged and are not replaced by simulated outcomes.

**Means.** The practical-size sensitivity qualifier changes from untested to limited in the stipulated construction. The primary remains inconclusive. The sparse companion remains descriptive and cannot license a mental-modelling claim. This is a completed scientific control failure, not an engineering failure to heal. Retain the original human result and its limited constructed sensitivity; no descendants. Build the other registered theory-days follow-ups within the existing budget and clock. No new tests were harvested from this wake, no p-value is added, and scientific reporting remains in the final packet at drain.

Design commit: `0aff714c38f3d43fa326175b3cc65b1e75d1fbe9`. Full native execution plus independent replay used 33.140625 CPU seconds; all TD6.ic rungs total 66.78125 against 900. Every output hash, source pin, parent output and native exit verifies. All aggregate counts and their intervals were independently recalculated from every retained world. Raw source text and identifiers remain private.
