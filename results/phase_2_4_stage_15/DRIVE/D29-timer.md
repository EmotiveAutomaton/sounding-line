# D29 timer extension: conditional bunching with invalid diagnostics

**Hypothesis.** Sessions may end unusually often just after the task's ten-minute minimum.
**METHOD.** Compare equal-writer duration mass from 600 to 660 seconds with a fixed linear extrapolation from 660 to 900 seconds, using 30-second bins and 2,000 writer bootstraps; retain the fixed duration-bin shuffle and shifted-cutoff diagnostic.
**Found.** The primary bunching contrast is positive, but both diagnostics are invalid because their extrapolated bin masses become negative in resampling. **Means.** The observed bunching is conditional on the linear baseline and lacks a valid result from these controls; it does not identify an internal stopping target.

The table shows excess session share, in percentage points, averaged equally
over 61 writers. The interval is a writer-bootstrap percentile 95% interval.
The probability is an approximate descriptive two-sided Wald reference.

| Complete comparison | Excess, points | 95% interval, points | Probability | State |
|---|---:|---|---:|---|
| Ten-minute boundary | 26.5008 | [16.8378, 36.6859] | 2.02809098e-07 | positive |
| Within-writer duration-bin shuffle | unavailable | unavailable | unavailable | invalid |
| Shifted 780-second cutoff | unavailable | unavailable | unavailable | invalid |

Duration is the last minus first logged event, not an observed finish-button
time. Every writer's histogram denominator includes all their sessions, including
those outside the fitted window. The primary's observed first-minute share is
40.8285%; the extrapolated share is 14.3276%. Negative counterfactual masses
were refused, not clipped; a diagnostic without a valid interval is not a clean
null. The asymmetric right-side baseline is required by the minimum-time task
and is a modeling assumption, not an identified causal counterfactual.

All 37 source/input pins, 1,414 completion hashes, fresh source/statistical
replay and native exit verify. Five targeted tests and actual native known-answer
execution passed. No further extension is opened; required controlled texture
remains. No family reset or mechanism admission is based on this diagnostic.
Theory/TODO integrate at 20:00 PDT. [Aggregate receipt](D29-timer.json).
