# Week 5 CH: clocks, independently measured choices, and player histories

Authority: [Week 5 packet](PACKET.md), sections 0, 2.2 and 3. Family ceiling:
2,500,000 CPU-seconds, including source preparation, replay, Stockfish, analysis,
pilots and descendants. Seed 20261107. CPU only; two single-thread Stockfish
processes per counted slot, 64 MB hash each. No Lichess evaluation-file scores.

## DESIGN CHECK

Read for this design: LESSONS sections 2–5, CONTROLS sections 1–7,
THREE_COGNITIVE_LAYERS expertise/attention account and its corrections (287–488),
set points and standing (661–851), and the complete Week 5 packet.

- **Case and check:** clock differences have known arithmetic, PGN main lines
  round-trip through python-chess, a single legal move has k50=1, and a position
  with exactly one mate in one has k50=1. These identities hold under both null
  and alternative human behavior. Any violation is an instrument failure.
- **Signed checks:** constructed within-player positive, zero and negative
  coefficients must be recovered with their direction. An exact-zero world may
  never become a supported effect. Singular targets and invalid bootstrap draws
  are reported explicitly; they are not dropped to manufacture an interval.
- **Falsifier:** no within-player association can produce support only through
  chance or a faulty uncertainty rule. Primaries require all of a player-cluster
  95% interval past the practical bar; intervals wholly opposite zero or wholly
  inside the practical band are against, otherwise inconclusive. Below-floor
  pooled results remain descriptive and do not license engine changes.
- **Smaller route:** whole-player frozen samples under amendments E/K/L; first
  5% in-slot pilot for forecasts over 7,200 CPU-seconds. No hidden sub-allocation.
  Rescoring texture uses at most 25,000 original positions and 200,000 family CPU
  seconds. Other texture is capped at one CPU-hour, unless packet L(e) applies.

## CH0: source and selection

Sources: 2017-04, 2017-05, 2017-06 and 2026-07 rated Standard monthly PGNs,
CC0, SHA-256 pinned from the official listing or previously verified local
receipt. May/June fall back to the existing April/July months if retrieval fails.
Sources stay private. Site URLs and raw usernames are not retained in derivatives.
Usernames are HMAC-SHA256 with the common private Week 5 salt. The salt is never
published. Every game ID derives from its source digest and source ordinal.

One streaming census counts eligible player games by month, time control and
400-point rating band, counts first-ten-ply opening position/move frequencies,
and retains complete per-move histories for the fixed 2% hash sample of players.
Per-game opening occurrences count once. The full months are never decompressed
to disk. SQLite transactional checkpoints bind the source digest and last game
ordinal. Restart skips saved ordinals, and never increments their counts again.
Each source's first 1,000 eligible games is round-tripped through python-chess.
The completed census is independently replayed before sample admission.

First-stage frame: at least 20 rated games in a month/time-control/rating-band
stratum. One deterministic hash rank assigns a multiply eligible player to one
stratum, so each player is selected once. Historical and 2026 groups each receive
half of the allocation, with 70% blitz and 10% each bullet, rapid and classical.
Within era/time-control strata, proportional rating-band quotas use the largest
remainder method. Unfilled quotas are reported, not reassigned across eras.
The selection reads no clocks, engine scores or results.

The second pass chooses ten games by seeded game hash and up to four moves per
game by seeded move hash, after excluding each player's first two moves. The
selection still precedes availability of think time. Up to 40 moves/player and
400,000 positions are the primary sample. Short games and missing clocks reduce
support explicitly; sampling is not repeated until an outcome happens to exist.

Time-control strata use initial seconds plus 40 increments: bullet <180; blitz
180–479; rapid 480–1499; classical >=1500. Think time is own previous clock minus
current clock plus increment. Missing clocks break the chain. First two moves,
negative times, and zero times are counted; zero times never enter time models.

## CH1: frozen engine ruler

Stockfish 19 sf_19 Windows universal executable SHA-256
`45bc8e4969147db9c2eb533810637994619bff0eacc81ccfd9854394901bcbd0`;
python-chess 1.11.2. Each position starts with `ucinewgame`, one thread, 64 MB
hash, MultiPV min(5, number of legal moves), and exactly 1,000,000 nodes.
If the played move is absent from the five, a separate root-move search uses
the same fixed node limit and fresh game state. Every completed score gets its
own immutable atomic checkpoint and fresh-process exact replay.

Filler batches begin no new search after 600 wall seconds, reserving equal time
for full replay plus the last fixed-node searches within a 30-minute scheduling
quantum. The counted supervisor's combined wall cap remains 1,800 seconds.
Batch completion is not population completion. The last offset and count are
explicit; only the authenticated full roster can authorize CH2/3/5 analysis.

k50/k100 count moves within 50/100 centipawns of the best, from the mover's
perspective. Stakes is the absolute pre-move evaluation; complexity is the legal
move count. Centipawn loss is best minus played, floored at zero. Mating values
are retained as mate distances, with a separate ordering sentinel for the
known-answer k50 check; they are **not literal centipawn observations**. Primary
regressions requiring numeric stakes/loss exclude those positions and report
the denominator; their k50 counts remain available as a labelled sensitivity.
Single-legal-move boards and unique mateIn1 puzzle positions must give k50=1.

Policy entropy is secondary. Within rating band, fit a softmax temperature on
a held-out month, then apply it only to other months; exclude and count played
moves outside the five from this conditional calibration. The companion
fixed-temperature (100 centipawns) result is the fallback when calibration has
fewer than 20 observations. It is labelled uncalibrated, not substituted for
the fitted primary ruler. No target month's choice tunes its own temperature.

## CH2, CH3 and CH5 analyses

CH2: log positive think time on k50, clock share, increment, move number,
stakes, legal-move count and total material, with player fixed effects. Blitz
is primary, practical bar log(1.03) per additional close move. At least 5,000
players with >=20 analysed moves; otherwise pool time controls descriptively.
Player demeaning and per-player sufficient statistics permit exact whole-player
bootstrap weighting. Use 2,000 draws for a primary, 200 only for texture.
Gap (best minus second) and breadth beyond the second are secondary rivals.
Single-move positions have no second-best gap and do not receive a fabricated
gap. Texture: each control, k100, policy entropy, 2017/2026, 300k/3m nodes.
Supported branch CH2.m uses absolute stakes <=50; against branch CH2.s uses
policy entropy. Ceiling 60,000 CPU-seconds plus the separately stated family
rescore allowance.

CH3: same model plus k50 × rating/400. Positive interaction is primary,
bar log(1.02) per 400 rating points. Book is first-ten-ply position seen in
>=500 same-month/control games and its modal played move (lexicographic UCI
tie break fixed in advance). Rating slope on book-move log time is secondary;
non-book comparison matches move number. Texture: controls and 200/800-point
rating bands. Ceiling 40,000 CPU-seconds.

CH5: centipawn loss on expected-log-time deviation × rating/400, with both
main terms, CH2 controls and player fixed effects. Expected time uses a
leave-one-move-out regression with player effect, control, 400-point band,
k50 and move-number decile. Nuisance fitting is repeated for each whole-player
resample. The excluded instruments are clock<=10 seconds and its rating
interaction, while clock share and a smooth quadratic clock term remain in
the controls. Both first-stage partial F statistics must exceed 10. OLS is
always reported; weak/invalid first stages route only to descriptive OLS.
Negative interaction favors multiplicative expertise; report improvement
`-interaction * log(2)` per doubling and 400 rating points, practical bar 1 cp.
The threshold's exclusion restriction is an unproved observational assumption,
not established by the F checks. Texture: controls, losses capped300/1000,
and stakes<200. Ceiling 40,000 CPU-seconds.

## CH4: reserve target

Use the complete 2% player histories, blitz first, chronological game splits
(first70% train, final30% test), >=50 games/player; >=115 games for the
10/20/40/80 learning curve. Compute move-number median clock share from
training games only. Fit a profile-likelihood piecewise response of log think
time around a target; nuisance terms and residual variance are estimated on
training games only. Compare the target and no-target models on identical
held-out moves; primary gain bar0.005 nats/move, 2,000 player resamples.
Below1,000 eligible players gives the pooled descriptive route.

Packet literal berserk exclusion stays: first clock below initial excludes and
counts the game. A bounded intake check found every subinitial first clock in
the two available months exactly half-initial (36/1,949 and18/1,966 observed
player first clocks); none lay strictly between half and initial. This is
source validation, not a scientific estimate. Report exact-half and other
subinitial cases separately; the latter are unauthenticated exclusions.
Exclude clocks<15% initial and count them. The floor is on the observed clock,
never the centered reserve. Targets are not assumed physiological needs.

Secondary: learning-curve gain; bidirectional overshoot at30% of target with
an AR(1) residual matched simulated null, never shuffled deviations; upper
quartile control-concentration difference in restoring slopes; two-threshold
dead-band versus one-target held-out gain. Target at move20, rapid, days versus
games concentration, and20/40% overshoot thresholds are texture. Synthetic200
player target recovery must place targets within5% clock before admission.
Ceiling80,000 CPU-seconds.

## CH6: stopping and standing

Use longitudinal 2% sample, sorted UTC timestamps. A gap>=30minutes starts a
session. Direct end timestamps take precedence; if absent, the frozen fallback
uses **start-to-start gaps**, explicitly a different session-boundary proxy.
No unobserved game-end time is invented from lag-adjusted clocks. Within-month
last records are right-censored, never treated as voluntary stops; the separated
2017/2026 windows cannot create intervening observed sessions.

Logistic discrete-time stop on net rating gain (positive versus negative, with
zero separate), last result, game count, hour-of-day and player fixed effects.
Primary odds ratio bar1.05, 2,000 player-cluster draws. Floor10,000 players with
>=5 observed sessions; below-floor pooled descriptive model runs automatically.
The continuous gain slope is secondary and cannot distinguish satiation from
loss-chasing causally. Texture:15/60minute gaps, blitz/rapid, streak terms,
2017/2026. Ceiling30,000 CPU-seconds.

## Dependencies and reporting

No CH regression is ready merely because this design exists. The root owner
reviews each native fixture and commits the design before readiness. CH2/3/5
also require the complete frozen CH1 roster and replay; CH4/6 require completed
history extraction. All effects are descriptive; partial batches show only
operational counts. Full write-through precedes ACK. Every landed primary
names earlier B4/set-point/standing ledger rows and routes its comparison under
the packet's two-generation reread rule. Central ledger/theory/publication
edits belong to the owner, not this builder.
