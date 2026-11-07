# B4 IC SENSITIVITY

**Hypothesis.** Could the frozen chess pipeline detect a positive interaction at the one-centipawn practical size under a declared conditional error model?

**METHOD.** Retain all 9,912 observed games and 514,787 moves, standardized predictors, instruments and controls. Preserve ordinary-regression nuisance coefficients, set its interaction to zero, and flip the original residual vector by one independent sign per whole game. Generate 100 worlds with seed 20261106. Refit both stages and run 2,000 game-bootstrap draws per zero world. Apply the algebraically exact, independently validated coefficient-and-interval shift at each of five fixed doses. Replay the complete grid in a separate process. All worlds and bootstrap draws remain in their denominators; none is invalid.

**Found.** The chess diagnostic has limited practical-size sensitivity in the registered constructed worlds; the human interaction remains inconclusive.

Every cell below gives a count out of 100 constructed worlds and its Wilson 95% interval for the corresponding rate. Positive and negative zero exclusion mean the entire interaction interval lies on that side of zero; practical-bar clearance requires its lower endpoint above +1. Coverage means the interval contains the planted interaction.

| Planted interaction (centipawns) | Positive zero exclusion | Negative zero exclusion | Clears +1 bar | Coverage of planted value |
|---|---|---|---|---|
| -5 | 2/100 [0.55%, 7.00%] | 10/100 [5.52%, 17.44%] | 2/100 [0.55%, 7.00%] | 93/100 [86.25%, 96.57%] |
| +0 | 3/100 [1.03%, 8.45%] | 4/100 [1.57%, 9.84%] | 2/100 [0.55%, 7.00%] | 93/100 [86.25%, 96.57%] |
| +1 | 4/100 [1.57%, 9.84%] | 4/100 [1.57%, 9.84%] | 3/100 [1.03%, 8.45%] | 93/100 [86.25%, 96.57%] |
| +5 | 11/100 [6.25%, 18.63%] | 1/100 [0.18%, 5.45%] | 9/100 [4.81%, 16.23%] | 93/100 [86.25%, 96.57%] |
| +10 | 33/100 [24.56%, 42.69%] | 0/100 [0.00%, 3.70%] | 28/100 [20.14%, 37.49%] | 93/100 [86.25%, 96.57%] |

The following table applies the original three-way human decision rule mechanically to each constructed world. Each cell again reports count out of 100 and Wilson 95% rate interval. These labels classify ruler worlds, not additional human findings.

| Planted interaction (centipawns) | Supports | Against | Inconclusive |
|---|---|---|---|
| -5 | 2/100 [0.55%, 7.00%] | 10/100 [5.52%, 17.44%] | 88/100 [80.19%, 93.00%] |
| +0 | 2/100 [0.55%, 7.00%] | 4/100 [1.57%, 9.84%] | 94/100 [87.52%, 97.22%] |
| +1 | 3/100 [1.03%, 8.45%] | 4/100 [1.57%, 9.84%] | 93/100 [86.25%, 96.57%] |
| +5 | 9/100 [4.81%, 16.23%] | 1/100 [0.18%, 5.45%] | 90/100 [82.56%, 94.48%] |
| +10 | 28/100 [20.14%, 37.49%] | 0/100 [0.00%, 3.70%] | 72/100 [62.51%, 79.86%] |

At +1, positive zero exclusion occurs in 4/100 worlds, with rate interval [1.57%, 9.84%]. Its lower bound is below the frozen 80% adequacy criterion. Null worlds exclude zero in either direction in 7/100 cases, with interval [3.43%, 13.75%]; the upper bound also fails the required at-most-10% calibration bound. That second failure does not prove excess false positives: its uncertainty includes 5%. Both predeclared adequacy requirements fail. The label is limited in this construction. Clearing a strict +1 threshold when truth is exactly +1 is a different event and is not the sensitivity adequacy criterion. Larger-dose detection remains limited; the complete grid and count uncertainty are retained.

This is a conditional linear-model calibration. Whole-game signs preserve within-game residual patterns but assume independent sign-symmetric game errors, with no cross-game dependence for repeated players. Generated quality may exceed zero and does not represent invented legal chess. Fixed instruments passing their numerical strength gate do not validate exclusion: real clock pressure may directly change quality. Parent bootstrap draws with weak but nonsingular instruments remain included. No score, threshold, sample, control or model was tuned after these outcomes.

**Means.** The original human interval and inconclusive verdict remain unchanged. Sensitivity is now tested and limited under the stipulated construction, replacing the earlier untested qualifier; no equivalence, human negative, causal multiplication or biological claim follows. Numerical implementation passes, but the practical-sensitivity admission criterion does not. Preserve the original human comparison and conditional sensitivity limits; no descendant follow-ups. Continue separately registered theory-days cards within the original budget and clock. No tests were harvested from this operational wake. Final scientific reporting remains at drain.

Design commit: `456b6e753f07c319c806ffebb2c06974e81b3897`. Execution and full independent replay used 394.625 CPU seconds; all B4.ic rungs total 404.1875 seconds against 3,600. Every output and input pin, all native exits, and independently recomputed aggregate counts and Wilson intervals verify. No p-value is added. The generic result configuration's constructed flag is false because the predictor source is observed; the calibrated outcomes are explicitly constructed, as stated in the dedicated calibration output and this record. No raw moves or identities are published.
