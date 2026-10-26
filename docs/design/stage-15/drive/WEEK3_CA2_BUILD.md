# CA2: recurring personal direction beyond country

CA2 asks whether an annotator's fitted deviation from her country's direction
recurs across disjoint sets of prompts. This implements the commissioned CA2
in the [Week 3 packet](../week3/PACKET.md), after complete CA1. Its original
allowance is 3,600 CPU seconds, including its timing, native validation,
execution and independent replay. These are frozen definitions, not results.

The two halves use CA1's existing conversation/prompt connected components.
The original eligible people and all comparisons remain fixed. Candidate-only
PCA, its 16 dimensions, whitening scale, and the three conditional-logit readers
are unchanged: population ridge one, country toward population ridge ten, and
individual toward country ridge ten. The same gradient certificate applies.
PCA is regenerated exactly against CA1's saved parameters. No new encoder,
label, model selection or provider call is required.

For each half, subtract the fitted country coefficient vector from the fitted
individual coefficient vector. The per-person readout is the cosine between
these two deviation vectors. Cosine measures direction and is unchanged by a
common orthogonal rotation of the feature coordinates. It is not a Pearson
correlation across arbitrarily numbered principal components. A zero deviation
in either half contributes exactly zero and is counted, without deleting that
person. The primary is the equal-person mean cosine minus its permutation mean.

CA1's freshly verified first-half fits are reused for the real data and all
1,000 reference assignments. Completion must authenticate every required saved
fit, the source bindings and the PCA record. The input hashes and seed must
match. A completed CA1 comparison is required regardless of whether its own
primary was positive, null or another valid outcome. Its incomplete or failed
attempt cannot supply CA2's first half.

CA2 newly fits the opposite half for the real data and all the identical whole-
conversation reassignments within country and first-prompt stratum. Every fake
person's connected components and halves are rebuilt. No person can disappear,
cross countries or lose a usable half; an unsupported assignment fails rather
than triggering a redraw or a reduced population. The default fallback uses
the frozen 50 first-prompt clusters as established by CA0 and CA1. The literal
turn-by-turn route remains unrun under the existing dependence clarification.

The 1,000 reference assignments use seed 20261026. Two thousand paired-person
bootstrap resamples give the interval for the real-minus-reference contrast.
A positive needs that interval strictly above zero and a one-sided permutation
probability below .05. Negative, marginal, unresolved and null bands are
exhaustive; a null says not detected with sensitivity untested. Main production
refuses a smaller bank or a reduced feature population. Verification repeats
all new opposite-half fits and reconstructs the statistic, while reauthenticating
the independently verified CA1 first-half evidence.

The descriptive decomposition uses the paired fitted individual directions,
with equal weight per person and half. It partitions total centered sums of
squares into country means, person means within country, and half disagreement
within person. These are empirical means of fitted directions, not a second
claim that the fitted country coefficient is an orthogonal component. The
residual includes estimation noise and split-specific variation; it is not an
isolated psychological residual or a causal variance component. The arithmetic
must close exactly within the stated numerical tolerance.

`week3_alignment_culture_timing` can precede complete CA1 using its completed
10% feature pilot. It fits the same kernels on sampled half-one training rows,
records every coverage denominator and computes no held-out score, recurrence
or decomposition. It extrapolates to all original people and half-one rows,
uses a twofold engineering margin, and prices 1,001 fits times two for the real
comparison, all 1,000 references and fresh replay. Source reads, full PCA,
assignment reconstruction, bootstrap and prior incurred charges are added by
the owner. Sparse sampled support never becomes a scientific population. An
over-budget projection holds main execution; it does not reduce the controls.

DESIGN CHECK: LESSONS sections 3–5 and CONTROLS sections 1–7 apply. Fourteen
targeted tests pass across the analysis and timing modules: exact parity with
CA1's opposite-half reader, planted personal recurrence against the actual
assignment reference, exact indifferent-world and common-country nulls, rotation/sign controls,
known decomposition, disjoint-half choice blindness, population/split mismatch
refusal, full replay, source/checkpoint corruption, fixed bank admission and
score-free timing. No corpus comparison or native launch has been performed by
this builder. The private handoff is
`.agent-state/drive-20261025/choice-handoff/CA2_READY.json`.

CA3 still needs complete calibrated VAL labels, its complete fit/target support
census and the full candidate feature table. Its earlier input-preparation
module retains every person and exposes unsupported input cases. CA4 needs
paired choice profiles and a frozen context-only reference under section 0.4;
CA2's saved opposite-half fits supply part of that dependency, but they do not
by themselves implement or license CA4. Neither study is claimed complete by
this build. Public reports remain aggregate; fitted person directions and
reference checkpoints stay in the private raw output tree.
