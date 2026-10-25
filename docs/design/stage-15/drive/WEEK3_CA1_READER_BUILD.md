# CA1 own direction beyond country: reader and timing build

The October 25 packet asks whether an annotator's choices predict her choices
on different prompts better than a country reader. `week3_alignment_stats`
implements that comparison after completed CA1 input and feature receipts.
It has not run a corpus comparison in this build pass.

The fixed numerical choices are 16 candidate-only principal components, scaled
by their candidate standard deviations, and conditional multinomial logit for
the four candidates. PCA contains no prompts, choices, explanations or identity
terms. A common candidate-set offset is removed because it cancels from the
choice probabilities. The population ridge penalty is one; the country direction
is shrunk toward population with penalty ten; the individual direction is shrunk
toward country with penalty ten. These summed-likelihood penalties are frozen
before corpus outcomes and are not tuned on the held-out halves. Damped Newton
fits require an absolute-gradient certificate of 0.0001.

The preparation pass's conversation/prompt connected components define disjoint
halves. Half zero trains all three readers; half one evaluates them. An annotator's
held-out decisions cannot enter any of the three fits. The primary is the mean
across annotators of country log loss minus individual log loss. Two thousand
annotator bootstrap resamples form its interval. The 1,000 writer-label references
supply a one-sided probability and a descriptive real-minus-reference interval.
A positive requires the primary interval above zero and permutation probability
below 0.05. Country over population and the fixed training-count bins are
descriptive. Prototype cosines remain pending CA3/VAL's independent labels.

The coding owner approved a dependence-preserving clarification before outcomes:
reassign **whole conversations** within country and the frozen cluster of their
first prompt, then rebuild every person's connected components, halves and all
three readers. This is the actual CA0 fallback. The corresponding shared-prompt
route conditions on country and first-prompt identity. The packet's literal
turn-by-turn shuffle remains unrun because it can split one conversation across
fake people. Candidate PCA is unchanged by an identity permutation, while every
label-dependent fit is rebuilt.

The original 20-comparison/10-prompt eligibility screen fixes the people once.
References do not reselect them. Their actual reassigned counts remain in the
private support records, and every person must still supply two nonempty,
disjoint connected-component halves. A missing person, mixed country or unsupported
split invalidates the comparison; no redraw or reduced population is accepted.
No conversation crosses halves, including inside the reference assignments.

Private checkpoints keep full fitted directions and support counts. The published
summary is aggregate only. Source receipts bind the prepared table to its feature
table. Continuation checks checkpoint hashes; full verification reconstructs PCA,
every split, reader and null result. The main route refuses fewer than 1,000 nulls
or features from a partial pilot. It uses the same cumulative CA1 allowance as
source preparation and embeddings.

Nine checks pass: finite-difference derivatives, a planted personal preference
recovered on disjoint prompts, an exactly indifferent world that cannot pass,
whole-conversation and country/cluster preservation, disjoint rebuilt halves,
held-out-choice blindness, PCA blindness to choices and prompt vectors, refusal
of unsupported fake people, actual handler/fresh replay and tamper detection,
and full-bank/full-feature guards. These checks validate the instrument; they
do not establish a corpus effect.

`week3_alignment_timing` is a separate timing instrument. A uniform 10% comparison
sample inevitably leaves some people without training rows or two usable halves.
It therefore fits the identical kernels on available sampled training rows,
records coverage and costs, and computes **no held-out score**. It projects those
costs to all fixed people and comparisons, applies a factor-two engineering
margin, and charges 1,001 fits times two passes for 1,000 nulls plus the real
calculation and fresh replay. That is an estimate, not a complexity guarantee.
Full metadata support is checked when all first prompts have frozen clusters;
otherwise that gate is explicitly pending full prompt embeddings. Four checks
pass for score prohibition, fresh kernel replay, exact feature-mode/source binding,
and changed-report refusal.

The owner must add incurred work, embeddings and their replay, full candidate PCA,
all complete split rebuilds, source work and bootstrap overhead to the timing
projection before admission. A sparse timing sample never becomes a scientific
cohort. The final inference concerns held-out choice prediction under this pinned
128-token multilingual representation; it does not independently identify values,
competence or causation.
