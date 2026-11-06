# WEEK4 WD1 CALIBRATION COST HOLD 20261104

**Hypothesis.** Can the complete sensitivity calibration fit its remaining allowance without changing the instrument?

**METHOD.** Independently replay the complete four-family timing prefix and apply its frozen slower-pass, full-bank, factor-three forecast. Check a separately implemented zero-column Newton optimization against the original full solver and downstream profiles. Preserve the first failure and repeat once after retaining the original full-shape likelihood, gradient, Hessian and line search.

**Found.** The corrected sensitivity calibration is cost-held; two exact-solver candidates fail their frozen profile-parity check and remain unadmitted.

The forecast is 94007.812500 CPU seconds against 56102.609375 remaining before further human work. No full calibration launched. The first compressed likelihood implementation differed in a downstream profile by approximately1.534e-9; the first repair that compressed only the Newton solve differed by approximately7.466e-9. Both exceed the unchanged1e-9 profile-parity limit. Other derivative checks and native handler checks do not override this failure. The source, both failed test receipts and the original invalid human run remain retained. No human effect was scored from any reference subset.

**Means.** Retain the cost and instrument holds. A separately frozen single-thread timing pass may measure the identical h2 code because small matrix operations may incur thread overhead; it must use the same forecast formula and fresh independent replay, retain every earlier charge and remain within the same allowance. No speed-up, calibration pass or scientific inference is claimed. No paid call, delegation, gear change or new scientific hypothesis occurred.
