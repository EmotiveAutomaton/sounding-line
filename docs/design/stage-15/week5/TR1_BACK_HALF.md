# TR1: is the repeatable property a level or a response to luck?

Prospective owner-review candidate, November 11, 2026. This note implements
back-half packet §2.3 / H12-T7; it changes no original MD result. It has not been
admitted or run on the source. The packet and Round 12 handoff commission the
question; the initial theory reading remains complete, with the current
set-point/mood discussion and correction history reread for this build.

DESIGN CHECK: LESSONS §§2–5; CONTROLS §§6–7. Measurement error can masquerade as
unstable gain. The two reliability estimators must recover all three known
stability worlds before human inference. A positive, measurable variance is a
separate gate. Ratios above one and negative corrected variances remain visible.
Every resample selects whole participants and retains all their plays; no failed
draw is redrawn or removed. A complete fresh replay is required. Exact source,
module and semantic bindings survive checkpoint/reentry. The source's twelve
ratings are a potential instrument limit, not evidence against traits.

## Source and measurement

Authenticate the complete, independently verified `MD-source.h1` and the completed
MD3 parent. Their task path must agree; the original archive/MAT SHA-256 and
every-value source verifier remain binding. Only repaired repeat-eligible
participants with at least two completed plays enter. Duplicate-counter and
nonfinite-clock exclusions inherit MD3 exactly. Source identities, demographics
and clinical fields are not loaded. Private ordinal clusters never enter URLs,
queries or public outputs. Cite Dryad DOI `10.5061/dryad.prr4xgxkk` (CC0).

Consecutive means adjacent **observed completed** plays in attempted-play-counter
order. Report missing-attempt pairs; do not invent unobserved outcomes. Each
participant contributes all such pairs, so the estimand is pair-weighted, with
whole-participant uncertainty. This can weight frequent returners more heavily.
The complete source supports twelve rating occasions per play; retain the actual
rating count and all rank/support exclusions in the run receipt.

Trial luck is chosen gamble outcome minus the mean of its two endpoints, or zero
for the sure option. Discount trial history by the packet's fixed 0.65. The first
rating precedes the first choice; the later rating stored in a trial follows that
trial's outcome, as the pinned source guide establishes. Fit all twelve ratings
by OLS on intercept and recent luck. Level is predicted rating at zero luck;
gain is happiness points per task-luck unit. Neither outcome clipping nor rating
standardization enters the primary. The original independent scalar-history
fixture and a dense least-squares reference verify these conventions.

Both full and each six-rating half regression must have rank. Form consecutive
pairs before enforcing this common support mask, retain failed-pair counts and
never bridge over an unsupported play. Fewer than twenty supported participant
clusters is unsupported for population inference; this is a numerical safeguard,
not a source-selected practical-effect bar.

## Reliability and the required qualification

Candidate sampling reliability at each side of the paired sample is
`1 − mean(per-play gain sampling variance) / observed gain variance`.
Per-play covariance is the OLS sandwich for a stationary AR(1) rating-residual
correlation. The common lag-one residual coefficient is estimated from pooled
within-play OLS residual products and bounded prospectively to [−0.95, 0.95]; both
the raw value and any bounding are reported. Each play's residual scale divides
its squared residuals by `trace((I − H)R)`, not the independence-only degrees of
freedom. This is an explicit conditional measurement model, not a claim that the
real residual process is exactly AR(1).

Candidate split-half reliability is the Spearman–Brown expression `2r/(1+r)`
using first-six and last-six gain estimates across the same paired sample at
each side. This temporal-half convention is frozen here. The corrected variance
is the observed variance times this reliability. The candidate cannot convert a
nonpositive reliability or undefined correlation into a usable stability ratio.

For each candidate, stability is the observed consecutive-play correlation
divided by the square root of the two reliabilities. Report it **unclipped**.
The primary variance check uses the minimum of the two corrected side variances,
requiring both to be measurably positive. All quantities are recomputed under
2,000 whole-participant resamples, including the pooled residual AR coefficient;
the estimator choice itself remains frozen after calibration.

Before human aggregate stability is computed, nuisance-only preparation obtains
the real trial structure and pooled residual autocorrelation/scale. For each of
the three fixed worlds (gain stability 1, 0.5 and 0), sample 2,000 entire observed
participant trajectories with replacement. Their trial histories and play counts
remain intact. Generate normally distributed gains with the named correlation
between adjacent plays, a constant participant level, and stationary rating-level
AR residuals matched to the nuisance estimate. This is conditional calibration
on observed trial choices, not an intervention on choices or recovered real
counterfactuals.

The planted gain standard deviation is fixed at one pooled residual standard
deviation of response per pooled within-play luck standard deviation. It is not
tuned to recovered stability or to the human variance gate. Generated ratings
are unbounded linear outcomes, explicitly constructed; no scale clipping changes
the planted relationship. Both estimators run the identical generated data.

An estimator qualifies only if each of its three recovered stabilities is within
0.1 of its generating target. Among qualifying estimators choose the smaller
absolute error at 0.5; exact ties choose sampling variance. This reconciles the
packet's all-three requirement with its instruction to stop when neither
estimator passes. Freeze the choice before any human aggregate result. If neither
passes, write **estimator unqualified**, with no human stability inference. These
three worlds are instrument checks, not a population power estimate.

## Inference and secondary reports

First require the corrected-variance interval to lie entirely above zero. If it
does not, the outcome is “no between-person differences in sensitivity could be
measured in this task.” Report the variance interval and the approximate smallest
variance visible (`2.8 × bootstrap SE`), explicitly a normal approximation and a
design limitation. A computed stability scale report is not interpreted when
this gate fails.

The primary gain-stability bands are fixed: above 0.5 stable, below 0.2 not stable,
between partly stable. Only a whole interval above 0.5 supports a stable
sensitivity; intervals spanning boundaries remain inconclusive. The complete
2,000-draw percentile interval uses every draw. Any undefined draw invalidates
that field's interval; retain the failure ordinals and no redraws. Amendment P's
`sees` and `supports_at` accompany the primary, with the 0.5 bar and optimistic
normal-approximation caveat. The owner landing must lead with limited sensitivity
when `sees > 0.5`.

Secondary outputs use the same source and whole-person draws: level stability
(explicitly a rating-scale-use report), gain divided by each play's rating SD,
level/gain correlation, and within-person next-play first rating on previous-play
total undiscounted luck. Carryover uses participants with at least two supported
pairs and varying earlier total luck; absorbed or empty cells remain unsupported.
Gap reports use fixed calendar-day bins [0,1], (1,7], and (7,∞). Negative gaps are
counted and excluded only from gap reports, not silently repaired. None of these
secondary fields changes the primary or claims rebound was experimentally forced.

## Bounded execution, replay and admission

New isolated modules: `week5_tr1_math`, `week5_tr1`, `week5_tr1_fixture`.
No original MD source, output, model, gate or runtime is edited. Source projection
seals blocks of 256 whole plays; controls seal only complete constructed worlds;
bootstrap checkpoints preserve every completed draw. UUID JSON publication and
sealed numerical writes use the existing qualified publication primitive.
`YIELD_REQUEST`, the standard `max_new_draws` operational quantum and bounded wall
time are honored between complete units. A pending partial phase returns
`status=yielded, verified=false`; no `RESULT` claims completion.

The first 5% of source-projection blocks deliberately yields for the in-run cost
check. This is **not** a full computation forecast. The complete control work plus
the first 100/2,000 bootstrap draws supplies the second, whole-program cost prefix.
The owner budgets remaining execution plus independent replay from actual CPU
receipts; no guessed timing is represented as measured. The candidate plan uses
40,000 CPU seconds total for TR1 within the current 120,000 MD family ceiling,
including failed attempts and replay, ≤2 numerical threads, a 3-GiB RAM forecast
to validate, the unchanged resource floors, and the campaign cutoff. No paid,
GPU or Ollama route exists. The owner must check actual remaining allowance.

Verification reloads the original source and independently repeats projection,
all three controls, method selection, every retained resample and aggregate
output in a separate replay subtree. It does not copy producer statistics.
Constructed tests exercise the actual full 2,000-draw handler, pause/reentry,
verification-false pauses, source/semantic refusal and exact dense arithmetic.
Only the parent-authentication boundary is substituted by a sealed constructed
task in that fixture. This is disclosed and does not qualify a real source or
native runtime. Under amendment Q, owner review, committed design and passing
constructed fixture precede the single counted run; no extra native numerical
campaign is proposed.

Current status: static candidate only. Owner review, targeted test token/checks,
source-parent authentication, measured resource/cost admission and complete
scientific execution/replay remain outstanding. New records carry
`record_kind`, `theory_tags=[H12-T7]` and `by_construction` as applicable; no shared
record is written by this build.
