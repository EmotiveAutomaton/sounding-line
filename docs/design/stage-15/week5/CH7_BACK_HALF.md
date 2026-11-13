# CH7: behaviour around a personal rating reference

Prospective implementation, November 11, 2026. This design is prepared for owner
review; it is not a committed design or an admission. Authority is
`PACKET_BACK_HALF.md` §2.4, R2 and amendments L, N, O, P and Q, with
`THEORY_HANDOFF_2026-11-11.md` question 6. Standing remains under review. A game
rating and playing another game do not establish social standing or risk-taking.

## DESIGN CHECK

The identifiable contrast is the difference in the magnitudes of two slopes of
playing on around the rating at the session's start. Losing the last game and
being below that starting rating are mechanically connected. Last result and
losing streak are controls; the simulated-history null prices the remaining
connection under an explicitly approximate rating law. The null is not a
reconstruction of Glicko-2, latent skill or the site's actual update rule. A
supporting result cannot exclude every model of rating regression toward skill.

No analysis selects players or months from unfinished results. The three complete
April, May and June 2017 source censuses and original 2% player history sample
are required. July is withdrawn and preserved. Whole-player bootstrap keeps
dependence across all three months. All new source projection, fixtures,
production, replay, interruptions and failures charge CH and the 60,000 CPU-second
CH7 envelope; the CH family remains 2,500,000 and campaign 6,000,000 CPU-seconds.

## Source and cases

The immutable earlier history projection omits the pregame ratings needed here.
`week5_ch7_source_v1` delegates its existing cooperative source traversal and
independent full raw replay, adding each sampled player's authenticated pregame
rating, the opponent's pregame rating and the source ordinal. Known game results
and every previous field retain exact values. An unknown result becomes missing,
not a loss. No original source, salt, index or source selection is changed.

The source wrapper refuses any month set except April/May/June. Its production
input is the fully completed, pinned sampled-history source. The consumer accepts
only a complete nonconstructed index and matching database/index seals bound to
the new projection code. Owner admission must additionally authenticate that
producer's complete native execution and independent-replay receipts; a seal
alone is not a claim that replay ran.

Sessions are within time-control class and month: consecutive starts less than
1,800 seconds apart. This preserves CH6's start-to-start scope and month-tail
censoring. The last observed game of each player/control/month has no stopping
label. Any absolute rating change greater than 25 removes its entire observed
session, with games and sessions counted. Missing times, changes, results and
pace remain separately counted. Blitz is first; fewer than 3,000 players with at
least five retained blitz sessions triggers pooled rapid plus blitz, with separate
control-class sessions and references and a control-class nuisance term. Below
the same pooled floor is descriptive, never a successful case check.

The window best and the count of first 30 games carry chronologically across all
three months within the control class. Reference histories retain provisional
sessions even though those sessions supply no primary outcome rows. The
provisional-first-window-game restriction is implemented and counted as a proxy;
that observation does not authenticate account creation or a true lifetime best.

## Frozen models and uncertainty

Recent distance is `(postgame rating - first pregame session rating) / 20`.
The two targets are its negative and positive parts. The linear probability
model includes player fixed effects, games so far, win/draw indicators, current
losing streak, pregame opponent rating gap / 400, and sine/cosine hour of day.
The primary is `abs(below slope) - abs(above slope)`. The base bar is one tenth
of the observed stopping probability. Intervals are 95% percentile intervals
from 2,000 whole-player resamples. A singular resample is retained as invalid;
any invalid draw withholds its interval rather than changing the draw count.
Dependent nuisance columns can be dropped, but either missing target makes the
estimand unsupported. Within-player sufficient statistics preserve the original
fixed-effect regression; the constructed dummy-matrix and replicated-player
checks compare the same coefficients independently.

The working bar is the larger of the base bar and
`2 * mean(abs(null contrasts)) + 3 * SD(null contrasts)` over all 20 valid null
histories, with sample SD. Any unsupported own-player fit or invalid null draw
withholds the calibrated bar and an inferential verdict; the original cohort is
not silently reduced. Primary support requires the contrast interval above the
working bar. An interval wholly below zero or inside the working band is against;
otherwise inconclusive. Below-floor results cannot route a supporting claim.

A floor requires a supporting contrast and the above-reference slope interval
inside the working band. A ladder requires both slope intervals outside that
band and the contrast interval inside it. Everything else is mixed. Per amendment
P, report `2.8 * bootstrap SE` and `working bar + 2.8 * SE` beside the estimate,
explicitly as optimistic normal approximations rather than measured sensitivity.

Registered secondary rows are:

- After the first 30 games, stopping following a win that strictly sets a new
  window best versus a win ending zero to 15 points below the preceding best.
  Retain only exact rating-gain strata containing both groups, include gain-stratum
  effects and count the retained rows/players/strata. Ties do not set a new best.
- The slope of playing on over distance below the window best after the first
  30 games. This second slope uses all retained results, not only wins; the
  win-only restriction belongs to the preceding new-best contrast.
- Median positive `think_time / clock_before` over measurable moves in the next
  within-session game, on the recent-reference terms. Missing/zero/negative clock
  use is excluded and counted. This is conditional on actually playing another
  observable game; it is not the primary probability outcome.
- The recent-reference contrast restricted to control-class histories whose
  first observed window game had an absolute rating change above 25. The above
  source qualification accompanies this proxy cell.

All secondaries use the same 2,000 player resamples; unsupported secondaries stay
explicit. No April exclusion applies to CH7: April-only calibration and excluded
April outcomes apply to the separate CH2 policy-entropy measures.

## Explicit approximate simulated-history null

For each player and control class, expected score is
`p = 1 / (1 + 10 ** (-rating_gap / 400))`. Draw probability is
`d = lambda * 2 * min(p, 1-p)`, loss probability `1-p-d/2`, and win probability
`p-d/2`. Thus probabilities are feasible and expected score remains p. The own
player's lambda in [0,1] is fitted by Bernoulli likelihood of draw versus decisive
outcome; boundary fits are retained and counted. This is not a categorical
maximum-likelihood fit using the additional win/loss direction information.

The positive update scale is the own-player least-squares coefficient through
the origin from observed rating change onto `(actual score - expected score)`.
It must be finite, strictly positive and identified. Report its range and the
median update residual RMSE. No clipping to a positive scale and no borrowing
another player's scale are permitted. Unpenalized own-player logistic playing-on
fits use only games so far, last-result indicators and sine/cosine hour, with an
intercept. Constant observed outcomes are recorded as boundary probabilities;
unconverged, separated or singular fits are unsupported, never ridge-repaired.

Each of 20 simulated complete chronological histories starts at the observed
first pregame rating, keeps the observed opponent schedule and observation
times, simulates all win/draw/loss outcomes, and updates rating by
`K * (simulated score - expected score)`. Rating gaps use the current simulated
rating. Playing on uses the fitted nuisance probability, with no reference term.
Simulated session starts follow simulated stopping and the original month
boundaries. The observed provisional/missingness and tail-censoring masks are
kept fixed; window references and the 30-game eligibility are rebuilt. The fixed
opponent schedule, missingness masks, approximate positive update rule and
nuisance fit are assumptions of this null, not verified properties of the site.

## Checkpoints, costs and remaining qualification

Execute caches complete player projections, complete own-player fits, and complete
bootstrap/null draws in private SQLite/JSON. Only a fully hash-authenticated
new-attempt copy can reuse them. Verification creates a fresh workspace and
recomputes every source player, fit and all 2,000/20 draws from zero. Owner yield
is checked during authentication, between players and draws, and inside the
full-history null between players. No partial hash or incomplete null draw earns
verification credit. Repeated verifier interruption can repeat work; all costs
remain charged.

The optional operational quantum counts newly closed source-player/fit/draw
units. First-five-percent receipts name the actual phase and denominator; they
are not five percent of total CPU. The first main candidate stops after
`ceil(source index players / 20)` new player projections. It measures source
setup only. Own-player fit, full-cohort algebra, bootstrap and complete-null costs
still need a conservative continuation assessment. One largest-player operation
and the memory resident full-cohort arrays are indivisible units. Their peak and
yield latency are unmeasured; qualification must establish they fit the declared
4-GiB peak and bounded work allowance, or prepare a separately reviewed successor.

Seven focused constructed tests passed in 12.15625 native Job CPU seconds; after
adding explicit support counts, all nine checks passed in 17.703125 seconds,
including complete constructed handler/replay and authenticated continuation.
The driver pre-start path/handle error is retained separately. No human source or
engine was loaded. `week5_ch7_native_fixture_v1` is a prepared, unrun counted
qualification: raw three-month constructed projection plus full replay; null,
planted floor and planted ladder worlds; 2,000 bootstraps and 20 complete simulated
histories each; numerical recovery, joint shape gates and full fresh native replay.
The earlier focused fixture remains preserved. Passing small algebra checks is
not passing this full native fixture or pricing production.

Admission requires owner review and committed-design status, complete native
qualification including checkpoint/refusal boundaries, authenticated complete
three-month source/roster and producer replay, actual resource measurements,
current family/campaign totals, and a total execute/replay forecast inside the
remaining ceilings. All candidate paths for unfinished dependencies remain null.

