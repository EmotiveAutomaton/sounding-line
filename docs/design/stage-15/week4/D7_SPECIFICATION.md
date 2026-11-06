# D7.s fixed-penalty duration specification curve

This implements the first-generation follow-up already registered after
S15-W4-D7-H1-HUMAN-20261104. It asks whether the held-out prediction reversal
depends on choosing a penalty separately for the baseline and novelty model.
No literature novelty is claimed; this is the registered robustness check of
the existing D7 estimator, not a new psychological test.

**Case and check.** Retain all 61 writers in the census and exactly the original
38 supported writers in every fit. Keep completed durations, elapsed-time
covariates, acceptance adjustment, chronological partitions, training-only
standardization, equal session weighting and equal writer weighting. Fit each
original ridge penalty (0.001, 0.01, 0.1), common to the baseline and augmented
model, without choosing among the three results. The primary object is the
complete three-row curve of held-out squared-log-duration loss gains. Positive
gain means better prediction; it does not mean longer examination.

For each row retain 2,000 paired writer resamples and all 200 original joint
duration/acceptance shuffles and 200 D7.h1 conditional session assignments.
Rebuild transforms and fits for every reference. The complete metadata bank
must preserve the original supported roster before fitting. Fake writers can
preserve population prediction and are not an individual-signal null.
Undefined or missing fits invalidate the whole bank, with no successful-only
probability. The original invalid unconditional assignments remain preserved.
Within-writer fits make resampling complete fitted writer units exactly equal
to duplicated-writer refits; validate this identity explicitly.

**DESIGN CHECK.** LESSONS sections 3–5 and CONTROLS sections 1–7 reread
2026-11-04. Constant responses must produce exact zero gain at every penalty.
Signed novelty must predict in either direction with the correct coefficient
sign. Native validation compares every fitted quantity with the original
single-penalty primitive exactly and coefficients with an independent augmented
least-squares oracle within 1e-10. Held-out response mutations must leave
training fits and predictions unchanged. Altered bindings, support, incomplete
banks and failed calibration refuse admission rather than becoming nulls.

Complete calibration uses the parent's thirty worlds: ten null, ten nuisance,
five positive and five negative, each with twelve writers, all 401 fitted arms
and 2,000 paired resamples. Each penalty separately retains the original
positive-gain gate: lower interval above zero, joint-reference positive-tail
probability at most .05, and reference mean at most .005. Each penalty must
have at most one false call in each ten-world null/nuisance group, at least four
detections in each five-world signed group and the correct coefficient signs.
Any row failing holds the entire human curve; no selective penalty admission.
This is constructed calibration, not empirical human power. Human zero-crossing
intervals remain not detected with sensitivity untested; negative intervals
describe prediction harm. All results are descriptive and create no descendants.

**Cost and smaller route.** The original follow-up ceiling is 1,800 CPU seconds,
including 60 seconds reserved for local checks, native validation, both cost
probes, all calibration, human execution, failures and fresh replay. No smaller
writer roster or shortened bank is authorized. Cost mode replaces all observed
duration and acceptance responses with a fixed generated response before any
fit. Include all 38 supported writers and the two conditional assignments with
the largest maximum writer row count. Calibration timing uses three twelve-writer
worlds and two references per family. Forecast both full workloads from the
slower independent phase, using the larger of whole-work and worst-writer
estimates and the original factor-three margin. Charge input authentication
and complete support-bank reconstruction once per phase; scale only fitted
work by the full arm/world count. Measure retained bytes too. Admit complete
calibration plus human forecast together only if they fit the remaining shared
allowance; otherwise record a cost hold, preserving the parent and all charges.

Completed fitted-arm checkpoints bind the exact source and configuration.
Fresh verification ignores their computational contents, rebuilds every arm,
and compares exact serialized records. Historical source modules are unchanged.
No GPU, paid provider, external transfer or new agent is used.
