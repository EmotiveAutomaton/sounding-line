# TR4: six strictly prospective handling forecasts

This implements the commissioned Week 3 TR4 comparison from the independently
verified handling census. It does not resume TR3 or its held validation.
The original 3,600 CPU-second cap, prior charge of 98.1875 seconds and one
card-wide engineering repair already used remain. No GPU, paid call, delegation
or new holdout access is required. All results are descriptive.

DESIGN CHECK: method LESSONS sections 3–5 and CONTROLS reread October 27.
Known equal shares must produce equal predictions and exactly zero paired gain.
Predictions must be unchanged by edits to the current or future target. A
constructed persistent change must favor adaptive over whole-history forecasts;
a stable record must not produce an invented adaptive advantage. Invalid counts,
incomplete census, ambiguous history, absent observations and insufficient
independent writers retain explicit unsupported states. These checks validate
instruments, not the human hypotheses.

## Population, chronology and scoring

Retain every session and the original WB1 writer split. The commissioned
eligibility floor is twelve recorded sessions per writer. The last third starts
at index floor(2n/3) in chronological storage order. A target is only scoreable
if it and its entire preceding history are strictly ordered, with each previous
end less than the next start. Touching/overlapping histories are unsupported,
not silently ordered by an identifier. Preserve their rows and exclusion reason.
Zero usable menus are missing observations; retain them, and do not invent a
four-class decision. Every comparator scores the identical supported target set.

Each session supplies canonical accept, edit, dismiss and ignore counts. For
filter observations use shares (count + 0.5)/(total + 2), with accept as the
additive-log-ratio base. Score the raw observed counts against the forecast
probabilities before updating, in nats per observed choice. Give sessions equal
weight within writer and test writers equal weight. The primary is whole-history
loss minus adaptive Kalman loss on test writers' final thirds. Discovery targets
are used only for selecting the exponential rate and change-point hazard.

## Frozen model definitions

- Whole-history mean: equal mean of earlier observed sessions' smoothed shares.
- Last-session forecast: the last earlier observed session's smoothed shares.
- Exponential mean: recursively update smoothed shares with a rate selected from
  0.01, 0.05, 0.1, 0.25, 0.5, 0.75 and 1 on discovery final-third log loss;
  smaller rates win exact ties. Initialize from the first observed session.
- Adaptive Kalman: a three-dimensional Gaussian local level in additive log
  ratios. The observation covariance has diagonal 1/(class count + 0.5) plus
  1/(accept count + 0.5) in every entry, a declared delta-method approximation.
  Initialize mean zero and covariance 10I. Process covariance is qI per recorded
  session. Select q independently at each forecast by the cumulative Gaussian
  predictive likelihood of that writer's earlier observations, from
  0, 0.0001, 0.001, 0.01, 0.1 and 1; smallest q wins ties. Maintain every grid
  filter in parallel so this is exact prefix fitting, not repeated optimization.
- Local linear trend: three levels plus three slopes. One-session transition
  adds slope to level; start levels and slopes at zero with covariance 10I and I
  respectively. Integrated slope-noise covariance is
  q times [[I/3, I/2], [I/2, I]]. Select q by the same prefix-only likelihood grid.
  Both Gaussian models map forecast mean log ratios back to four probabilities;
  this is a plug-in forecast, not exact logistic-normal integration.
- Bayesian online change point: categorical Dirichlet counts with prior 0.5 in
  each class; exact Dirichlet-multinomial session likelihood; constant hazards
  0.01, 0.025, 0.05, 0.1 and 0.2, selected on discovery final-third log loss.
  Keep every run length, including the prior reset branch; no pruning.
  Prediction precedes update. This follows the recursive run-length formulation
  of [Adams and MacKay, sections 1–2.3](https://arxiv.org/html/0710.3742v1), read
  October 27. Its categorical observation model is this implementation's choice.

A writer with no earlier observed choices has no scoreable forecast. Uniform
initial states are retained for instrument checks, never counted as an observed
personal history. Unknown menu classes do not enter any count denominator.

## Remaining admission work

The full comparison still requires all six constructed/native checks, completed
source binding, two thousand paired writer bootstraps, two hundred within-writer
outcome permutations with histories rebuilt, and the packet's complete
writer-reassignment controls. Volatility split-half reliability additionally
requires one thousand writer-label permutations within prompt and a real-writer
paired uncertainty calculation. Reference semantics, complete calibration and
whole-design cost admission must be frozen and validated before a human result
is computed. This initial model build does not waive any of those gates.
