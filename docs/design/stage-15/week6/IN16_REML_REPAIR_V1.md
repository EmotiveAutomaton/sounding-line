# IN16: isolated numerical replay repair

Prepared engineering proposal, not qualified or admitted. The failed original
attempt and every original checkpoint remain immutable. This addendum retains
the source, populations, units, estimand, controls, seed, 2,000 draws, rank and
boundary rules, and the original absolute replay tolerance of 1e-7 with zero
relative tolerance. It supplies no scientific interpretation.

## Observed failure and inference

The retained `IN16-primary-prefix-continuation-1` producer completed successfully
and its independent verifier exited 1 on November 16, 2026. Both saved aggregate
banks contain all 2,000 draws. Exactly 387 draw comparisons exceed 1e-7, all in
the conditional writer-share field; the largest absolute discrepancy is
3.7075670980546427e-7. Clearing and its fixed-unit conversion differ by at most
8.056055822436292e-15. Field inventories and recorded failure states agree.
Only differences derived from saved aggregate draws were inspected; no
participant rows were read or scientific estimates displayed or interpreted.

Both original implementations minimize the profiled REML objective using
`minimize_scalar(method='bounded', bounds=(0,12), xatol=1e-9, maxiter=200)`.
Production forms covariance-weighted sufficient statistics; independent replay
solves each writer's covariance directly. Both subtract a fitted quadratic
from a response quadratic to form residual sum of squares. Objective-value
roundoff near a stationary point can shift a numerical argmin more than the
objective's apparent convergence tolerance. This is the code-supported cause
hypothesis, localized by the aggregate differences; it has not yet been
confirmed by running the repaired solver on a constructed or human panel.

## Exact numerical change

Let t=log(1+lambda), where lambda=tau²/sigma², V=I+lambda 11', D=dV/dt,
A=X'V^-1 X and r=y-X beta. The same profiled REML objective is

    F(t) = log|V| + log|A| + (n-p) log(R/(n-p)),  R=r'V^-1 r.

Its derivative, using the fitted normal equations, is

    F'(t) = tr(V^-1 D) - tr(A^-1 X'V^-1 D V^-1 X)
            - (n-p) (r'V^-1 D V^-1 r)/R.

Production computes each writer's residual quadratic as the sum of squared
within-writer residual deviations plus n times squared residual mean divided
by 1+n lambda. This is algebraically the original Woodbury quadratic without
subtracting large fitted response sums. Replay independently solves the dense
covariance for X, y, residuals and D; it does not call the production covariance
formula. Multiplicities remain independent writer copies in every trace,
quadratic and residual degree of freedom.

The original bounded scalar optimization identifies the basin. A separately
declared engineering refinement brackets its analytic derivative within at
most 0.01 log-ratio units of that candidate, using the fixed radius sequence
in the new source. A negative-to-positive crossing is refined by Brent's
method at absolute t tolerance 1e-12, relative tolerance four float64 epsilons
and at most 100 iterations. Failure to find a local minimum, nonfinite scores
or root failure is explicit and retained, never replaced by a passing value.
The zero boundary still competes using the original 1e-9 objective convention;
the fixed upper-bracket refusal remains at 12 minus 1e-5. The original rank
tolerance 1e-9 and residual lower bound 1e-12 remain. No bootstrap draw is
dropped or replaced.

The stricter root tolerance is internal optimizer accuracy, not a wider replay
acceptance tolerance. `week5_in12_v1.compare` is unchanged and still compares
all full-bank values. Clearing, preparation, source selection, original trait
construction and duration scaling are imported from their unchanged versions.

## DESIGN CHECK

Relevant LESSONS §3 independent algebra versus sampling validity, §4 retained
precision failure, §5 retained checkpoint/failure accounting, and CONTROLS
§6–7 were reviewed. These controls concern numerical implementation, not
population sensitivity or a changed sampling model.

The literal balanced intercept-only fixture has a closed-form REML answer
from its between-writer and within-writer mean squares. A positive between-
writer component must recover that answer within 1e-8 on each independent
path. With all writer means equal, both paths must select the zero boundary.
Offsets of 0, 5 and 1,000 test response-translation invariance. Nonuniform
writer multiplicities test independent-copy degrees of freedom. Ragged
multi-predictor worlds and a fixed eight-draw bootstrap bank must retain
full production/replay agreement under the original 1e-7 rule.

Analytic-score checks compare direct and sufficient-statistic forms and finite
differences away from an optimum. Unsupported writers, exact rank loss, zero
residual variance, optimizer failure, nonfinite derivative, an unbracketed
local optimum and the upper boundary must refuse. The original clearing plant
must still recover its exact value. A comparator trap at 1.01e-7 must fail.
Dependency binding must pin the frozen source and refuse an old checkpoint
under a changed dependency binding. All controls are constructed-only and
have not been executed by the builder.

## Admission, costs and recovery

The retained failed continuation used 388.09375 execute CPU seconds and
927.71875 verify CPU seconds: 1,315.8125 native CPU seconds, with 1,360.9492242
wall seconds. Its earlier 100-draw prefix used 23.28125 native CPU seconds.
Owner-filed supervision and earlier preparation/fixture charges remain in the
same IN16 and IN-family ledgers. This note reports observations, not new or
duplicate charges. If the ordinary flat 30-second attempt charge applies,
the failed continuation's inclusive charge is 1,345.8125; the owner reconciles
that against the authoritative ledger before any new reservation.

Proposed first qualification: one counted, two-thread native Job with 300 CPU
seconds and 900 wall seconds for the exact focused pytest command in the
private delivery README. No pytest cache; retain source pins before and after,
actual native identity and inclusive usage; release only its owned lease.
The owner reviews and installs the candidate before running that command.

The new entry point is `runners.drive.cards.week6_in16_repair_v1`. It uses a
separately named runner and math module and changes the dependency/semantic
binding. No original draw can be relabelled as repaired or copied through that
binding. After passing constructed qualification, reserve a fresh full-scope
attempt under the unchanged 20,000-second IN16 ceiling and 200,000-second
family ceiling, including all old costs. Its ordinary first quantum of 100
draws is an in-slot timing/checkpoint stage, not a new scientific pilot. Use
the measured repair cost and remaining ledgers to authorize continuation to
all 2,000 producer and fresh independent draws. Preserve the failed original
and exact original output hashes. Do not amend or manufacture its completion.

A full fresh rerun is the simplest safe recovery because the old draw bank
binds the old numerical method. Reusing only unaffected clearing values would
need a separate exact migration design and is not part of this candidate.
The repair computes more direct covariance solves and residuals, so its cost
is not assumed equal to the failed version. Actual counted timing controls
admission; no change to the research ceiling or calendar is proposed.

If the unchanged 1e-7 check still fails, retain that failure and diagnose it.
Do not widen tolerance, round the two implementations to agree, discard the
secondary, select successful draws or reuse the production answer in replay.
