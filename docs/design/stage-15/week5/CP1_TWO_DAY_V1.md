# CP1: warmth matching and standing complementarity

Prospective implementation, 2026-11-13. Owner review, a committed design and
complete counted fixture remain required. This document claims no completed
human source, marker adjudication, effect, measured cost or native qualification.
The two-day packet is controlling. R13–R15 supporting handoffs were not found;
their contents are not reconstructed here. Frozen intake V1 remains unchanged.

## Question and source gates

Does a parent's lexical assertion predict deference more than assertion in the
reply, after subtracting the conversation's shuffled association? The primary
bar is 0.02 standardized-slope units. Warmth matching, four utterance-admin role
strata and the continuous edit-count gap are secondary diagnostics.

The source is the exact pinned ConvoKit wiki-corpus ZIP identified in
`RF_CP_INTAKE_TWO_DAY_V1.md`, never the awry or politeness corpus. Analysis reads
only the qualified source's salted IDs, lexical counts and metadata. It requires
the source's actual fresh native replay, exact source-block digests, the frozen
manual-label digest and the actual fully verified instrument decision. A source
template, a constructed proof or a hash by itself cannot release human analysis.
Every marker family needs frequency at least 3% and at least 80 correct among
exactly 100 privately adjudicated sampled hits. No thresholds change here.

## Frozen rows and estimator

The source's explicit reply edge defines a pair. Root utterances are not pairs;
self-speaker replies and pairs with either utterance below 10 stripped tokens
are declared exclusions. Missing parents, cross-conversation edges and self
edges are counted collection errors; above 1% of nonroot reply opportunities
refuses collection. Every source refusal remains counted separately. No text is
read by this consumer. Parent and reply are ordered by salted source IDs within
each sorted conversation, with no dependence on a marker or result.

For each slope, ordinary least squares with an intercept and both variables
standardized is the correlation. Pool eligible pairs with equal pair weights.
Shuffle the whole reply bundle among the pairs within a conversation 200 times,
moving all three reply counts and the reply speaker's edit count together.
The parent and its metadata stay fixed. A fixed PCG64 permutation per
conversation, view and index is seeded by SHA-256 of the declared seed 20261112.
Each statistic is its observed value minus its mean under all 200 shuffles.
The primary is the corrected assertion-to-deference slope minus corrected
assertion-to-assertion slope. Identical reply deference/assertion arrays must
produce exactly zero in every permutation and bootstrap draw.

Bootstrap whole conversations 2,000 times, with replacement; retain every pair
in each selected conversation. Each global draw uses its own SHA-derived PCG64
seed under 20261107. A duplicated conversation reuses the same fixed permutation
bank: the estimator, including its Monte Carlo null, is a fixed function of the
selected conversations. It does not draw a different null for duplicate copies.
Report the linear percentile 95% interval and sample bootstrap SE. Undefined
draws are retained; an incomplete set of 2,000 defined draws receives no
inferential interval. No retry, favorable deletion, zero fill or extra shuffle.

Twenty conversations are the inherited floor. Below it, run the pooled
descriptive estimate without an inferential interval. Also report counts of
conversations with variable parent assertion and with exchangeable replies. If
no within-conversation contrast is possible, label the primary `design cannot
test`, not a null. This diagnostic does not introduce a new count threshold.

## Secondary definitions, pending owner review

Run four role strata using the source **utterance** is-admin flags, ordered as
parent then reply. Within each observed stratum, shuffle replies within each
conversation. The main pooled estimator remains unchanged. A stratum inherits
the 20-conversation floor and the primary's 0.02 bar; it is a descriptive texture.

The packet's graded edit-count difference is implemented as the standardized
assertion-by-gap interaction in a model with intercept, assertion, signed
reply-minus-parent edit-count gap and their product. Subtract the corresponding
assertion-response interaction from the deference-response interaction, then
subtract the 200-shuffle mean. Standardize assertion, gap and each response in
each replicate; do not standardize their product again. Moving the complete
reply bundle recomputes the gap. This is a **prospective secondary operational
definition for owner review**, not an additional primary or inherited bar.
The static corpus edit count has no demonstrated event-time clock: this
diagnostic describes retrospective count differences and makes no temporal or
causal rank claim. Rank deficiency leaves this diagnostic unsupported without
discarding the primary. Full-rank standardized normal matrices require minimum
eigenvalue above 1e-10 times maximum and solve residual at most 1e-8. Independent
centered-moment least-squares replay must agree within 2e-8.

## Checkpoints, cost and privacy

The handler seals 64-conversation banks and 20-draw uncertainty blocks, binding
source, instrument, code, sample, view, seeds and exact global indices. It checks
cooperative yield within permutation loops and each aggregation block/draw.
Continuation accepts only authenticated closed blocks; an unsealed output
refuses rather than being silently replaced. The fresh verifier rebuilds the
entire bank and all draws, compares complete outputs, and uses an independent
centered-moment/least-squares implementation for every newly replayed draw.

CPU-only, at most two numerical threads; no raw-text export or external model.
All stages and failures debit CP's 60,000-second family. Real cost and peak
memory are **unmeasured**. The counted first cost prefix covers a fixed number
of complete conversation blocks; a forecast above 7,200 seconds requires the
first 5% checkpointed in-slot pilot, including full replay. Native guards apply.
The first implementation keeps the source join in memory and banks on disk;
its real working set and combined execution/replay disk requirement must be
measured rather than inferred from a small constructed fixture.

If amendment E is actually triggered, freeze a whole-conversation sample with
the inherited 20261102 seed, size derived from the charged measured cost and
remaining allowance. No sample size is selected in advance. Preserve the full
population denominator and sample fraction; below-floor sample is cost-held.
No sample-cost receipt or guessed forecast is fabricated by this handler.

## DESIGN CHECK and known answers

LESSONS 2–5 and CONTROLS apply. The case check is a within-conversation predictor
and response contrast after the fixed marker instrument passes. The strongest
rival is accommodation: assertion predicts assertion. Neither association is
felt emotion or a causal intervention. Adminship and lexical politeness are
fallible measurements, not direct psychological labels.

The source fixture already defines ten literal pairs with independent hand
counts. Statistical fixtures add positive complementary and negative convergent
worlds, matched by swapping deference and assertion, an identical-response exact
zero, fixed covariance known answers and an independent direct-row permutation
oracle. Preserve every 2,000-draw index in full native qualification. Refusal
fixtures cover failed/manual gates, changed provenance, incomplete banks,
tampering, missing variance, excessive pair-join errors, sample authority and
checkpoint continuation. These fixtures are prepared, not yet executed.

Every aggregate record carries H15-T4, record kind, constructed status and the
activation fields. Report estimate, interval, bar, SE, `sees = 2.8 SE` and
`supports at = bar + 2.8 SE` for the primary. Secondary statistics without a
packet bar do not invent one. A sensitivity qualification or fresh native proof
is not a scientific claim. The owner controls interpretation and EX6 release;
this handler never exports it.
