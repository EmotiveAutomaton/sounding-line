# CH8 and CH12: forecast-linked stopping and repeatable behavioral indices

Prepared November 13, 2026 under the two-day packet sections 3A and 4. Unadmitted
table-card candidates. SG1 is the only source; no engine scores or source
re-qualification are required. The packet remains verbatim. Original CH7,
TR1, source and live scoring files remain untouched.

## DESIGN CHECK

CH8 requires the same player to supply varying forecast and stopping outcomes.
The packet's 400-player planted contrast of 0.06 and zero counterpart, literal
fixed-effect dummy regression and an independently coded cross-product formula
check that case. State confounding remains even if those checks pass. No
behavioral result identifies SHAME or RAGE; a public game rating is not standing
in a room. The theory alternatives are the packet's attributed proposals.

CH12 requires measurable between-player variance before stability is interpreted.
TR1's 2,000-person worlds at stability 1, 0.5 and 0 are re-pointed to bounded
LEVEL, GAIN and FORECAST-GAIN indices, with independently noisy odd/even whole
sessions. All three recovery errors must be below 0.1. Literal hand counts and
a separate OLS implementation check the underlying indices. Constant or missing
indices must produce unsupported variance, never stable zero-noise conclusions.

The smaller routes retain the packet's exact support fallbacks: CH8 blitz then
rapid+blitz, below floor descriptive; CH12 20 sessions/30 losses in each half
then 10/15, labelled low reliability, and fewer than 300 players descriptive.
Failed numerical draws are retained, never redrawn. A source or fitted-unit
resource interruption yields safely and remains charged; no arbitrary smaller
population or altered threshold is selected after outcomes.

## Common forecast and source

The approved separate hash is exactly
`SHA256('SG1-forecast|20261112|' + existing_salted_player_key)`; first digit 0/1/2
calibrates, all other digits analyze. This repairs the original empty-analysis
split while retaining every selected history player. The curator's exact answer
and rationale are in `SG1_TWO_DAY_V1.md` and the two-day implementation record.

For each time-control class, ordered logistic regression fits loss/draw/win on
rating gap divided by 100 and a Black indicator. Thresholds are ordered through
a positive exponential distance. There is no separate intercept in the linear
predictor, since the thresholds carry it. All three categories and full design
rank are required. An unconverged/separated fit remains unsupported. Expected
score is win probability plus half draw probability. Its ten quantile bins are
checked on analysis players; ties remain in one bin and empty bins are counted.
If any nonempty bin differs from its actual mean by more than 0.03, that bin's
observed mean replaces E, as the packet prescribes. This aggregate recalibration
uses analysis outcomes and is explicitly not out-of-sample validation.

Both consumers authenticate SG1's complete table, seal, index and pinned native
completion/replay receipts. Only non-calibration players enter. Input SQLite
remains immutable. A lazy player mapping avoids materializing every game
dictionary at once; only calibration numeric arrays and aggregate sufficient
statistics span players. The largest one-player history and each ordered fit
are indivisible measured-resource units. The missing local Round 13–15 handoffs
are not represented as read; formulas and attribution come from the packet.

## CH8 formula and full registered secondary set

Primary rows are lost blitz games, not provisional and not month-censored,
with finite forecast and prior-session form. Candidate players have five
sessions and ten losses; 3,000 such players meets the primary case. If blitz
fails, pool rapid+blitz with a class term. If no player meets even the pooled
case, retain the pooled descriptive outcome rows rather than manufacturing a
population interval. Missing forecast, prior form and outcome support remain
visible through source/forecast/support counts.

The player-fixed-effect linear probability model uses favourite (E >= 0.65)
and middle (0.35 < E < 0.65) indicators, with underdog as reference; games so far,
sum of earlier surprise in that session, current losing streak, sine/cosine
hour, tournament and pooled-control indicators. The favourite coefficient is
the primary. Bar is 0.1 times the overall stopping probability after a loss.
Only nuisance redundancy among nuisance columns may drop. The target is then
tested conditional on every retained control: a missing underdog reference or
control perfectly confounded with favourite status is unsupported, never a
different contrast produced by dropping the control.

All 2,000 whole-player draws calculate the same registered outputs: the primary;
previous-start-gap falsification on the same lost rows and controls; points
lost and continuous E together (both targets required); remaining games after
the loss; non-tournament STOP/REMATCH/other-opponent shares in the three E bins;
and STOP rates by surprise decile over all results. The falsification excludes
only rows without an observable previous gap. A nonzero falsification remains
a rival inherited by the descriptive primary, not a post hoc gate or a repair.

## CH12 formula, reliability and limitations

Split at May 16, 2017 00:00 UTC. The packet imposes no class or provisional-session
exclusion on this card, so all control classes and provisional flags remain;
report that scope and changing control composition as a rival. Stop outcomes
still exclude censored tails. Before support selection, each player/half has
LEVEL = stopping share after favourite wins, GAIN = stopping share after losses
minus after wins, and FORECAST-GAIN = the OLS slope of stopping on E among
losses. Undefined class means and unidentifiable slopes remain missing.

Alternate whole source-defined sessions in chronological order within each
half, never individual games. TR1's split-half reliability is `2*r/(1+r)` from
odd/even index correlations across players. Corrected half variances are the
observed full-index variance times reliability. Across-half stability is the
raw correlation divided by the square root of the two reliabilities, unclipped.
The minimum corrected variance's bootstrap interval must lie entirely above
zero before interpreting any stability interval. Per-index missing support is
reported; fewer than 300 supported players cannot route a stable-trait claim.

Primary is GAIN stability: interval above 0.5 stable, below 0.2 not stable,
inside the intervening band partly stable, otherwise inconclusive. LEVEL and
FORECAST-GAIN are the same secondary calculation. LEVEL/GAIN correlation is
reported separately in each half with the same attenuation correction. Their
shared win-stop component creates correlated measurement error that this simple
correction does not remove; it cannot settle the number of psychological dials.

## Independent replay, uncertainty and admission

Production CH8 uses within-player centered cross-products and scaled normal
equations. Replay uses the independent raw-sum fixed-effect identity and least
squares on scaled aggregates. Forecast replay uses a separately coded logistic
identity and independently refits its parameters. CH12 replay uses a separate
moment calculation and OLS for the slope. All 2,000 draw multiplicities and every
formula are recomputed from the same verified table. Numerical agreement uses
relative 1e-6/absolute 1e-7, while categorical decisions and support/denominator
records must match exactly. A discrepancy refuses verification.

Execute caches completed forecast and bootstrap values only under the complete
source/code/config binding; a new counted attempt must authenticate all copied
bytes. Verification always starts from zero in a fresh directory. Source reads,
forecast optimizer iterations and bootstrap draws honor owner yield. The first
100 draws provide the actual 5% bootstrap checkpoint after setup; this is not
a claim of 5% of whole-card CPU. Setup/fit, repeated work and fresh replay all
charge the card. A whole-source cost forecast remains an owner-admission gate.

Ceilings remain CH8 60,000 and CH12 40,000 CPU-seconds, inside CH's existing
family and campaign. Candidates keep resource floors and a provisional 4-GiB
peak bound; actual source cost and memory are unmeasured. Every primary reports
estimate, interval, bar, `sees = 2.8*SE` and `supports_at = bar+2.8*SE`. These are
normal approximations, not empirical power. All outputs retain activation lists,
theory tags, source scope and descriptive/unsupported status. No launch follows
from this preparation alone.
