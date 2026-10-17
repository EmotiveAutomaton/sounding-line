# V1: outcome-prediction calibration of the unchanged Phase 0 pipeline

DESIGN CHECK: LESSONS 3–5 and reader reliability/admissibility reread October 16.
Under the zero injection, generating probabilities equal the saved population
forecast exactly and oracle injected gain is zero. Positive accept-logit offsets
increase accept probability only for the assigned writers. Future/unresolved
outcomes cannot enter a lag. A changed natural label cannot change a simulated
world. These controls run before the finite grid.

This is the Phase 0 arm of V1 only, on all 1,399 retained sessions. The Stage 14
text/adaptation and D16 process-identity arms require distinct null constructions
and are not authorized by this arm's outcome redraw. No model or provider calls.
Successful recovery here cannot establish that weak human effects are genuine
or that a different instrument is sufficiently sensitive.

## Frozen construction and fit

Use the complete retained Phase 0 population forecasts as conditional generating
probabilities. Real text, timing and cohort geometry are fixed. In each world,
select a random half of the canonically sorted writers (floor of half); shift
accept log odds by delta times one of:

- offset: one;
- content taste: a random writer-specific sign times standardized lexical
  similarity. Similarity is the maximum Jaccard overlap between any offered
  suggestion and the union of words in that writer's earlier completed sessions
  on other prompts. Each earlier session contributes its last retained decision
  prefix, not an invented final text. Empty history has zero overlap. Standardize
  once within writer over the fixed covariate roster, retaining zero-variance cases;
- habit: the mean accept rate of the last three resolved simulated choices,
  centered at 0.5; an empty history contributes zero.

Generate in open-time/key order. A choice enters history only when its recorded
resolution time is at or before the next choice's open time. Rebuild the previous
handling feature for every row from simulated history; never reuse natural lags.
Freeze all covariates before drawing any outcome. This is a conditional outcome
plasmode, not a simulation of altered text production or decision timing.

For each of the three constructions use deltas 0, 0.1, 0.2, 0.4, 0.8 and ten
independent worlds, seeds derived from 161016 and canonical grid index: 150 total.
Run the unchanged Phase 0 session-start fitting function and its past-only
penalty selection. Retain every row's generated probability/outcome, rebuilt lag,
predictions, every fit receipt, and the full grid. No altered optimiser, narrowed
cohort, selected seed or simulated truth passed to fitting.

## Readout and bounds

The primary recovered contrast is backbone versus refitted population half-Brier.
Recovery means its writer-cluster 95% bootstrap interval is wholly above zero,
using the existing 2,000-draw interval with fixed ordering. Report the complete
recovery curve, ten-world Wilson intervals and zero-dose recovery separately.
Ten worlds give coarse operating characteristics, not a precise false-positive
rate or a general detection guarantee.

Oracle injected gain is half the mean squared distance between generating and
saved population probability vectors. It is not the fitted pipeline's expected
gain. Report both, plus conditional expected gain of the actual fitted forecasts,
interval coverage for that conditional target, and observed-minus-expected error.
These diagnostics do not silently widen earlier intervals or retrofit significance.
Any recovery boundary is a discrete grid crossing; no smooth curve is invented
from ten worlds and no extension is selected on these results.

The old full Phase 0 checkpoints span about 186 seconds. This suggests roughly
eight hours for 150 fits; allow 20 computation hours and 12 hours waiting for the
exclusive CPU lease after V2, with a 10 GiB output cap. One numerical thread,
8 GiB RAM/commit and 20 GiB disk floors, exact native supervision and immutable
per-world checkpoints. A failed world stops the grid and retains all work.
Null worlds are required instrument controls, not negative human findings to be
discarded under the curator's early-futility rule. No downstream scientific branch
is extended or funded by an unfinished calibration.
