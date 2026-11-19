# CH13 and CH14: riders on the preserved SG1 table

Prepared for owner review under the November 15 full-week extension, sections
3B and 4. This is untested prospective code. No human row or new human outcome
was opened during this build. Prediction filing precedes this work. The R24
handoff's one-page definitions and S20/S21 were read; the packet supplies the
operational estimands. No theory or claim-ledger change follows from preparation.

## DESIGN CHECK

LESSONS sections 2/3/4/5 and the preserved SG1, CH8/CH12 and CH11 designs govern.
The source case is a recorded, chronologically ordered game followed by another
recorded game. A missing clock or unknown tournament identifier does not establish
a zero wait. CH13's case requires the same player to supply at least five losses
and five wins in each of the short and long bins. Twenty supported players is the
standing default population floor; below it retain descriptive points and counts,
withhold population intervals. This floor never pools players to manufacture the
per-player case. A null is not an unsupported comparison.

CH14's case is a choice among at least two options she already used in the same
context, with thirty earlier valid context games and a nonempty chronological
training/test partition. Missing context, future-novel choices and unavailable
chronology are counted separately. The same twenty-player standing population
floor governs intervals. The whole-player bootstrap must retain every draw;
invalid fits are recorded, not redrawn. Any missing primary draw withholds its
interval. Identical inputs must give exactly zero gain/contrast, never a tiny
rounding value promoted to a signed finding.

Null, alternative and traps share the same source, split, covariates, thresholds,
budgets and replay. The smaller route is a counted checkpoint/pilot and the
packet's descriptive support fallback, not an outcome-selected sample.

## Source and coverage

The sole production source is the complete, independently replayed SG1 table
from `SG1-source-continuation-2-20261113`. It retains the original salted two-percent
**player** sample, selected by `int(key[:16],16) < .02 * 2**64`. This is neither
two percent of games nor CH1's 10,000-player engine roster. It contains retained
April–June 2017 histories and no engine score is required. The approved independent
forecast split remains SHA256 of `SG1-forecast|20261112|` plus the existing salted
key: first hex 0/1/2 calibrates, others analyze. No new salt or roster is drawn.

Code inspection establishes that the table has start time, `duration_est` and its
missingness reason, tournament flag and salted ID, first moves by colour, scores,
pregame ratings and chronological history. Availability counts and qualifying
population sizes remain unmeasured until counted source setup. No claim is made
that all required fields are populated in real rows.

SG1's duration sums observed clock differences and increments, with the losing
side's final clock added for decisive Time forfeit. It excludes both first-move
latencies; missing/invalid clocks and ambiguous increment reductions are missing.
CH13's end is start plus this unchanged duration estimate, never wall-clock truth.

Only the original source database is opened immutable/read-only with every SQLite
sidecar refused. The new pair projection is private scratch, transactionally
checkpointed by a complete player. It may be copied only through the ordinary
authenticated new-attempt runtime. Neither original table nor source receipt is
modified. Runtime/native source admission and all original hashes remain owner's
prelaunch obligations; a file's existence alone is not qualification.

## CH13: within-player contrast and sampled peers

Sort each complete player's history by start then stable game ID, spanning months
and control classes. Adjacent observed games must have the same identified arena;
do not skip an intervening game to create a pair. Require increasing starts,
finite nonnegative duration and nonnegative estimated end-to-next-start wait.
Missing/tied/nonarena/tail/negative-gap cases have distinct census counters.

Analysis outcomes use non-calibration players only. The frozen SG1 forecast is
fitted on calibration players, with its previously approved decile recalibration.
Outcome is next score minus its forecast. Within-player outcome centering cancels
from each loss-minus-win difference, so physical time units and the exact contrast
are preserved. Do not centre minute values or move bin boundaries per player.

The primary is each player's after-loss minus after-win shift under two minutes,
minus that shift at twenty minutes or more, averaged equally over supported
players. Both four-cell counts must be at least five. Bar is -0.010 score points;
the estimate must reach it and the 95% player-bootstrap interval exclude zero
below. Six descriptive bins are [0,2), [2,5), [5,10), [10,20), [20,60), [60,infinity).

POOL-WAIT is explicitly a **sampled-peer** measurement. All retained sampled
players, including calibration players, can supply timing context only. Exclude
the focal player entirely. Within the same arena and inclusive ±60 seconds of her
estimated end, choose one nearest-ending eligible pair per other player; ties
use end then stable game ID. The median of a nonempty pool is defined, including
the average of the two middle waits for an even pool. Report the complete donor
size distribution and missing-pool count. A one-person pool does not itself meet
the contrast's separate population/row support requirements. No whole-arena
population, causal pairing instrument or source expansion is claimed.

The curator approved prospectively: sampled-peer waits take priority **only when
both intervals exclude zero in opposite directions**. Otherwise retain own-WAIT.
If peer support is absent, explicitly report an unsupported peer check and retain
the own-WAIT result with self-selection as a limit. This implements the November
16 owner relay of the answer “Use this explicit comparison rule (Recommended)”.
Magnitude disagreement, one interval spanning zero or a missing interval never
triggers a replacement.

Secondaries include both wait measures over all six bins, favourite/underdog
strata, and next-game DEPARTURE or berserk. The owner approved prospectively that
both losses and comparison wins use the same preceding forecast stratum: E>=0.65
for favourites, E<=0.35 for underdogs. This only fixes the secondary's comparator;
it leaves the primary population unchanged. DEPARTURE uses unchanged past-only
CH11 contexts and its twenty-game support. Berserk remains unavailable until the
exact source-bound SG1.v native result/seal/execute/replay and owner admission are
provided; absence holds only this secondary. No inferred flag is silently admitted.
The primary bar is not copied to these descriptive secondary metrics.

Bootstrap draws whole analysis players 2,000 times from one frozen sorted roster.
The empirical forecast and measured peer waits are held fixed, matching the
inherited table-card contract. This does not model cross-player arena dependence;
it is an explicit limit on the observational comparison.

## CH14: chronological predictive gain

Retain CH11 contexts: control class, colour, and Black's opponent first move.
Histories span the complete three-month window and are updated only after the
current choice is evaluated. At thirty earlier valid context games, the options
are only previously played moves. A novel chosen move is counted/excluded from
this likelihood, then added for subsequent choices. At least two past options
are required. No pseudo-count or unknown-option bucket changes the packet model.

Features per option are natural log of its earlier count, log(1+hours since last
use), and for the secondary log(1+all intervening player games). Original physical
hours/counts are retained. A common per-choice shift cancels in conditional-logit
probabilities and supplies within-choice centering without changing the model.

The first floor(2*n/3) eligible choices for each player train the common pooled
coefficient pair; her remaining choices evaluate it. Count-only and count+recency
use exactly the same choice menus and split. Training requires at least two
choices and evaluation at least one. The primary is the equally weighted mean
of each player's held-out log-likelihood gain per choice, not the pooled sum that
would overweight prolific players. Its bar is +0.003 nats, with interval above zero.
Every bootstrap resamples whole players and refits training coefficients before
evaluating their held-out choices; no held-out choice tunes the model.

Secondaries replace elapsed hours with games since use, and evaluate both trained
models on held-out choices following a break of at least seven days. Those are
held-out subsets of the original fit, not new fits restricted after seeing results.
Singular information, coefficients beyond the declared numerical bound, failed
line search or failed gradient certificate retain an invalid fit. They do not
trigger a new penalty, feature drop or draw. Bounds are numerical qualification
requirements and cannot be loosened after human outcomes.

The vector likelihood/gradient and scalar probability/gradient/Hessian replay are
separate implementations. Production uses BFGS; replay uses Newton with bounded
backtracking. Counts, options, split and all final inferential fields must match;
gradient and information-eigenvalue diagnostics remain retained separately and
are not required to have identical floating-point values.

## Known answers and qualification

The supplied `fixtures31b.py` is preserved. Its CH13 worlds are reconstructed with
the exact declared seeds and fed through this handler's within-player formula:
-0.0302, -0.0211 and -0.0008 rounded, with the packet's 0.006 recovery tolerance.
The composition trap separately shows that pooled short-wait curves can change
while the within-player contrast stays fixed. Literal boundaries, clocks,
self/other donors, sparse support and every peer-priority branch are checked.

The supplied CH14 script **does not qualify the packet's model**: it fits/evaluates
the same data and adds an early-share covariate. Its 0.0116 remains supplied
reference evidence, not a target for this chronological two-feature card. The
replacement literal fixture fixes training and separate held-out choice counts:
54/46 versus count-only 50/50 gives exactly
`0.54*log(0.54/0.5)+0.46*log(0.46/0.5)` = approximately 0.0032034 nats. A 50/50
world gives zero. A fixed 75/25 preference with count contrast log(3) gives a
positive count coefficient near one but zero recency gain. Independent derivative,
offset-invariance, novel-option, month/context, chronological split and complete
constructed SG1 execute/fresh-replay tests accompany those rulers.

No fixture has been executed by the builder. Owner review, counted constructed
tests, native continuation/replay qualification and exact producer-consumer
admission are outstanding. Prepared is not qualified or running.

## Costs, admission and reporting

Each new card has 40,000 CPU seconds, including preparation, fixtures, source
setup, fits, 2,000 draws, replay, all failures and supervision, within the existing
CH family and six-million-second Week 6 campaign ceiling. No carried CH/SG1 cost
is reset or charged twice. Initial controls are proposed inside one counted
600-CPU/1,200-wall slot; actual measured cost determines a subsequent native
qualification envelope. These are proposals, not permission for builder execution.

Production candidates remain unadmitted templates. The first attempt should cover
complete source setup and the first 100 of 2,000 draws under a 7,200-CPU maximum,
with ordinary two-thread CPU-only Gear2 resource guards and original Week6 clock.
The private pair database, largest player history and CH14 option arrays require
measured peak memory; a provisional four-GiB projection must pass current aggregate
memory admission. No whole-card cost or memory fit is asserted before that check.

Review CH13 with CH8 and CH14 with CH11, as the packet orders. Complete internal
write-through and the final set-level packet remain the owner's obligations.
No interim per-artifact score or scientific verdict is delivered by this build.
