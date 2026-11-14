# CH10: costly claims after results, with the approved arena-bonus control

Prepared November 13, 2026 before any response fit. Unadmitted. The curator's
exact decision is: **“Use the 2+ win bonus control (recommended)”.** The original
packet and `CH10_FEATURES_MODEL_HOLD_V1.md` remain unchanged. The original full
categorical streak model is retained as **cannot identify the win/loss contrast**:
previous-win equals the sum of the one-win and two-plus-win indicators. It is
not fitted or silently repaired by dropping a control. Numeric 0/1/2 is not an
alternate primary. The approved control is the indicator for a known winning
streak of at least two, matching the packet's arena-scoring rival.

## DESIGN CHECK

The complete constructed primary has 300 synthetic players with exact berserk
frequencies 0.10 after losses and 0.14 after wins, crossed with the registered
controls. The adjusted contrast must recover 0.04 and contain it in its full
2,000-player-resample interval. A separate complete distributed-lag world plants
win coefficients decaying by 0.5 and loss coefficients decaying by 0.8. Both
coefficient sequences and their lag3/lag1 ratios 0.25 and 0.64 must be recovered,
with their difference -0.39. Frequency compression represents explicitly counted
binary successes/failures at identical predictor vectors; it preserves exact
cross-products, means, row counts and whole-player weights. A literal expanded
cell checks that algebra. This validates arithmetic, not empirical power.

Source is complete verified SG1, with the independent forecast split already
approved. Cards use analysis players only. CH10 additionally requires the exact
verified SG1.v instrument result, its seal and native completion/replay receipts,
plus explicit owner admission. A histogram alone cannot release the card.
Nonfinite/missing/outside clocks stay missing rather than non-berserk. A missing
tournament identity or any unpositioned game in that player's tournament is
counted and excluded. The chronology adapter retains all source rows, including
missing-start rows that other time-ordered consumers cannot use.

State at the first observed tournament game is left-censored. Possible capped
streaks begin as {0,1,2}; a loss/draw resets to known zero and two observed wins
establish two-plus. Unknown outcomes restore uncertainty. Current outcomes enter
only subsequent predictors. Game number and elapsed minutes are relative to the
first observed game, not a claimed whole-tournament start.

Primary: player-fixed-effect linear probability of current BERSERK on previous
win and draw indicators (loss reference), current own-minus-opponent rating gap
per hundred, previous BERSERK, approved two-plus bonus, observed game number and
minutes since first observed game. Bar is one tenth of the base berserk rate.
Targets are tested conditional on all registered controls. Missing reference or
control confounding remains unsupported, not a changed comparison.

Every registered secondary is retained: underdog versus favourite previous wins;
favourite versus underdog previous losses; after a failed berserk versus another
loss; and the current rating-gap slope. The failed-claim model treats previous
BERSERK as its target instead of duplicating that same column as a nuisance.
The two surprise contrasts exclude middle-E preceding games and missing E.
Time courses are a joint distributed-lag model with separate win/loss indicators
at lags1-4, each relative to draws, plus the same controls. All eight lag targets
must be jointly identified. Lag3/lag1 ratios and their difference retain undefined
zero-denominator draws; no clipping, redrawing or unregistered reference change.

All five models and all ratios use the same 2,000 whole-player multiplicities.
Independent verification reconstructs histories, fits independent raw-sum
fixed-effect cross-products and recomputes all draws and ratios from zero.
One-person or constant-outcome readouts have diagnostics without population
intervals. Setup is player-streamed and stores aggregate sufficient statistics.
The first candidate is complete setup plus100/2000 draws, not5% of total CPU.
Authenticated new-attempt copying preserves checkpoints; final replay is fresh.
The 60,000-CPU ceiling, actual cost/peak qualification, independent native proof,
owner design review and source/instrument admissions remain gates.

Arena scoring, unobserved standings, game duration and selection remain rivals.
Activation is the packet's pride/claim-versus-SHAME analogy. A public game rating
is not standing in a room; these data do not identify an emotional channel.
