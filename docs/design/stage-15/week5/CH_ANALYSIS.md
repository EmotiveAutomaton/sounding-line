# CH analysis implementation addendum

This is a pre-outcome clarification of the committed [CH pipeline](CH_PIPELINE.md)
and [packet](PACKET.md), not a change to the running CH0/CH1 source or engine.
The CH family retains its 2,500,000 CPU-second ceiling and CPU-only scope.
All private projections, per-player fits, scores and resumable checkpoints stay
under ignored storage. Aggregate reporting waits for an entire card and replay.

## DESIGN CHECK

LESSONS 2–5 and CONTROLS 1–7 apply. The two directions and exact-zero worlds
must pass the same numerical and uncertainty rules. Player fixed effects are
checked against an independent full dummy-variable matrix; whole-player
bootstrap weighting is checked against explicit replicated player samples.
Leave-one-move-out residuals match actual deleted-row refits. Unidentifiable
targets, separated logistic fits and invalid bootstrap draws remain unsupported
or inconclusive. They are never treated as nulls or deleted from intervals.
All 200 planted clock targets must recover within 5% of the initial clock.
Serialized native fixtures exercise every CH4 secondary and CH6's right-censored
session tails, then recompute entire outputs in a fresh process.

## Complete input binding and finite grid

`week5_ch_collection.py` requires the frozen position roster, every completed
batch's report and successful replay, and post-replay SHA-256 bindings for all
scores. It joins every roster row exactly once at the declared node limit;
duplicates, extras, changed records and missing positions refuse. Batch completion
cannot authorize an incomplete population's effect calculation. The aggregate
collection receipt binds the complete private analytical-row stream. Constructed
collections are explicitly marked and cannot pass the scientific consumer gate.

Within a 400-point rating band, the earliest other available frozen month is the
calibration month for a target month's policy entropy. That choice is fixed
without inspecting fit. Top-five choice probabilities use the engine's existing
temperature fit; mating scores and choices outside the five are excluded and
counted. Fewer than 20 conditional choices leaves fitted entropy unavailable.
A separately labelled fixed-100-centipawn entropy remains a descriptive fallback.
Changing a target month's choices cannot change its own fitted temperature.

`week5_ch_grid.py` declares 44 finite cells: five primaries, two conditional
branches, and 37 texture cells. Each primary/branch uses 2,000 resamples and
each texture uses 200. Ordinary texture has a 3,600 CPU-second cap; the two
25,000-position node-count routes share the packet's 200,000 CPU-second rescore
allowance. Whole-family accounting remains binding. The owner enforces the
seven-consecutive-inside-band texture stop, six-null primary family stop,
2,000-draw precision follow-ups, and maximum two descendant generations.
Declared dependencies are readiness conditions, not evidence that a run occurred.

## CH2, CH3 and CH5

CH2's support count uses players with at least 20 measured moves. If the 5,000
player floor fails, pool time controls with control indicators and retain player
effects; label the result below-floor descriptive. Stakes-only and complexity-only
control variants are registered rival textures. CH2.m fits k50 × critical-position
indicator, alongside both main terms and the original controls, so the coefficient
tests whether the slope is steeper at absolute stakes ≤50. Merely reporting a
separate subset slope would not test that contrast. CH2.s substitutes entropy.

CH3's interaction uses rating-band midpoints in 400-point units. Its book-move
rating secondary first attempts a within-player coefficient; absence of within-
player rating variation is unsupported, not a zero result. A pooled descriptive
rating coefficient with player-cluster uncertainty is reported beside it. The
book/non-book rating interaction includes exact move-number indicators, so the
comparison matches ply opportunities. The unique-game position denominator and
500-game threshold remain those of the frozen census.

CH5 uses exact leave-one-move-out expected-time fits and refits all nuisance
parameters in every player resample. Both endogenous columns and both excluded
instruments are retained; both partial F statistics must exceed 10. The improvement
readout is −interaction × log(2), in centipawns per doubling per 400 rating points.
Weak instruments leave descriptive OLS only; a default floor below 20 players
uses pooled descriptive OLS. The ten-second threshold's exclusion restriction
remains an unproved observational assumption. No result establishes causality.

## CH4: held-out targets and explicit secondary definitions

Primary gain is total held-out log-likelihood improvement divided by held-out
moves. Whole-player resamples recompute that numerator/denominator ratio. The
equal-player mean is a labelled secondary. All targets, move-number medians,
slopes and variances use training games only. The 10/20/40/80 learning-curve
fits share exactly the same held-out games. Their profile-likelihood widths
are scale-only descriptions: residual dependence prevents treating the naive
likelihood widths as evidence for learning. Intervals for gains remain player
cluster intervals.

Overshoot uses the fitted absolute clock target (training move-number median
plus fitted centered target) to define the packet's relative 30% excursion.
An excursion ends after two consecutive moves within 5% of the initial clock
of the target, or after ten own moves. Crossing the target before that endpoint
counts as overshoot. Uncrossed excursions truncated by the observed game or a
clock-floor break are right-censored and reported separately. Deficit and surplus
have separate denominators; absent excursions are unsupported, not zero rates.

The matched null estimates AR(1) persistence and innovation variance from
within-game training residuals, starting each simulation at its observed initial
share and advancing the clock by increment minus simulated think time. Twenty
simulations per held-out sequence use the same floor, horizon and settling rule.
Nonstationary residual fits are unsupported. No deviation shuffle is used.
The secondary estimate is each player's observed-minus-null overshoot share,
with whole-player uncertainty, separately for deficit and surplus.

Precision is the median restoring-slope difference between the top concentration
quartile and the remaining players. Concentration is the largest control share
of games; its days texture uses distinct control/day pairs. Quartiles are rebuilt
in each resample; tied concentrations without both groups are unsupported.
The band model profiles half-widths 0, 0.025, 0.05, 0.10 and 0.15 of the initial
clock beside the point model, with training selection and identical test moves.
The no-restoring interval concerns the additional target response; original
clock/move/increment nuisance terms stay in both models.

## CH6 and bounded storage

The session fallback and trailing-game censoring are unchanged. Positive versus
negative net session rating is the primary contrast, zero net change has its own
indicator, and the continuous-gain coefficient is secondary with its own player
interval. The model includes cyclic UTC hour, last result, game count and player
effects; the unsupported floor takes the packet's pooled descriptive route.

`week5_ch_history_index.py` projects the completed source histories to an indexed
private SQLite table, keeping only the clock/timing and game metadata needed by
CH4/CH6. Every value is replayed independently. CH4 loads only one player's rich
history at a time. CH6 accumulates compact numeric session arrays rather than
all move dictionaries. Neither this projection nor analysis modifies the frozen
CH0 database. Incomplete source or projected histories refuse scientific use.

The index commits every 1,000 player-games and honors the supervisor's yield
request there. A new attempt can resume a hash-bound copy with unchanged source
identity; a completed index is never resumed. Analysis checkpoints bind every
input specification and configuration. Completed deterministic bootstrap draws
and player fits can be reused only by a new attempt with that exact binding.
Fresh verification deliberately ignores the resume cache and recomputes all work.
The first completed 5% of a recorded analysis loop emits a cost checkpoint;
this is a forecast for that loop, not a final claim or a hidden sub-allocation.

Projected peak RAM is 4 GiB for analytical cards. Native resource admission,
combined execute/replay accounting, whole-player sample routes and measured
in-slot forecasts govern larger real inputs. A design note or constructed
fixture is not a full-data cost measurement.
