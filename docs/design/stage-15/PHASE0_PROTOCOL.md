# Phase 0 version 1: saved-output and prequential analyses

Frozen before execution, 2026-10-14. Authority: the next-round commission and the
curator's instruction to implement and run appropriate work without another routine
approval. This protocol is descriptive. No adaptive family kill, promotion,
engine admission, new inference or provider request is licensed by its outputs.

**DESIGN CHECK.** LESSONS 2-5 and CONTROLS read for this implementation. Under the
null, constant forecasts cannot discriminate and noise yields zero estimated
between-maker variance after truncation. Under the alternative, planted maker
offsets and biased informative forecasts are recovered. Target-label mutations
must leave held-out predictions unchanged. Changed inputs, malformed probabilities,
missing support, future labels, duplicate attempts and resource/deadline violations
refuse. Wide intervals are unresolved, not evidence of equivalence.

## T0a: where does uncertainty in personalization come from?

Use the exact 234 main targets and all 31 writers from the completed paired local
baseline/cloud analysis. Gain means population half-Brier minus partial-pooling
half-Brier; positive favors personalization. Fit unequal-size random-intercept
ANOVA components: pooled within-writer mean square; between-writer mean square
adjusted for effective cluster size. Report raw and zero-truncated between variance,
within variance, intraclass fraction, observed writer-mean spread and equal-writer
mean gain. Two thousand deterministic maker bootstrap draws give component intervals;
the existing 10,000-draw writer/prompt-crossed method describes gain uncertainty.
This decomposition does not model all prompt or historical-source dependence.

## T0b: do calibrated cloud probabilities add evidence?

Use all 936 retained forecasts on the same 234 main targets; no new inference.
Analyze H0, H1, H2 and H3 separately. Preserve all seven baseline comparisons.
For each outer held-out writer, fit every calibrator only on other writers.
Generate inner leave-one-writer-out corrected probabilities within that training
set before estimating a simplex weight for corrected reader plus B-mixlogit.
Minimize equal-writer half-Brier for stacking and equal-writer log loss for calibration.

Two methods are fixed: (1) requested EM prior adjustment then scalar temperature,
using mean raw training predictions as the reference prior and only unlabelled
outer-batch probabilities for EM; (2) bias-corrected temperature with three free
class offsets and one reference offset. Method 1 is an assumption sensitivity:
class-conditional invariance and the true LLM source prior are unverified.
Method 2 is separately named and does not silently replace it. The calibration
scale is exp(a), a in [-3,3]; offsets in [-8,8], L2 penalty .001. EM stops at
maximum change below 1e-8 or 2,000 iterations; nonconvergence is recorded.

Probabilities are clipped to 1e-8 and renormalized for numerical stability, declared
before scoring. Standalone invalid forecasts retain half-Brier 1 and system log
loss -log(.01). Stacking falls back to B-mixlogit on an invalid reader. Report both
half-Brier and log loss, all method/arm curves, own-history versus donor-history,
and the frozen delta .01 screen using both descriptive writer and prompt-crossed
intervals. These intervals condition on fitted predictions; they are not simultaneous,
do not cover calibration refitting uncertainty and do not control selection over arms.
Any passing screen is a candidate for independent confirmation, not an engine admission.

## T0c: how does the local backbone improve with accumulated history?

Replay every usable chronological CoAuthor session using the existing source
extractor, source hashes and exposure ledger. Preserve source exclusions and actual
writer/session/decision denominators. Each session starts a new frozen fit from all
sessions whose recorded end is strictly earlier than its start. Refit the existing
multinomial population model and writer residual, without effort features. Select
writer penalty from {.01,.1,1,10} on that writer's historical last 20 percent, with
the calibration model trained before that historical split. Fewer than ten own
decisions or insufficient calibration support use fixed penalty 1. Fewer than eight
population decisions use the personal-frequency fallback. No current-session labels
fit a parameter; already resolved same-session previous handling is an observed feature.

Comparators: Laplace-smoothed population frequencies and personal counts with four
population-prior pseudo-observations, frozen at the same session start. Gain is
comparator loss minus partial-pooling loss. Report all decisions, own-prompt-novel
and globally prompt-novel subsets, each over prior-own-decision bins 0, 1-9, 10-29,
30-99, 100-299, 300+. Include half-Brier and log loss; intervals are conditional
descriptive summaries of evolving forecasts, not independent confirmations.

## Execution and recording

Serial order T0c, T0b, T0a prioritizes the longer replay. Single-thread numerical
libraries and below-normal native priority avoid competition with live projects.
Minimum free RAM 8 GiB, commit headroom 8 GiB, disk 20 GiB. Maximum wall time 18
hours, with a hard cap at October 16 10:00 PDT, whichever is earlier. One immutable
attempt claim, source/input plan and exact native owner; per-session checkpoints
survive interruption. No automatic retry, source mutation, stale-lock deletion,
GPU lock acquisition or provider call. Completion and failures are registered with
the existing watcher; its independent six-hour clock is unchanged.

After the whole cell completes, independently replay integrity and selected scoring,
then write FINDINGS, the instrument ledger (and theory only as current reporting
policy permits), TODO and the curator roll-up before ACK. Preserve the Stage 14
joint final packet. Raw text, writer keys, native identities and predictions stay local;
public summaries contain aggregates and reproducibility hashes only.
